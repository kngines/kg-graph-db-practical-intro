from py2neo import Graph


class KGRecommender:
    def __init__(self, neo4j_auth, neo4j_db="neo4j"):
        # 初始化Neo4j连接
        self.graph = Graph(
            "bolt://localhost:7687"
        )

    def recommend_classmate_research(self, person_name):
        """推荐目标人物同学的研究方向（学术推荐）"""
        query = """
        MATCH (p:Person {name: $name})-[r:大学同学]->(classmate:Person)
        RETURN classmate.name AS classmate_name, classmate.research_field AS research_field
        """
        results = self.graph.run(query, name=person_name).data()
        return results

    def recommend_similar_organization(self, org_name):
        """推荐与目标机构类型相同的机构（企业/高校推荐）"""
        query = """
        MATCH (target:Organization {name: $name})
        MATCH (similar:Organization {type: target.type}) WHERE similar.name <> $name
        RETURN similar.name AS org_name, similar.type AS org_type
        """
        results = self.graph.run(query, name=org_name).data()
        return results


# 初始化推荐器
recommender = KGRecommender(neo4j_auth=("neo4j", "your_custom_password"))

# 场景1：推荐张三同学的研究方向
classmate_research = recommender.recommend_classmate_research("张三")
print("场景1：张三同学的研究方向推荐")
for rec in classmate_research:
    print(f"同学：{rec['classmate_name']}, 研究方向：{rec['research_field']}")

# 场景2：推荐与北京大学类型相同的机构（此处暂无其他高校，可补充数据后测试）
similar_orgs = recommender.recommend_similar_organization("北京大学")
print("\n场景2：与北京大学同类的机构推荐")
if similar_orgs:
    for rec in similar_orgs:
        print(f"机构名称：{rec['org_name']}, 机构类型：{rec['org_type']}")
else:
    print("暂无同类机构数据，可补充清华大学、复旦大学等高校数据后重试")