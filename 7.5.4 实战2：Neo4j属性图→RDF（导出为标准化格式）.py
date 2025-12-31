from neo4j import GraphDatabase
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD


class Neo4j2RDFConverter:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.EX = Namespace("http://example.org/neo4j2rdf/")  # 自定义命名空间

    def close(self):
        self.driver.close()

    def convert(self, output_file, rdf_format="turtle"):
        """将Neo4j属性图导出为RDF"""
        g = Graph()

        with self.driver.session() as session:
            # 1. 提取所有节点
            node_result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS label, n.id AS id, properties(n) AS props
            """)
            for record in node_result:
                label = record["label"]
                node_id = record["id"]
                props = record["props"]

                # 定义节点URI
                node_uri = self.EX[f"{label.lower()}/{node_id}"]
                # 声明节点类型
                g.add((node_uri, RDF.type, URIRef(f"{self.EX}{label}")))

                # 添加节点属性
                for prop_name, prop_value in props.items():
                    if prop_name not in ["id", "uri"]:
                        prop_uri = self.EX[prop_name]
                        # 处理数据类型
                        if isinstance(prop_value, int):
                            g.add((node_uri, prop_uri, Literal(prop_value, datatype=XSD.int)))
                        elif isinstance(prop_value, str):
                            g.add((node_uri, prop_uri, Literal(prop_value, datatype=XSD.string)))

                # 2. 提取所有关系
                rel_result = session.run("""
                    MATCH (n)-[r]->(m)
                    RETURN labels(n)[0] AS n_label, n.id AS n_id,
                           type(r) AS rel_type,
                           labels(m)[0] AS m_label, m.id AS m_id
                """)
                for rel_record in rel_result:
                    n_uri = self.EX[f"{rel_record['n_label'].lower()}/{rel_record['n_id']}"]
                    m_uri = self.EX[f"{rel_record['m_label'].lower()}/{rel_record['m_id']}"]
                    rel_uri = self.EX[rel_record['rel_type']]

                    # 添加关系三元组
                    g.add((n_uri, rel_uri, m_uri))

        # 序列化RDF文件
        g.serialize(destination=output_file, format=rdf_format)
        print(f"成功将Neo4j属性图导出为RDF文件 {output_file}")


# 工具使用示例
if __name__ == "__main__":
    converter = Neo4j2RDFConverter("bolt://localhost:7687", "neo4j", "123456")
    converter.convert("neo4j_to_rdf.ttl", rdf_format="turtle")
    converter.close()