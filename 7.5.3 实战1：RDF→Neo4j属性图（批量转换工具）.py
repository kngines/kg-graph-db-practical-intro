from neo4j import GraphDatabase
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF


class RDF2Neo4jConverter:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def close(self):
        self.driver.close()

    def _get_node_label(self, uri, rdf_graph):
        """从RDF中提取节点的类型作为Neo4j Label"""
        types = [t for t in rdf_graph.objects(URIRef(uri), RDF.type)]
        return types[0].split("/")[-1] if types else "Resource"

    def _clean_name(self, uri):
        """清理URI名称，确保符合Neo4j命名规范"""
        # 提取最后部分
        name = uri.split("/")[-1].split("#")[-1]
        # 移除特殊字符，只保留字母、数字和下划线
        import re
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # 如果以数字开头，添加前缀
        if cleaned and cleaned[0].isdigit():
            cleaned = f"rel_{cleaned}"
        return cleaned or "RELATIONSHIP"  # 默认名称

    def convert(self, rdf_file, rdf_format="turtle"):
        """将RDF文件转换为Neo4j属性图"""
        # 读取RDF文件
        g = Graph()
        g.parse(rdf_file, format=rdf_format)

        with self.driver.session() as session:
            # 1. 创建所有节点
            nodes = set([s for s, p, o in g] + [o for s, p, o in g if isinstance(o, URIRef)])
            for node in nodes:
                if isinstance(node, URIRef):
                    label = self._get_node_label(node, g)
                    node_id = node.split("/")[-1]
                    session.run(f"""
                        MERGE (n:{label} {{id: $node_id}})
                        SET n.uri = $node_uri
                    """, node_id=node_id, node_uri=str(node))

            # 2. 创建关系和属性
            for s, p, o in g:
                s_id = s.split("/")[-1]
                s_label = self._get_node_label(s, g)
                p_name = self._clean_name(str(p))  # 使用清理后的名称

                if isinstance(o, URIRef):
                    # 客体是节点，创建关系
                    o_id = o.split("/")[-1]
                    o_label = self._get_node_label(o, g)
                    session.run(f"""
                        MATCH (n:{s_label} {{id: $s_id}}), (m:{o_label} {{id: $o_id}})
                        MERGE (n)-[r:{p_name}]->(m)
                        SET r.uri = $p_uri
                    """, s_id=s_id, o_id=o_id, p_name=p_name, p_uri=str(p))
                elif isinstance(o, Literal):
                    # 客体是字面量，设置属性
                    p_name = self._clean_name(str(p))  # 使用清理后的名称
                    session.run(f"""
                        MATCH (n:{s_label} {{id: $s_id}})
                        SET n.{p_name} = $o_value
                    """, s_id=s_id, p_name=p_name, o_value=str(o))

        print(f"成功将RDF文件 {rdf_file} 转换为Neo4j属性图")

# 工具使用示例
if __name__ == "__main__":
    converter = RDF2Neo4jConverter("bolt://localhost:7687", "neo4j", "123456")
    converter.convert("book_author.rdf", rdf_format="turtle")
    converter.close()