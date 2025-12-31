from neo4j import GraphDatabase
import os
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, AutoModelForSequenceClassification

# 设置镜像源
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 定义Neo4j连接配置
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "auth": ("neo4j", "123456")  # 根据实际配置修改
}

# 初始化模型变量
tokenizer = None
model = None
label_map = None
re_tokenizer = None
re_model = None
REL_LABELS = None

# 加载中文NER模型
MODEL_NAME = "ckiplab/bert-base-chinese-ner"
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)

    # 获取模型的标签映射
    if hasattr(model.config, 'id2label'):
        label_map = model.config.id2label
    else:
        # 默认标签映射
        label_map = {0: "O", 1: "B-PER", 2: "I-PER", 3: "B-ORG", 4: "I-ORG", 5: "B-LOC", 6: "I-LOC"}

    print("成功加载中文NER模型")
except Exception as e:
    print(f"NER模型加载失败: {e}")

# 加载关系抽取模型
RE_MODEL_NAME = "./models/bert-base-chinese"
try:
    REL_LABELS = ["创始人", "位于", "属于", "无关系"]
    re_tokenizer = AutoTokenizer.from_pretrained(RE_MODEL_NAME)
    re_model = AutoModelForSequenceClassification.from_pretrained(
        RE_MODEL_NAME, num_labels=len(REL_LABELS)
    )
    print("成功加载关系抽取模型")
except Exception as e:
    print(f"关系抽取模型加载失败: {e}")


def extract_entities(text):
    """提取文本中的中文实体（人名PER/机构ORG/地名LOC）"""
    global tokenizer, model

    # 检查模型是否已加载
    if tokenizer is None or model is None:
        print("错误：模型未加载，无法执行实体提取")
        return []

    # 编码文本
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    # 模型推理
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
    logits = outputs.logits
    predictions = torch.argmax(logits, dim=2)

    # 解析实体
    tokens = tokenizer.convert_ids_to_tokens(input_ids[0])
    entities = []
    current_entity = None
    current_type = None

    for token, pred in zip(tokens, predictions[0]):
        label = label_map[pred.item()]
        if token in ["[CLS]", "[SEP]"]:
            continue

        # 处理实体开始
        if label.startswith("B-"):
            if current_entity:
                entities.append((current_entity, current_type))
            current_entity = token.replace("##", "")  # 处理分词后的子词
            current_type = label.split("-")[1]
        # 处理实体内部
        elif label.startswith("I-") and current_entity:
            current_entity += token.replace("##", "")
        # 非实体，结束当前实体
        elif label == "O" and current_entity:
            entities.append((current_entity, current_type))
            current_entity = None
            current_type = None

    # 处理最后一个实体
    if current_entity:
        entities.append((current_entity, current_type))

    return entities


def extract_relation(text, entity1, entity2):
    """抽取两个实体间的关系"""
    # 构造输入：[CLS] 实体1 [SEP] 实体2 [SEP] 上下文 [SEP]
    input_text = f"{entity1}[SEP]{entity2}[SEP]{text}"
    inputs = re_tokenizer(
        input_text, return_tensors="pt", padding=True, truncation=True, max_length=128
    )

    # 模型推理（实际需用标注数据微调模型，此处为框架示例）
    with torch.no_grad():
        outputs = re_model(**inputs)
    logits = outputs.logits
    pred_idx = torch.argmax(logits, dim=1).item()
    return REL_LABELS[pred_idx]


def import_ner_re_to_neo4j(text):
    """将NER+RE结果导入Neo4j"""
    # 1. 提取实体
    entities = extract_entities(text)
    # 2. 构建实体映射（去重）
    entity_map = {ent: ent_type for ent, ent_type in entities}
    # 3. 提取实体对关系
    entity_list = list(entity_map.keys())
    print(entity_list)

    driver = GraphDatabase.driver(**NEO4J_CONFIG)

    with driver.session() as session:
        # 写入实体节点
        for ent, ent_type in entity_map.items():
            # 节点标签：PER/ORG/LOC
            session.run(f"""
                MERGE (n:{ent_type} {{name: $name}})
            """, name=ent)

        # 写入实体间关系
        for i in range(len(entity_list)):
            for j in range(i + 1, len(entity_list)):
                e1 = entity_list[i]
                e2 = entity_list[j]
                rel = extract_relation(text, e1, e2)
                if rel != "无关系":
                    session.run(f"""
                        MATCH (a {{name: $e1}}), (b {{name: $e2}})
                        MERGE (a)-[:{rel}]->(b)
                    """, e1=e1, e2=e2)

    driver.close()
    print("非结构化文本抽取结果导入Neo4j完成！")


# 定义测试文本
text = "马云于1999年创立阿里巴巴，公司总部位于杭州余杭区。"

# 执行导入
import_ner_re_to_neo4j(text)
