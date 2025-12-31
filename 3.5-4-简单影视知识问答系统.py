import jieba
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

def extract_entity(question, entity_types=["Actor", "Movie"]):
    """简单实体抽取（基于词典匹配，实际场景需用命名实体识别模型）"""
    # 从知识图谱中获取所有实体名称
    entity_names = []
    for et in entity_types:
        cypher = f"MATCH (n:{et}) RETURN n.name AS name"
        results = graph.run(cypher).data()
        entity_names.extend([r["name"] for r in results])

    # 分词后匹配实体
    words = jieba.lcut(question)
    matched_entities = []
    for name in entity_names:
        if name in question:
            matched_entities.append((name, next(et for et in entity_types if name in [r["name"] for r in graph.run(
                f"MATCH (n:{et}) RETURN n.name AS name").data()])))
    return matched_entities


def kbqa(question):
    """知识图谱问答主函数"""
    # 步骤1：抽取实体
    entities = extract_entity(question)
    if not entities:
        return "抱歉，我无法理解你的问题中的实体信息"

    entity_name, entity_type = entities[0]
    question_lower = question.lower()

    # 步骤2：匹配问题意图并执行查询
    if entity_type == "Actor" and ("参演" in question or "演了" in question):
        # 问题："吴京参演了哪些电影？"
        return search_actor_works(entity_name)
    elif entity_type == "Movie" and ("导演" in question or "执导" in question):
        # 问题："《流浪地球2》的导演是谁？"
        cypher = f"""
        MATCH (d:Director)-[r:DIRECTED]->(m:Movie {{name: '{entity_name}'}})
        RETURN d.name AS 导演
        """
        result = graph.run(cypher).data()
        if not result:
            return f"未查询到《{entity_name}》的导演信息"
        return f"《{entity_name}》的导演是：{','.join([r['导演'] for r in result])}"
    elif entity_type == "Movie" and ("演员" in question or "主演" in question):
        # 问题："《战狼2》的演员有哪些？"
        cypher = f"""
        MATCH (a:Actor)-[r:ACTED_IN]->(m:Movie {{name: '{entity_name}'}})
        RETURN a.name AS 演员
        """
        result = graph.run(cypher).data()
        if not result:
            return f"未查询到《{entity_name}》的演员信息"
        return f"《{entity_name}》的演员有：{','.join([r['演员'] for r in result])}"
    elif entity_type == "Movie" and ("票房" in question or "收入" in question):
        # 问题："《战狼2》的票房是多少？"
        cypher = f"""
        MATCH (m:Movie {{name: '{entity_name}'}})
        RETURN m.box_office AS 票房
        """
        result = graph.run(cypher).data()
        if not result:
            return f"未查询到《{entity_name}》的票房信息"
        return f"《{entity_name}》的票房是：{result[0]['票房']}"
    else:
        return "抱歉，我暂时无法回答这个问题"

# 测试问答功能
if __name__ == "__main__":
    questions = [
        "吴京参演了哪些电影？",
        "《流浪地球2》的导演是谁？",
        "《战狼2》的演员有哪些？",
        "《战狼2》的票房是多少？",
        "吴京还有哪些电影？"
    ]

    for q in questions:
        print(f"问题：{q}")
        print(f"答案：{kbqa(q)}")
        print("-" * 50)