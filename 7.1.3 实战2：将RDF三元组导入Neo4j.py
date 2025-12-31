from neo4j import GraphDatabase
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF  # 移除SCHEMA导入

# 手动定义Schema.org命名空间
SCHEMA = Namespace("http://schema.org/")

# 1. 配置Neo4j连接
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "123456"  # 替换为你的Neo4j密码
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 2. 读取RDF文件
g = Graph()
g.parse("book_author.rdf", format="turtle")
EX = Namespace("http://example.org/")


# 3. 定义RDF转Neo4j的函数
def rdf_to_neo4j(tx, subject, predicate, obj):
    # 处理节点：提取URI中的唯一标识（如books/1001 → 1001）
    def get_node_id(uri):
        return uri.split("/")[-1] if isinstance(uri, URIRef) else str(uri)

    # 清理关系类型名称，确保符合Neo4j命名规范
    def clean_rel_type(uri):
        # 提取最后部分
        rel_name = uri.split("/")[-1].split("#")[-1]
        # 移除特殊字符，只保留字母、数字和下划线
        import re
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', rel_name)
        # 如果以数字开头，添加前缀
        if cleaned and cleaned[0].isdigit():
            cleaned = f"rel_{cleaned}"
        return cleaned or "RELATIONSHIP"  # 默认关系类型

    # 处理主体节点
    subj_id = get_node_id(subject)
    subj_type = None
    # 获取主体的类型（如schema:Book）
    for s, p, o in g.triples((subject, RDF.type, None)):
        subj_type = o.split("/")[-1].split("#")[-1]  # schema:Book → Book

    if subj_type:
        tx.run(f"""
            MERGE (n:{subj_type} {{id: $subj_id}})
            SET n.uri = $subj_uri
        """, subj_id=subj_id, subj_uri=str(subject))

    # 处理客体：区分资源（URI）和字面量（Literal）
    if isinstance(obj, URIRef):
        # 客体是资源（节点）
        obj_id = get_node_id(obj)
        obj_type = None
        for s, p, o in g.triples((obj, RDF.type, None)):
            obj_type = o.split("/")[-1].split("#")[-1]

        if obj_type:
            tx.run(f"""
                MERGE (m:{obj_type} {{id: $obj_id}})
                SET m.uri = $obj_uri
            """, obj_id=obj_id, obj_uri=str(obj))

        # 创建节点间关系（谓词作为关系类型）
        rel_type = clean_rel_type(str(predicate))
        tx.run(f"""
            MATCH (n:{subj_type} {{id: $subj_id}}), (m:{obj_type} {{id: $obj_id}})
            MERGE (n)-[r:{rel_type}]->(m)
            SET r.uri = $pred_uri
        """, subj_id=subj_id, obj_id=obj_id, rel_type=rel_type, pred_uri=str(predicate))
    else:
        # 客体是字面量（节点属性）
        prop_name = clean_rel_type(str(predicate))
        tx.run(f"""
            MATCH (n:{subj_type} {{id: $subj_id}})
            SET n.{prop_name} = $obj_value
        """, subj_id=subj_id, obj_value=str(obj))


# 4. 批量导入RDF数据到Neo4j
with driver.session() as session:
    for subj, pred, obj in g:
        session.execute_write(rdf_to_neo4j, subj, pred, obj)

# 5. 验证导入结果
with driver.session() as session:
    result = session.run("""
        MATCH (b:Book)-[r:author]->(p:Person)
        RETURN b.name AS book_name, p.name AS author_name
    """)
    print("\n=== Neo4j导入结果验证 ===")
    for record in result:
        print(f"图书：{record['book_name']}，作者：{record['author_name']}")

driver.close()
