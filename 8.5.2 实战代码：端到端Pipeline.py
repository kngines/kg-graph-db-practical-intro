import mysql.connector
import json
import re
from neo4j import GraphDatabase
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import pandas as pd
from neo4j import GraphDatabase
from sqlalchemy import create_engine, text

# ===================== 全局配置 =====================
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "company_db"
}
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687"
}

# 创建 SQLAlchemy 引擎
def create_mysql_engine():
    connection_string = f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}"
    return create_engine(connection_string)



# 在全局配置部分修改NER模型初始化
NER_MODEL_NAME = "ckiplab/bert-base-chinese-ner"
tokenizer = AutoTokenizer.from_pretrained(NER_MODEL_NAME)
ner_model = AutoModelForTokenClassification.from_pretrained(NER_MODEL_NAME)

# 从模型配置获取标签映射
if hasattr(ner_model.config, 'id2label'):
    label_map = ner_model.config.id2label
else:
    # 默认标签映射
    label_map = {0: "O", 1: "B-PER", 2: "I-PER", 3: "B-ORG", 4: "I-ORG", 5: "B-LOC", 6: "I-LOC"}

# ===================== 工具函数 =====================
def preprocess_text(text):
    """文本清洗"""
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", "", text)
    return text

def extract_entities(text):
    """NER实体提取"""
    text = preprocess_text(text)
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = ner_model(**inputs)
    predictions = torch.argmax(outputs.logits, dim=2)
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

    entities = []
    current_ent, current_type = None, None
    for token, pred in zip(tokens, predictions[0]):
        label = label_map[pred.item()]
        if token in ["[CLS]", "[SEP]"]:
            continue
        if label.startswith("B-"):
            if current_ent:
                entities.append((current_ent, current_type))
            current_ent = token.replace("##", "")
            current_type = label.split("-")[1]
        elif label.startswith("I-") and current_ent:
            current_ent += token.replace("##", "")
        elif label == "O" and current_ent:
            entities.append((current_ent, current_type))
            current_ent, current_type = None, None
    if current_ent:
        entities.append((current_ent, current_type))
    return list(set(entities))  # 去重


def get_similarity(text1, text2):
    """相似度计算（实体对齐用）"""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, text1, text2).ratio()


# ===================== 数据接入 =====================
def load_multi_source_data():
    """加载多源数据：结构化(MySQL)+半结构化(JSON)+非结构化(文本)"""
    # 1. 加载结构化数据（MySQL）
    engine = create_mysql_engine()

    try:
        # 获取employee表的列信息
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'employee' AND TABLE_SCHEMA = :database"),
                                  {"database": MYSQL_CONFIG['database']})
            available_columns = [row[0] for row in result.fetchall()]

        # 获取department表信息用于关联查询
        if 'dept_id' in available_columns and 'name' in available_columns:
            # 关联employee和department表获取部门名称
            query = """
            SELECT e.name, e.age, d.name as dept, e.dept_id
            FROM employee e
            LEFT JOIN department d ON e.dept_id = d.id
            """
            df_emp = pd.read_sql(query, engine)

            # 如果没有dept列或为空，使用dept_id作为部门名
            if 'dept' not in df_emp.columns or df_emp['dept'].isna().all():
                df_emp['dept'] = df_emp['dept_id'].astype(str)
        else:
            # 如果表结构不符合预期，使用默认数据
            print("警告: employee表结构不符合预期，使用默认数据")
            df_emp = pd.DataFrame({
                'name': ['张三', '李四', '王五'],
                'dept': ['技术部', '销售部', '人事部'],
                'position': ['工程师', '销售经理', 'HR']
            })
    except Exception as e:
        print(f"数据库查询失败: {e}")
        # 使用默认数据
        df_emp = pd.DataFrame({
            'name': ['张三', '李四', '王五'],
            'dept': ['技术部', '销售部', '人事部'],
            'position': ['工程师', '销售经理', 'HR']
        })

    # 2. 加载半结构化数据（JSON）
    json_data = [
        {"company": "阿里巴巴", "ceo": "张勇", "location": "杭州"},
        {"company": "腾讯", "ceo": "马化腾", "location": "深圳"}
    ]

    # 3. 加载非结构化文本数据
    text_data = [
        "马云1999年创立阿里巴巴，总部在杭州余杭区",
        "马化腾1998年创立腾讯，总部位于深圳南山区"
    ]

    return df_emp, json_data, text_data

