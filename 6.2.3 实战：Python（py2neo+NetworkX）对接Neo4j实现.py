from py2neo import Graph, Node, Relationship
import networkx as nx

# ---------------------- 1. 连接Neo4j并写入数据 ----------------------
graph = Graph("bolt://localhost:7687")

# 清空现有数据（避免重复，测试用）
graph.run("MATCH (n:City) DETACH DELETE n")

# 创建城市节点
cities = ["上海", "南京", "杭州", "合肥", "苏州", "无锡"]
nodes = {city: Node("City", name=city) for city in cities}
for node in nodes.values():
    graph.create(node)

# 创建带权运输边（cost：运输成本）
edges = [
    ("上海", "南京", 30), ("上海", "杭州", 20), ("上海", "苏州", 10),
    ("南京", "合肥", 25), ("南京", "无锡", 15), ("苏州", "无锡", 5),
    ("杭州", "合肥", 40), ("无锡", "合肥", 35)
]
for start, end, cost in edges:
    rel = Relationship(nodes[start], "TRANSPORT", nodes[end], cost=cost)
    graph.create(rel)
    # 无向边：反向再创建一条（Neo4j本身是有向图，模拟无向）
    rel_rev = Relationship(nodes[end], "TRANSPORT", nodes[start], cost=cost)
    graph.create(rel_rev)


# ---------------------- 2. 从Neo4j读取数据构建NetworkX图 ----------------------
def build_graph_from_neo4j():
    G = nx.Graph()
    # 读取所有城市节点
    nodes_result = graph.run("MATCH (n:City) RETURN n.name AS name").data()
    for node in nodes_result:
        G.add_node(node["name"])

    # 读取所有运输边（带成本）
    edges_result = graph.run(
        "MATCH (a:City)-[r:TRANSPORT]->(b:City) RETURN a.name AS start, b.name AS end, r.cost AS cost").data()
    for edge in edges_result:
        G.add_weighted_edges_from([(edge["start"], edge["end"], edge["cost"])])
    return G


G = build_graph_from_neo4j()

# ---------------------- 3. 执行最短路径算法 ----------------------
# Dijkstra算法
dijkstra_path = nx.dijkstra_path(G, source="上海", target="合肥", weight="weight")
dijkstra_cost = nx.dijkstra_path_length(G, source="上海", target="合肥", weight="weight")
print(f"Dijkstra最短路径：{' → '.join(dijkstra_path)}，总成本：{dijkstra_cost}百元")

# A*算法
heuristic = {
    "上海": 40, "南京": 25, "杭州": 40, "合肥": 0, "苏州": 30, "无锡": 35
}
astar_path = nx.astar_path(
    G, source="上海", target="合肥",
    heuristic=lambda u, v: heuristic[v],
    weight="weight"
)
astar_cost = nx.astar_path_length(G, source="上海", target="合肥", heuristic=lambda u, v: heuristic[v], weight="weight")
print(f"A*最短路径：{' → '.join(astar_path)}，总成本：{astar_cost}百元")

# ---------------------- 4. 算法结果回写Neo4j（可选，供业务查询） ----------------------
# 给起点节点添加最短路径属性
start_node = nodes["上海"]
start_node["shortest_path_to_合肥"] = " → ".join(dijkstra_path)
start_node["shortest_path_cost"] = dijkstra_cost
graph.push(start_node)  # 更新节点属性