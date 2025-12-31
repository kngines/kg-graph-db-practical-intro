# 导入所需库
from rdflib import Graph, URIRef
from neo4j import GraphDatabase

# 1. 加载本地RDF链接数据
rdf_graph = Graph()
rdf_graph.parse("linked_data_graph.rdf", format="xml")
print("===== 成功加载本地链接数据 =====")

# 2. 配置Neo4j连接信息（请替换为你的Neo4j密码）
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your_neo4j_password"  # 替换为你的Neo4j数据库密码

# 3. 创建Neo4j驱动并实现数据转换
class RDF2Neo4jConverter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def convert_rdf_to_kg(self, rdf_graph):
        """将RDF三元组转换为Neo4j知识图谱（节点+关系）"""
        with self.driver.session() as session:
            for subj, pred, obj in rdf_graph:
                session.execute_write(self._create_kg_entities, subj, pred, obj)
        print("===== 链接数据已成功转换为Neo4j知识图谱 =====")

    @staticmethod
    def _create_kg_entities(tx, subj, pred, obj):
        """内部方法：创建节点和关系"""
        # 处理主体节点（提取URI中的实体ID，创建/匹配节点）
        subj_id = str(subj).split("/")[-1]
        subj_uri = str(subj)
        tx.run(
            "MERGE (s:Entity {id: $id, uri: $uri})",
            id=subj_id, uri=subj_uri
        )

        # 处理客体：分URI实体和文字字面量两种情况
        if isinstance(obj, URIRef):
            # 客体是URI实体：创建/匹配节点，并建立关系
            obj_id = str(obj).split("/")[-1]
            obj_uri = str(obj)
            tx.run(
                "MERGE (o:Entity {id: $id, uri: $uri})",
                id=obj_id, uri=obj_uri
            )

            # 建立主体到客体的关系（关系类型为谓词名称）
            rel_type = str(pred).split("/")[-1]
            tx.run("""
                MATCH (s:Entity {uri: $subj_uri}), (o:Entity {uri: $obj_uri})
                MERGE (s)-[r:`%s`]->(o)
            """ % rel_type, subj_uri=subj_uri, obj_uri=obj_uri)
        else:
            # 客体是文字字面量：作为主体节点的属性
            prop_name = str(pred).split("/")[-1]
            prop_value = str(obj)
            # 处理多语言属性（如"张三"@zh）
            if hasattr(obj, "language") and obj.language:
                prop_name += f"_{obj.language}"

            # 使用字符串格式化构建Cypher查询，因为属性名不能参数化
            # 使用字符串格式化构建Cypher查询，因为属性名不能参数化
            cypher_query = """
                MATCH (s:Entity {{uri: $subj_uri}})
                SET s.`{prop_name}` = $prop_value
            """.format(prop_name=prop_name.replace('`', ''))  # 防止注入，移除反引号

            tx.run(cypher_query, subj_uri=subj_uri, prop_value=prop_value)

    def query_kg(self):
        """在Neo4j中查询知识图谱数据（Cypher查询）"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (author:Entity {id: "ZhangSan"})-[r]->(book:Entity {id: "GraphDBBook"})
                RETURN 
                    author.id AS 作者ID,
                    author.name_zh AS 作者姓名,
                    author.title AS 作者职业,
                    type(r) AS 关系类型,
                    book.id AS 书籍ID,
                    book.title AS 书籍名称
            """)
            print("===== Neo4j知识图谱查询结果 =====")
            for record in result:
                for key, value in record.items():
                    print(f"{key}：{value}")

# 4. 执行转换与查询
if __name__ == "__main__":
    converter = RDF2Neo4jConverter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        # 转换RDF链接数据到Neo4j知识图谱
        converter.convert_rdf_to_kg(rdf_graph)
        # 查询知识图谱
        converter.query_kg()
    finally:
        # 关闭Neo4j连接
        converter.close()
        print("\n===== Neo4j连接已关闭 =====")