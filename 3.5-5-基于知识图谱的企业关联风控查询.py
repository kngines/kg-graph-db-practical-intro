import jieba
import pandas as pd
from py2neo import Graph, Node, Relationship

# 连接Neo4j数据库（默认用户名neo4j，密码需自行修改）
graph = Graph("bolt://localhost:7687")

# 清空现有数据（测试用，生产环境慎用）
graph.delete_all()

def build_finance_kg():
    """构建简单金融风控知识图谱（企业、股东、担保关系）"""
    # 清空现有影视知识图谱（单独构建金融图谱，也可保留多类图谱）
    graph.delete_all()

    # 创建实体节点（企业、股东、银行）
    company1 = Node("Company", name="A科技有限公司", credit_rating="AA", status="正常")
    company2 = Node("Company", name="B制造有限公司", credit_rating="BB", status="逾期")
    company3 = Node("Company", name="C贸易有限公司", credit_rating="A", status="正常")
    shareholder1 = Node("Shareholder", name="张三", id_card="11010119900101XXXX")
    shareholder2 = Node("Shareholder", name="李四", id_card="12010119850505XXXX")
    bank1 = Node("Bank", name="中国工商银行", branch="北京分行")

    # 创建关系（持股、担保、贷款）
    rel1 = Relationship(shareholder1, "HOLDS_SHARES", company1, ratio=0.6)  # 张三持股A公司60%
    rel2 = Relationship(shareholder1, "HOLDS_SHARES", company2, ratio=0.3)  # 张三持股B公司30%
    rel3 = Relationship(company1, "GUARANTEES", company2, amount="5000万")  # A公司为B公司担保5000万
    rel4 = Relationship(company2, "APPLIED_LOAN", bank1, amount="8000万", status="逾期")  # B公司在工行贷款8000万（逾期）
    rel5 = Relationship(company3, "GUARANTEES", company2, amount="3000万")  # C公司为B公司担保3000万

    # 写入Neo4j
    graph.create(company1 | company2 | company3 | shareholder1 | shareholder2 | bank1)
    graph.create(rel1 | rel2 | rel3 | rel4 | rel5)

    print("金融风控知识图谱构建完成！")


def query_related_risk(company_name):
    """查询企业的关联风险（担保企业、股东关联企业、风险传导路径）"""
    # 1. 查询该企业的担保对象及风险状态
    guarantee_cypher = f"""
    MATCH (c:Company {{name: '{company_name}'}})-[g:GUARANTEES]->(target_c:Company)
    RETURN '担保对象' AS 关联类型, target_c.name AS 关联企业, 
           target_c.status AS 企业状态, g.amount AS 担保金额
    """
    # 2. 查询该企业的股东关联企业
    shareholder_cypher = f"""
    MATCH (c:Company {{name: '{company_name}'}})<-[h:HOLDS_SHARES]-(s:Shareholder)
    MATCH (s)-[h2:HOLDS_SHARES]->(other_c:Company)
    WHERE other_c.name <> '{company_name}'
    RETURN '股东关联' AS 关联类型, other_c.name AS 关联企业, 
           other_c.status AS 企业状态, h2.ratio AS 持股比例
    """
    # 3. 查询风险传导路径（若关联企业逾期）
    risk_cypher = f"""
    MATCH path = (c:Company {{name: '{company_name}'}})-[*1..2]->(risk_c:Company {{status: '逾期'}})
    RETURN '风险传导路径' AS 关联类型, 
           reduce(names = '', n IN nodes(path) | names + n.name + ' -> ') AS 传导路径,
           risk_c.name AS 风险企业, '逾期' AS 风险状态
    """

    # 合并查询结果
    guarantee_result = graph.run(guarantee_cypher).data()
    shareholder_result = graph.run(shareholder_cypher).data()
    risk_result = graph.run(risk_cypher).data()
    all_result = guarantee_result + shareholder_result + risk_result

    if not all_result:
        return f"未查询到{company_name}的关联风险信息"
    return pd.DataFrame(all_result)


# 测试金融风控查询
if __name__ == "__main__":
    # 构建金融知识图谱
    build_finance_kg()

    # 查询A科技有限公司的关联风险
    print("=== A科技有限公司关联风险查询 ===")
    print(query_related_risk("A科技有限公司"))