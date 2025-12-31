import pandas as pd
from py2neo import Graph, Node, Relationship

# 连接Neo4j数据库（默认用户名neo4j，密码需自行修改）
graph = Graph("bolt://localhost:7687")

def recommend_movie_by_director(movie_name):
    """根据电影导演，推荐该导演的其他作品"""
    cypher = f"""
    MATCH (target_m:Movie {{name: '{movie_name}'}})<-[r:DIRECTED]-(d:Director)
    MATCH (d)-[r2:DIRECTED]->(rec_m:Movie)
    WHERE rec_m.name <> '{movie_name}'
    RETURN d.name AS 导演, rec_m.name AS 推荐电影, 
           rec_m.release_year AS 上映年份, rec_m.box_office AS 票房
    """
    result = graph.run(cypher).data()
    if not result:
        return f"未查询到《{movie_name}》导演的其他作品"
    return pd.DataFrame(result)


def recommend_movie_by_actor(movie_name):
    """根据电影演员，推荐该演员参演的其他作品"""
    cypher = f"""
    MATCH (target_m:Movie {{name: '{movie_name}'}})<-[r:ACTED_IN]-(a:Actor)
    MATCH (a)-[r2:ACTED_IN]->(rec_m:Movie)
    WHERE rec_m.name <> '{movie_name}'
    RETURN a.name AS 演员, rec_m.name AS 推荐电影, 
           rec_m.release_year AS 上映年份, rec_m.box_office AS 票房
    """
    result = graph.run(cypher).data()
    if not result:
        return f"未查询到《{movie_name}》演员的其他作品"
    return pd.DataFrame(result)


# 测试推荐功能
if __name__ == "__main__":
    # 根据《流浪地球2》导演推荐其他作品
    print("=== 基于《流浪地球2》导演的推荐 ===")
    print(recommend_movie_by_director("流浪地球2"))

    # 根据《流浪地球2》演员推荐其他作品
    print("\n=== 基于《流浪地球2》演员的推荐 ===")
    print(recommend_movie_by_actor("流浪地球2"))