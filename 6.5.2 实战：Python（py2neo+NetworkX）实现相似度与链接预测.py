from py2neo import Graph, Node, Relationship
import networkx as nx
import matplotlib.pyplot as plt
from networkx.algorithms import similarity, link_prediction

# ---------------------- 1. 连接Neo4j并写入用户-电影数据 ----------------------
graph = Graph("bolt://localhost:7687", user="neo4j", password="123456")

# 清空现有数据
graph.run("MATCH (n) WHERE n:User OR n:Movie DETACH DELETE n")

# 创建用户和电影节点
users = ["U1", "U2", "U3", "U4", "U5"]
movies = ["M1（科幻）", "M2（科幻）", "M3（喜剧）", "M4（喜剧）", "M5（悬疑）"]
nodes = {}
# 添加用户节点
for user in users:
    nodes[user] = Node("User", id=user)
    graph.create(nodes[user])
# 添加电影节点
for movie in movies:
    nodes[movie] = Node("Movie", name=movie)
    graph.create(nodes[movie])

# 创建观影关系
edges = [
    ("U1", "M1（科幻）"), ("U1", "M2（科幻）"), ("U1", "M5（悬疑）"),
    ("U2", "M1（科幻）"), ("U2", "M3（喜剧）"),
    ("U3", "M2（科幻）"), ("U3", "M4（喜剧）"), ("U3", "M5（悬疑）"),
    ("U4", "M3（喜剧）"), ("U4", "M4（喜剧）"),
    ("U5", "M1（科幻）"), ("U5", "M4（喜剧）")
]
for start, end in edges:
    rel = Relationship(nodes[start], "WATCHED", nodes[end])
    graph.create(rel)

# ---------------------- 2. 从Neo4j读取数据构建二分图 ----------------------
def build_bipartite_graph():
    G = nx.Graph()  # 修改这里：使用 nx.Graph() 而不是 nx.bipartite.Graph()
    # 读取用户和电影节点，标注分区（0：用户，1：电影）
    users_result = graph.run("MATCH (n:User) RETURN n.id AS id").data()
    movies_result = graph.run("MATCH (n:Movie) RETURN n.name AS name").data()
    G.add_nodes_from([user["id"] for user in users_result], bipartite=0)
    G.add_nodes_from([movie["name"] for movie in movies_result], bipartite=1)
    # 读取观影关系
    edges_result = graph.run("MATCH (a:User)-[r:WATCHED]->(b:Movie) RETURN a.id AS user, b.name AS movie").data()
    for edge in edges_result:
        G.add_edge(edge["user"], edge["movie"])
    return G

G = build_bipartite_graph()

# ---------------------- 3. 可视化二分图 ----------------------
plt.rcParams["font.sans-serif"] = ["SimHei"]
pos = nx.bipartite_layout(G, users)  # 二分图布局
nx.draw(G, pos, with_labels=True, node_size=2000,
        node_color=["#673AB7" if n in users else "#E91E63" for n in G.nodes()],
        font_size=10, font_color="white")
plt.title("用户-电影观影二分图")
plt.show()

# ---------------------- 4. 执行相似度与链接预测算法 ----------------------
# 1. 投影到用户网络（基于共同观影）
user_graph = nx.bipartite.projection.projected_graph(G, users)
# 计算用户间Jaccard相似度
jaccard_sim = similarity.jaccard_coefficient(user_graph, [("U1", "U5"), ("U2", "U4"), ("U1", "U3")])
print("=== 用户Jaccard相似度 ===")
for u1, u2, sim in jaccard_sim:
    print(f"{u1} & {u2}: {sim:.4f}")

# 2. 链接预测（Adamic-Adar指数，预测用户可能观看的电影）
# 待预测的用户-电影对
candidate_pairs = [("U1", "M3（喜剧）"), ("U5", "M2（科幻）"), ("U2", "M5（悬疑）")]
aa_pred = link_prediction.adamic_adar_index(G, candidate_pairs)
print("\n=== 潜在观影链接预测（Adamic-Adar） ===")
for u, m, score in aa_pred:
    print(f"{u} → {m}: 预测分数 {score:.4f}")

# ---------------------- 5. 预测结果回写Neo4j（供推荐业务使用） ----------------------
# 给用户添加推荐电影列表
for u, m, score in link_prediction.adamic_adar_index(G, candidate_pairs):
    if score > 0:  # 只保留有预测价值的结果
        user_node = nodes[u]
        # 读取现有推荐列表，避免重复
        current_recs = user_node.get("recommended_movies", [])
        if m not in current_recs:
            current_recs.append({"movie": m, "prediction_score": round(score, 4)})
        user_node["recommended_movies"] = current_recs
        graph.push(user_node)

# 验证回写结果
result = graph.run("MATCH (u:User {id: 'U1'}) RETURN u.recommended_movies AS recs").data()
print("\n=== U1的推荐电影（Neo4j回写结果） ===")
for rec in result[0]["recs"]:
    print(f"{rec['movie']}: 预测分数{rec['prediction_score']}")