def build_triples(df_emp, json_data, text_data):
    """构建三元组"""
    triples = []

    # 1. 结构化数据生成三元组 - 检查列是否存在
    if 'name' in df_emp.columns and 'dept' in df_emp.columns:
        for _, row in df_emp.iterrows():
            emp_name = row["name"]
            dept_name = row["dept"]
            triples.append((emp_name, "任职于", dept_name, "PER", "ORG"))

    # 2. 半结构化数据生成三元组
    for item in json_data:
        company = item["company"]
        ceo = item["ceo"]
        loc = item["location"]
        triples.append((ceo, "担任CEO", company, "PER", "ORG"))
        triples.append((company, "位于", loc, "ORG", "LOC"))

    # 3. 非结构化文本抽取三元组
    for text in text_data:
        entities = extract_entities(text)
        ent_map = {e: t for e, t in entities}
        ent_list = list(ent_map.keys())
        # 简单关系抽取（基于规则）
        if "马云" in ent_list and "阿里巴巴" in ent_list:
            triples.append(("马云", "创始人", "阿里巴巴", "PER", "ORG"))
        if "马化腾" in ent_list and "腾讯" in ent_list:
            triples.append(("马化腾", "创始人", "腾讯", "PER", "ORG"))

    # 4. 实体对齐（去重相似实体）
    aligned_triples = []
    ent_align_map = {}  # 实体对齐映射：别名→标准名
    for s, p, o, s_t, o_t in triples:
        # 对齐主语
        s_aligned = s
        for std_ent in ent_align_map:
            if get_similarity(s, std_ent) > 0.8 and s not in ent_align_map:
                s_aligned = std_ent
        if s_aligned not in ent_align_map:
            ent_align_map[s_aligned] = s_t
        # 对齐宾语
        o_aligned = o
        for std_ent in ent_align_map:
            if get_similarity(o, std_ent) > 0.8 and o not in ent_align_map:
                o_aligned = std_ent
        if o_aligned not in ent_align_map:
            ent_align_map[o_aligned] = o_t
        aligned_triples.append((s_aligned, p, o_aligned, ent_align_map[s_aligned], ent_align_map[o_aligned]))

    return list(set(aligned_triples))  # 去重

# ===================== Neo4j存储 =====================
def import_triples_to_neo4j(triples):
    """导入三元组到Neo4j"""
    driver = GraphDatabase.driver(**NEO4J_CONFIG)
    with driver.session() as session:
        tx = session.begin_transaction()
        for s, p, o, s_t, o_t in triples:
            # 处理关系名特殊字符
            p = p.replace(" ", "_").replace("-", "_")
            tx.run(f"""
                MERGE (s:{s_t} {{name: $s_name}})
                MERGE (o:{o_t} {{name: $o_name}})
                MERGE (s)-[:{p}]->(o)
            """, s_name=s, o_name=o)
        tx.commit()
    driver.close()
    print(f"共导入{len(triples)}条三元组到Neo4j！")


# ===================== 知识查询 =====================
def query_neo4j_kg():
    """Neo4j知识图谱查询示例"""
    driver = GraphDatabase.driver(**NEO4J_CONFIG)
    with driver.session() as session:
        # 1. 查询所有创始人关系
        print("\n=== 查询所有创始人关系 ===")
        result1 = session.run("""
            MATCH (p:PER)-[:创始人]->(o:ORG)
            RETURN p.name AS 创始人, o.name AS 公司
        """)
        for record in result1:
            print(f"{record['创始人']} → {record['公司']}")

        # 2. 查询公司所在地
        print("\n=== 查询公司所在地 ===")
        result2 = session.run("""
            MATCH (o:ORG)-[:位于]->(l:LOC)
            RETURN o.name AS 公司, l.name AS 所在地
        """)
        for record in result2:
            print(f"{record['公司']} → {record['所在地']}")
    driver.close()


# ===================== 执行完整Pipeline =====================
if __name__ == "__main__":
    # 1. 加载多源数据
    df_emp, json_data, text_data = load_multi_source_data()
    # 2. 构建并融合三元组
    triples = build_triples(df_emp, json_data, text_data)
    # 3. 导入Neo4j
    import_triples_to_neo4j(triples)
    # 4. 查询分析
    query_neo4j_kg()