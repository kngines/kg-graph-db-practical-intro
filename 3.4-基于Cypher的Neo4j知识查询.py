from py2neo import Graph

# 连接Neo4j数据库
graph = Graph(
    "bolt://localhost:7687"
)

# 场景1：查询张三的所有关联关系和对象
query1 = """
MATCH (zhangsan:Person {name: "张三"})-[r]->(obj)
RETURN zhangsan.name, type(r) AS relationship, obj.name AS object, obj.type AS object_type
"""
result1 = graph.run(query1).data()
print("场景1：张三的所有关联关系")
for res in result1:
    print(res)

# 场景2：查询张三的大学同学的研究方向（多跳查询）
query2 = """
MATCH (zhangsan:Person {name: "张三"})-[r:大学同学]->(lisi:Person)
RETURN zhangsan.name, lisi.name, lisi.research_field AS lisi_research_field
"""
result2 = graph.run(query2).data()
print("\n场景2：张三同学的研究方向")
for res in result2:
    print(res)

# 场景3：查询所有高校类型的机构
query3 = """
MATCH (org:Organization {type: "高校"})
RETURN org.name, org.type
"""
result3 = graph.run(query3).data()
print("\n场景3：所有高校机构")
for res in result3:
    print(res)

# 场景4：创建索引（优化后续查询）- 兼容所有版本
try:
    # 尝试新语法
    graph.run("CREATE INDEX person_name_index FOR (p:Person) ON (p.name)")
    print("已为Person.name创建索引")
except:
    try:
        # 如果新语法失败，尝试旧语法
        graph.run("CREATE INDEX ON :Person(name)")
        print("已为Person.name创建索引")
    except:
        print("Person.name索引已存在或无法创建")

try:
    # 尝试新语法
    graph.run("CREATE INDEX org_type_index FOR (o:Organization) ON (o.type)")
    print("已为Organization.type创建索引")
except:
    try:
        # 如果新语法失败，尝试旧语法
        graph.run("CREATE INDEX ON :Organization(type)")
        print("已为Organization.type创建索引")
    except:
        print("Organization.type索引已存在或无法创建")



