# 完整的Neo4j批量存储示例
from neo4j import GraphDatabase
import pandas as pd

# 定义Neo4j连接配置
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "auth": ("neo4j", "123456")  # 根据实际配置修改
}

# 批量导入三元组数据
def batch_import_to_neo4j(triples):
    """
    triples格式：[(实体1, 关系, 实体2, 实体1类型, 实体2类型), ...]
    """
    driver = GraphDatabase.driver(**NEO4J_CONFIG)

    with driver.session() as session:
        # 开启事务批量写入
        tx = session.begin_transaction()
        for s, p, o, s_type, o_type in triples:
            tx.run(f"""
                MERGE (s:{s_type} {{name: $s_name}})
                MERGE (o:{o_type} {{name: $o_name}})
                MERGE (s)-[:{p}]->(o)
            """, s_name=s, o_name=o)
        tx.commit()

    driver.close()
    print(f"Neo4j批量导入{len(triples)}条三元组完成！")


# 测试数据
test_triples = [
    ("马云", "创始人", "阿里巴巴", "PER", "ORG"),
    ("阿里巴巴", "位于", "杭州", "ORG", "LOC"),
    ("杭州", "属于", "浙江省", "LOC", "LOC")
]
batch_import_to_neo4j(test_triples)