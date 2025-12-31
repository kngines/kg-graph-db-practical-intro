from py2neo import Graph
import pandas as pd

graph = Graph("bolt://localhost:7687", user="neo4j", password="123456")

# 优化前：逐行读取数据，效率低
# edges_result = graph.run("MATCH (a:User)-[r:CO_BUY]->(b:User) RETURN a.id, b.id, r.count").data()

# 优化后：批量读取为DataFrame，提升效率
def batch_read_edges():
    query = """
    MATCH (a:User)-[r:CO_BUY]->(b:User)
    RETURN a.id AS start, b.id AS end, r.count AS count
    """
    # 批量读取并转换为DataFrame
    df = graph.run(query).to_data_frame()
    return df.values.tolist()  # 转换为列表，便于构建NetworkX图

edges = batch_read_edges()
print(f"批量读取到{len(edges)}条边")