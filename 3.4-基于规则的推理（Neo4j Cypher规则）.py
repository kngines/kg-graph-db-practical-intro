from py2neo import Graph

graph = Graph(
    "bolt://localhost:7687"
)

# 定义推理规则：若A毕业于B，B是高校，则推导A是B的“校友”
inference_query = """
MATCH (p:Person)-[r:毕业于]->(org:Organization {type: "高校"})
MERGE (p)-[new_r:校友]->(org)
RETURN p.name, org.name, type(new_r) AS new_relationship
"""
inference_result = graph.run(inference_query).data()
print("基于规则推理的新知识（校友关系）：")
for res in inference_result:
    print(res)

# 验证推理结果
verify_query = """
MATCH (p:Person)-[r:校友]->(org:Organization)
RETURN p.name, org.name
"""
verify_result = graph.run(verify_query).data()
print("\n验证推理结果：")
for res in verify_result:
    print(res)