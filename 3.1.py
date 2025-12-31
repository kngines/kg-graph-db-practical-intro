from py2neo import Graph, Node, Relationship, Subgraph
from py2neo.matching import NodeMatcher

# 连接Neo4j数据库（替换为你的Neo4j地址、账号、密码）
graph = Graph(
    "bolt://localhost:7687",  # Neo4j的Bolt协议地址，默认端口7687
    # username="root",
    # password="root"  # 替换为你修改后的密码
)

# 初始化节点匹配器（用于后续查询节点）
node_matcher = NodeMatcher(graph)

# # 清空数据库（可选，用于重复测试时避免数据冗余）
graph.delete_all()
# print("成功连接Neo4j数据库！")
#
# # 1. 创建人物实体（类别：Poet，附带属性）
# li_bai = Node(
#     "Poet",  # 实体类别（标签）
#     name="李白",
#     alias="李太白",
#     birth_year=701,
#     native_place="陇西成纪"
# )
#
# du_fu = Node(
#     "Poet",
#     name="杜甫",
#     alias="杜子美",
#     birth_year=712,
#     native_place="河南巩县"
# )
#
# # 2. 创建作品实体（类别：Work，附带属性）
# jing_ye_si = Node(
#     "Work",
#     title="《静夜思》",
#     genre="五言绝句",
#     era="盛唐"
# )
#
# chun_wang = Node(
#     "Work",
#     title="《春望》",
#     genre="五言律诗",
#     era="中唐"
# )
#
# # 将实体添加到知识图谱
# graph.create(li_bai)
# graph.create(du_fu)
# graph.create(jing_ye_si)
# graph.create(chun_wang)
# print("成功创建实体！")
#
# # 1. 创建“李白-创作-《静夜思》”的关系（附带创作地点属性）
# create_1 = Relationship(li_bai, "创作", jing_ye_si, create_place="扬州")
#
# # 2. 创建“杜甫-创作-《春望》”的关系
# create_2 = Relationship(du_fu, "创作", chun_wang, create_place="长安")
#
# # 3. 可选：创建人物间的关系（李白和杜甫为“好友”）
# friend_relation = Relationship(li_bai, "好友", du_fu, acquaintance_year=744)
#
# # 将关系添加到知识图谱
# graph.create(create_1)
# graph.create(create_2)
# graph.create(friend_relation)
# print("成功创建关系！")
#
# # 查询1：获取所有诗人的信息
# poet_query = """
# MATCH (p:Poet)
# RETURN p.name AS 诗人姓名, p.alias AS 别名, p.birth_year AS 出生年份, p.native_place AS 籍贯
# """
# poet_result = graph.run(poet_query).data()
# print("===== 所有诗人信息 =====")
# for poet in poet_result:
#     print(poet)
#
# # 查询2：获取某部作品的创作者及创作信息
# work_query = """
# MATCH (p:Poet)-[r:创作]->(w:Work {title:"《静夜思》"})
# RETURN p.name AS 创作者, w.title AS 作品名称, w.genre AS 体裁, r.create_place AS 创作地点
# """
# work_result = graph.run(work_query).data()
# print("\n===== 《静夜思》创作信息 =====")
# for work in work_result:
#     print(work)
#
# # 查询3：获取所有“创作”关系的关联数据
# relation_query = """
# MATCH (p:Poet)-[r:创作]->(w:Work)
# RETURN p.name AS 诗人, w.title AS 作品, r.create_place AS 创作地点
# """
# relation_result = graph.run(relation_query).data()
# print("\n===== 所有创作关系信息 =====")
# for rel in relation_result:
#     print(rel)

# 1. 更新实体属性（为李白添加“逝世年份”属性）
# li_bai_node = node_matcher.match("Poet", name="李白").first()
# if li_bai_node:
#     li_bai_node["death_year"] = 762
#     graph.push(li_bai_node)
#     print("成功更新李白的逝世年份属性！")

# 2. 删除关系（可选：删除李白和杜甫的“好友”关系）
# friend_del_query = """
# MATCH (p1:Poet {name:"李白"})-[r:好友]->(p2:Poet {name:"杜甫"})
# DELETE r
# """
# graph.run(friend_del_query)
# print("成功删除好友关系！")