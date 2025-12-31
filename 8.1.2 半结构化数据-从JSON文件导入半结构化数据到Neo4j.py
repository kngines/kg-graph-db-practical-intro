import json
from neo4j import GraphDatabase

# 1. 配置数据库连接
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "company_db"
}
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687"
}

# 1. 读取JSON数据（示例：商品-品牌半结构化数据）
def read_json_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# 2. 解析并导入Neo4j
def import_json_to_neo4j(json_data):
    driver = GraphDatabase.driver(**NEO4J_CONFIG)

    with driver.session() as session:
        for item in json_data:
            # 提取实体：商品、品牌
            product_id = item["product_id"]
            product_name = item["product_name"]
            brand_name = item["brand"]["name"]
            brand_country = item["brand"]["country"]

            # 写入节点和关系
            session.run("""
                MERGE (b:Brand {name: $brand_name, country: $brand_country})
                MERGE (p:Product {id: $product_id, name: $product_name, price: $price})
                MERGE (p)-[:BELONGS_TO]->(b)
            """, brand_name=brand_name, brand_country=brand_country,
                        product_id=product_id, product_name=product_name, price=item["price"])

    driver.close()
    print("半结构化JSON数据导入Neo4j完成！")


# 测试数据（可保存为product_data.json）
test_json = [
    {"product_id": "P001", "product_name": "iPhone 15", "price": 5999,
     "brand": {"name": "苹果", "country": "美国"}},
    {"product_id": "P002", "product_name": "Mate 60 Pro", "price": 4999,
     "brand": {"name": "华为", "country": "中国"}}
]
# 执行导入
# import_json_to_neo4j(read_json_data("product_data.json"))
import_json_to_neo4j(test_json)