#!/usr/bin/env python3
# 文件名：user_community_analysis.py
from py2neo import Graph
import networkx as nx
import community as community_louvain


def full_analysis_pipeline():
    # 1. 连接Neo4j
    graph = Graph("bolt://localhost:7687", user="neo4j", password="123456")

    # 2. 构建图
    def build_graph():
        G = nx.Graph()
        # 读取节点数据（批量）
        nodes_df = graph.run("MATCH (n:User) RETURN n.id AS id").to_data_frame()

        # 验证节点数据
        if nodes_df.empty or 'id' not in nodes_df.columns:
            print("警告：没有找到用户节点数据")
            return G

        # 添加节点
        valid_nodes = nodes_df['id'].dropna().tolist()  # 过滤None值
        G.add_nodes_from(valid_nodes)

        # 读取边数据（批量）
        edges_df = graph.run(
            "MATCH (a:User)-[r:CO_BUY]->(b:User) RETURN a.id AS start, b.id AS end, r.count AS count").to_data_frame()

        # 验证边数据
        if not edges_df.empty and all(col in edges_df.columns for col in ['start', 'end', 'count']):
            # 过滤None值的边
            edges_df = edges_df.dropna(subset=['start', 'end', 'count'])
            edges = edges_df[["start", "end", "count"]].values.tolist()
            # 过滤包含None的边
            valid_edges = [(start, end, count) for start, end, count in edges
                           if start is not None and end is not None and count is not None]
            G.add_weighted_edges_from(valid_edges)
        else:
            print("警告：没有找到边数据或列名不匹配")

        return G

    G = build_graph()

    # 检查图是否为空
    if G.number_of_nodes() == 0:
        print("图中没有节点，无法进行社区发现")
        return

    # 3. 执行社区发现算法
    louvain_partition = community_louvain.best_partition(G, weight="weight")

    # 4. 结果回写Neo4j
    for user, cid in louvain_partition.items():
        graph.run("MATCH (u:User {id: $user}) SET u.louvain_community = $cid", user=user, cid=cid)

    print("全流程分析完成，共处理", len(louvain_partition), "个用户")


if __name__ == "__main__":
    full_analysis_pipeline()
