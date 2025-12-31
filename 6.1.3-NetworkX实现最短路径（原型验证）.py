import networkx as nx
import matplotlib.pyplot as plt

# 1. 构建带权无向图（物流网络：城市-运输成本）
G = nx.Graph()
# 节点：城市
nodes = ["上海", "南京", "杭州", "合肥", "苏州", "无锡"]
G.add_nodes_from(nodes)
# 带权边（运输成本，单位：百元）
edges = [
    ("上海", "南京", 30), ("上海", "杭州", 20), ("上海", "苏州", 10),
    ("南京", "合肥", 25), ("南京", "无锡", 15), ("苏州", "无锡", 5),
    ("杭州", "合肥", 40), ("无锡", "合肥", 35)
]
G.add_weighted_edges_from(edges)

# 2. 可视化图结构
plt.rcParams["font.sans-serif"] = ["SimHei"]  # 解决中文显示
pos = nx.spring_layout(G, seed=42)  # 固定布局种子
nx.draw(G, pos, with_labels=True, node_size=2500, node_color="#4CAF50", font_size=12, font_color="white")
edge_labels = nx.get_edge_attributes(G, "weight")
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)
plt.title("长三角物流网络（运输成本）")
plt.show()

# 3. Dijkstra算法：上海→合肥最短路径（最小成本）
dijkstra_path = nx.dijkstra_path(G, source="上海", target="合肥", weight="weight")
dijkstra_cost = nx.dijkstra_path_length(G, source="上海", target="合肥", weight="weight")
print(f"Dijkstra最短路径：{' → '.join(dijkstra_path)}，总成本：{dijkstra_cost}百元")

# 4. A*算法（启发式函数：预估到合肥的运输成本）
heuristic = {
    "上海": 40, "南京": 25, "杭州": 40, "合肥": 0, "苏州": 30, "无锡": 35
}
# A*核心：heuristic函数接收(u, v)，返回v到目标的预估成本
astar_path = nx.astar_path(
    G, source="上海", target="合肥",
    heuristic=lambda u, v: heuristic[v],
    weight="weight"
)
astar_cost = nx.astar_path_length(G, source="上海", target="合肥", heuristic=lambda u, v: heuristic[v], weight="weight")
print(f"A*最短路径：{' → '.join(astar_path)}，总成本：{astar_cost}百元")