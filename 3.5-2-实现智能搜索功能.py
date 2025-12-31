import pandas as pd
from py2neo import Graph, Node, Relationship

# 连接Neo4j数据库（默认用户名neo4j，密码需自行修改）
graph = Graph("bolt://localhost:7687")

def search_actor_works(actor_name):
    """搜索指定演员的参演作品及详情"""
    cypher = f"""
    MATCH (a:Actor {{name: '{actor_name}'}})-[r:ACTED_IN]->(m:Movie)
    RETURN a.name AS 演员, m.name AS 电影名称, m.release_year AS 上映年份, 
           m.box_office AS 票房, r.role AS 饰演角色
    """
    result = graph.run(cypher).data()
    if not result:
        return f"未查询到演员{actor_name}的参演作品"
    return pd.DataFrame(result)


def search_movie_related(movie_name):
    """搜索指定电影的关联信息（导演、演员、类型）"""
    cypher = f"""
    MATCH (m:Movie {{name: '{movie_name}'}})
    OPTIONAL MATCH (d:Director)-[r:DIRECTED]->(m)
    OPTIONAL MATCH (a:Actor)-[r2:ACTED_IN]->(m)
    OPTIONAL MATCH (m)-[r3:BELONGS_TO]->(g:Genre)
    RETURN m.name AS 电影名称, collect(d.name) AS 导演, 
           collect(a.name) AS 演员, collect(g.name) AS 类型,
           m.box_office AS 票房
    """
    result = graph.run(cypher).data()
    if not result:
        return f"未查询到电影{movie_name}的关联信息"
    return pd.DataFrame(result)


# 测试搜索功能
if __name__ == "__main__":
    # 搜索吴京的参演作品
    print("=== 吴京的参演作品 ===")
    print(search_actor_works("吴京"))

    # 搜索《流浪地球2》的关联信息
    print("\n=== 《流浪地球2》关联信息 ===")
    print(search_movie_related("流浪地球2"))