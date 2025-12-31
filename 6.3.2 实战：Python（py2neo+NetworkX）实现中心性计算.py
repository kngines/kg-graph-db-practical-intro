from py2neo import Graph, Node, Relationship
import networkx as nx
import matplotlib.pyplot as plt

# ---------------------- 1. 连接Neo4j并写入社交网络数据 ----------------------
# graph = Graph("bolt://localhost:7687", user="neo4j", password="123456")
graph = Graph("bolt://localhost:7687")

# 清空现有数据
graph.run("MATCH (n:User) DETACH DELETE n")

# 创建用户节点
users = ["用户A", "用户B", "用户C", "用户D", "用户E", "用户F"]
nodes = {user: Node("User", name=user) for user in users}
for node in nodes.values():
    graph.create(node)

# 创建关注关系（有向边：(关注者, 被关注者)）
edges = [
    ("用户A", "用户B"), ("用户A", "用户C"), ("用户B", "用户C"),
    ("用户B", "用户D"), ("用户C", "用户D"), ("用户D", "用户E"),
    ("用户E", "用户D"), ("用户F", "用户C"), ("用户F", "用户E")
]
for start, end in edges:
    rel = Relationship(nodes[start], "FOLLOWS", nodes[end])
    graph.create(rel)

# ---------------------- 2. 从Neo4j读取数据构建图 ----------------------
def build_social_graph():
    # 构建有向图（关注是单向的）
    G = nx.DiGraph()
    # 读取节点
    nodes_result = graph.run("MATCH (n:User) RETURN n.name AS name").data()
    for node in nodes_result:
        G.add_node(node["name"])
    # 读取关注关系
    edges_result = graph.run("MATCH (a:User)-[r:FOLLOWS]->(b:User) RETURN a.name AS start, b.name AS end").data()
    for edge in edges_result:
        G.add_edge(edge["start"], edge["end"])
    return G

G = build_social_graph()

# ---------------------- 3. 可视化社交网络 ----------------------
plt.rcParams["font.sans-serif"] = ["SimHei"]
pos = nx.kamada_kawai_layout(G)  # 力导向布局
nx.draw(G, pos, with_labels=True, node_size=2000, node_color="#2196F3", font_size=11, font_color="white")
plt.title("社交网络关注关系")
plt.show()

# ---------------------- 4. 执行中心性算法 ----------------------
# 1. PageRank（阻尼系数0.85，默认值）
pagerank = nx.pagerank(G, alpha=0.85)
print("=== PageRank（影响力排名） ===")
for user, score in sorted(pagerank.items(), key=lambda x: x[1], reverse=True):
    print(f"{user}: {score:.4f}")

# 2. 中介中心性（无向化处理，社交网络分析常用）
# 转换为无向图计算中介中心性
undir_G = G.to_undirected()
betweenness = nx.betweenness_centrality(undir_G, normalized=True)
print("\n=== 中介中心性（桥梁作用） ===")
for user, score in sorted(betweenness.items(), key=lambda x: x[1], reverse=True):
    print(f"{user}: {score:.4f}")

# 3. 紧密中心性
closeness = nx.closeness_centrality(undir_G)
print("\n=== 紧密中心性（传播效率） ===")
for user, score in sorted(closeness.items(), key=lambda x: x[1], reverse=True):
    print(f"{user}: {score:.4f}")

# ---------------------- 5. 结果回写Neo4j ----------------------
for user in users:
    node = nodes[user]
    node["pagerank_score"] = round(pagerank[user], 4)
    node["betweenness_score"] = round(betweenness[user], 4)
    node["closeness_score"] = round(closeness[user], 4)
    graph.push(node)

# 验证回写结果
result = graph.run("MATCH (u:User) RETURN u.name AS user, u.pagerank_score AS pagerank ORDER BY pagerank DESC").data()
print("\n=== Neo4j回写结果（PageRank） ===")
for item in result:
    print(f"{item['user']}: {item['pagerank']}")