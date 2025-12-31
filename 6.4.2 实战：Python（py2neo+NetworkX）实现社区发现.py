from py2neo import Graph, Node, Relationship
import networkx as nx
import community as community_louvain  # python-louvain库
import matplotlib.pyplot as plt

# ---------------------- 1. 连接Neo4j并写入电商用户数据 ----------------------
graph = Graph("bolt://localhost:7687", user="neo4j", password="123456")

# 清空现有数据
graph.run("MATCH (n:User) DETACH DELETE n")

# 创建用户节点
users = ["U1", "U2", "U3", "U4", "U5", "U6", "U7", "U8"]
nodes = {user: Node("User", id=user) for user in users}
for node in nodes.values():
    graph.create(node)

# 创建共同购买关系（带权重：共同购买次数）
edges = [
    ("U1", "U2", 3), ("U1", "U3", 2), ("U2", "U3", 4),
    ("U3", "U4", 1), ("U4", "U5", 3), ("U5", "U6", 2),
    ("U6", "U4", 4), ("U7", "U8", 3), ("U7", "U1", 1), ("U8", "U2", 1)
]
for start, end, count in edges:
    rel = Relationship(nodes[start], "CO_BUY", nodes[end], count=count)
    graph.create(rel)
    # 无向边：反向创建
    rel_rev = Relationship(nodes[end], "CO_BUY", nodes[start], count=count)
    graph.create(rel_rev)

# ---------------------- 2. 从Neo4j读取数据构建图 ----------------------
def build_user_graph():
    G = nx.Graph()
    # 读取节点
    nodes_result = graph.run("MATCH (n:User) RETURN n.id AS id").data()
    for node in nodes_result:
        G.add_node(node["id"])
    # 读取带权边
    edges_result = graph.run("MATCH (a:User)-[r:CO_BUY]->(b:User) RETURN a.id AS start, b.id AS end, r.count AS count").data()
    for edge in edges_result:
        G.add_weighted_edges_from([(edge["start"], edge["end"], edge["count"])])
    return G

G = build_user_graph()

# ---------------------- 3. 执行社区发现算法 ----------------------
# 1. Louvain算法（基于共同购买次数加权）
louvain_partition = community_louvain.best_partition(G, weight="weight")
print("=== Louvain社区划分 ===")
for community_id in set(louvain_partition.values()):
    members = [user for user, cid in louvain_partition.items() if cid == community_id]
    print(f"社区{community_id}: {members}")

# 2. 标签传播算法
label_propagation_partition = nx.algorithms.community.label_propagation.label_propagation_communities(G)
print("\n=== 标签传播社区划分 ===")
for idx, community in enumerate(label_propagation_partition):
    print(f"社区{idx}: {list(community)}")

# ---------------------- 4. 可视化社区划分 ----------------------
plt.rcParams["font.sans-serif"] = ["SimHei"]
pos = nx.spring_layout(G, seed=42)
# Louvain社区着色
colors = ["#FF9800", "#9C27B0", "#00BCD4"]
node_colors = [colors[louvain_partition[user]] for user in G.nodes()]
nx.draw(G, pos, with_labels=True, node_size=2000, node_color=node_colors, font_size=12)
plt.title("电商用户社区划分（Louvain）")
plt.show()

# ---------------------- 5. 结果回写Neo4j ----------------------
for user in users:
    node = nodes[user]
    node["louvain_community"] = louvain_partition[user]
    # 标签传播结果（取第一个匹配的社区ID）
    for idx, community in enumerate(label_propagation_partition):
        if user in community:
            node["lp_community"] = idx
            break
    graph.push(node)

# 验证回写结果
result = graph.run("MATCH (u:User) RETURN u.id AS user, u.louvain_community AS louvain_cid ORDER BY louvain_cid").data()
print("\n=== Neo4j回写结果（Louvain社区） ===")
for item in result:
    print(f"{item['user']}: 社区{item['louvain_cid']}")