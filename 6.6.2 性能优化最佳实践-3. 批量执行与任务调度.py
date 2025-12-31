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
        # 读取数据（批量）
        nodes_df = graph.run("MATCH (n:User) RETURN n.id AS id").to_data_frame()
        edges_df = graph.run(
            "MATCH (a:User)-[r:CO_BUY]->(b:User) RETURN a.id AS start, b.id AS end, r.count AS count").to_data_frame()
        # 构建图
        G.add_nodes_from(nodes_df["id"].tolist())
        edges = edges_df[["start", "end", "count"]].values.tolist()
        G.add_weighted_edges_from(edges)
        return G

    G = build_graph()

    # 3. 执行社区发现算法
    louvain_partition = community_louvain.best_partition(G, weight="weight")

    # 4. 结果回写Neo4j
    for user, cid in louvain_partition.items():
        graph.run("MATCH (u:User {id: $user}) SET u.louvain_community = $cid", user=user, cid=cid)

    print("全流程分析完成，共处理", len(louvain_partition), "个用户")


if __name__ == "__main__":
    full_analysis_pipeline()