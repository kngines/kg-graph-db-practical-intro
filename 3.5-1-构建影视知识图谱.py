from py2neo import Graph, Node, Relationship

# 连接Neo4j数据库（默认用户名neo4j，密码需自行修改）
graph = Graph("bolt://localhost:7687")

# 清空现有数据（测试用，生产环境慎用）
graph.delete_all()

# 1. 创建实体节点（演员、电影、导演、类型）
actor1 = Node("Actor", name="吴京", nationality="中国", birth_year=1974)
actor2 = Node("Actor", name="刘德华", nationality="中国", birth_year=1961)
movie1 = Node("Movie", name="流浪地球2", release_year=2023, box_office="40.29亿")
movie2 = Node("Movie", name="战狼2", release_year=2017, box_office="56.94亿")
director1 = Node("Director", name="郭帆", nationality="中国", birth_year=1980)
director2 = Node("Director", name="吴京", nationality="中国", birth_year=1974)  # 吴京同时是导演
genre1 = Node("Genre", name="科幻")
genre2 = Node("Genre", name="动作")

# 2. 创建关系（参演、执导、属于、合作）
rel1 = Relationship(actor1, "ACTED_IN", movie1, role="刘培强")
rel2 = Relationship(actor1, "ACTED_IN", movie2, role="冷锋")
rel3 = Relationship(actor2, "ACTED_IN", movie1, role="图恒宇")
rel4 = Relationship(director1, "DIRECTED", movie1)
rel5 = Relationship(director2, "DIRECTED", movie2)
rel6 = Relationship(movie1, "BELONGS_TO", genre1)
rel7 = Relationship(movie2, "BELONGS_TO", genre2)
rel8 = Relationship(actor1, "COOPERATED_WITH", actor2, works="流浪地球2")

# 3. 将节点和关系写入Neo4j
graph.create(actor1 | actor2 | movie1 | movie2 | director1 | director2 | genre1 | genre2)
graph.create(rel1 | rel2 | rel3 | rel4 | rel5 | rel6 | rel7 | rel8)

print("影视知识图谱构建完成！")