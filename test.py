from py2neo import Graph, Node, Relationship
import networkx as nx

# ---------------------- 1. 连接Neo4j并写入数据 ----------------------
graph = Graph("bolt://localhost:7687", user="neo4j", password="123456")

# 清空现有数据（避免重复，测试用）
graph.run("MATCH (n:City) DETACH DELETE n")

# 创建城市节点
cities = ["上海", "南京", "杭州", "合肥", "苏州", "无锡"]
nodes = {city: "aaa" for city in cities}

print( nodes )