import re
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import GraphDatabase

# 定义Neo4j连接配置
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "auth": ("neo4j", "123456")  # 根据实际配置修改
}

# 工具函数：文本相似度计算
def get_similarity(text1, text2):
    """融合编辑距离和TF-IDF余弦相似度"""

    # 预处理
    def preprocess(t):
        t = t.lower()
        t = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fa5]", "", t)
        return t

    t1, t2 = preprocess(text1), preprocess(text2)
    # 编辑距离相似度
    edit_sim = SequenceMatcher(None, t1, t2).ratio()
    # TF-IDF余弦相似度
    if len(t1) == 0 or len(t2) == 0:
        tfidf_sim = 0.0
    else:
        vec = TfidfVectorizer()
        tfidf = vec.fit_transform([t1, t2])
        tfidf_sim = cosine_similarity(tfidf)[0][1]
    # 加权融合
    return (edit_sim * 0.6) + (tfidf_sim * 0.4)


# 1. 实体对齐：合并Neo4j中相似实体
def entity_alignment(neo4j_config, threshold=0.8):
    """对齐Neo4j中相似度高于阈值的实体"""
    driver = GraphDatabase.driver(**neo4j_config)

    try:
        with driver.session() as session:
            # 读取所有实体（示例：ORG类型）
            result = session.run("MATCH (n:ORG) RETURN n.name AS name")
            org_names = [record["name"] for record in result]

            # 遍历实体对，计算相似度
            aligned_pairs = []
            for i in range(len(org_names)):
                for j in range(i + 1, len(org_names)):
                    name1, name2 = org_names[i], org_names[j]
                    sim = get_similarity(name1, name2)
                    if sim >= threshold:
                        aligned_pairs.append((name1, name2))
                        # 合并实体：将name2的关系迁移到name1，删除name2
                        session.run("""
                            MATCH (a:ORG {name: $name2})-[r]->(b)
                            MATCH (c:ORG {name: $name1})
                            MERGE (c)-[nr:TYPE(r)]->(b)
                            DELETE r, a
                        """, name1=name1, name2=name2)

        print(f"完成实体对齐，合并{len(aligned_pairs)}组相似实体：{aligned_pairs}")
    finally:
        driver.close()


# 2. 实体消歧：区分Neo4j中同名实体
def entity_disambiguation(neo4j_config, entity_name, context):
    """基于上下文消歧同名实体"""
    driver = GraphDatabase.driver(**neo4j_config)

    try:
        with driver.session() as session:
            # 读取所有同名实体的邻居信息（图结构特征）
            result = session.run("""
                MATCH (n {name: $name})-[r]->(m)
                RETURN n, collect({rel: TYPE(r), neighbor: m.name}) AS neighbors
            """, name=entity_name)
            entities = [{"node": record["n"], "neighbors": record["neighbors"]}
                        for record in result]

        # 计算上下文与实体邻居的相似度
        best_match = None
        max_sim = 0.0
        for ent in entities:
            # 拼接邻居信息作为实体特征
            neighbor_text = " ".join([f"{item['rel']}{item['neighbor']}"
                                      for item in ent["neighbors"]])
            sim = get_similarity(context, neighbor_text)
            if sim > max_sim:
                max_sim = sim
                best_match = ent["node"]

        return best_match
    finally:
        driver.close()


# 测试实体融合
# 1. 先向Neo4j写入待对齐实体
test_align_data = [("阿里巴巴", "ORG"), ("阿里集团", "ORG"), ("腾讯", "ORG")]
driver = GraphDatabase.driver(**NEO4J_CONFIG)
try:
    with driver.session() as session:
        for name, ent_type in test_align_data:
            session.run(f"MERGE (n:{ent_type} {{name: $name}})", name=name)
finally:
    driver.close()

# 2. 执行实体对齐
entity_alignment(NEO4J_CONFIG, threshold=0.8)

# 3. 测试实体消歧
# 先写入同名实体：苹果（公司）、苹果（水果）
driver = GraphDatabase.driver(**NEO4J_CONFIG)
try:
    with driver.session() as session:
        session.run("MERGE (n:ORG {name: '苹果'})-[:生产]->(m:Product {name: 'iPhone'})")
        session.run("MERGE (n:FRUIT {name: '苹果'})-[:生长于]->(m:LOC {name: '山东'})")
finally:
    driver.close()

# 消歧：上下文"苹果发布新款iPhone" → 匹配ORG类型的苹果
disambig_result = entity_disambiguation(NEO4J_CONFIG, "苹果", "苹果发布新款iPhone")
print(f"\n=== 实体消歧结果 ===")
if disambig_result:
    print(f"消歧实体：{disambig_result['name']}，类型：{list(disambig_result.labels)[0]}")
else:
    print("未找到匹配的实体")
