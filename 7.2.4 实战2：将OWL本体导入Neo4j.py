from neo4j import GraphDatabase
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL  # 移除SCHEMA导入

# 手动定义Schema.org命名空间
SCHEMA = Namespace("http://schema.org/")

# 1. 连接Neo4j
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "123456"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 2. 读取OWL本体
g = Graph()
g.parse("book_ontology.owl", format="xml")
EX = Namespace("http://example.org/ontology/")


# 3. 导入类及继承关系到Neo4j
def import_ontology_classes(tx):
    # 提取所有类
    classes = [cls for cls in g.subjects(RDF.type, OWL.Class)]
    for cls in classes:
        cls_name = cls.split("/")[-1]
        # 提取父类
        super_classes = [sc for sc in g.objects(cls, RDFS.subClassOf)]
        super_class_names = [sc.split("/")[-1] for sc in super_classes if str(sc).startswith(str(SCHEMA))]

        # 创建类节点（用Label表示类，Neo4j的Label天然支持继承逻辑）
        if super_class_names:
            tx.run(f"""
                CREATE (c:OntologyClass {{name: $cls_name}})
                SET c.uri = $cls_uri
                WITH c
                MATCH (sc:OntologyClass {{name: $super_name}})
                CREATE (c)-[:SUB_CLASS_OF]->(sc)
            """, cls_name=cls_name, cls_uri=str(cls), super_name=super_class_names[0])
        else:
            tx.run(f"""
                CREATE (c:OntologyClass {{name: $cls_name, uri: $cls_uri}})
            """, cls_name=cls_name, cls_uri=str(cls))


# 4. 导入属性约束到Neo4j
def import_ontology_properties(tx):
    # 提取函数型属性
    func_props = [prop for prop in g.subjects(RDF.type, OWL.FunctionalProperty)]
    for prop in func_props:
        prop_name = prop.split("/")[-1]
        # 提取域和范围
        domain = [d for d in g.objects(prop, RDFS.domain)][0].split("/")[-1]
        range_ = [r for r in g.objects(prop, RDFS.range)][0].split("/")[-1]

        tx.run(f"""
            CREATE (p:OntologyProperty {{name: $prop_name, type: "FunctionalProperty"}})
            SET p.uri = $prop_uri
            WITH p
            MATCH (d:OntologyClass {{name: $domain}}), (r:OntologyClass {{name: $range}})
            CREATE (p)-[:DOMAIN]->(d)
            CREATE (p)-[:RANGE]->(r)
        """, prop_name=prop_name, prop_uri=str(prop), domain=domain, range=range_)


# 5. 执行导入
with driver.session() as session:
    session.execute_write(import_ontology_classes)
    session.execute_write(import_ontology_properties)

# 6. 验证本体导入结果
with driver.session() as session:
    result = session.run("""
        MATCH (c:OntologyClass)-[:SUB_CLASS_OF]->(sc:OntologyClass)
        RETURN c.name AS sub_class, sc.name AS super_class
    """)
    print("\n=== Neo4j本体类继承关系 ===")
    for record in result:
        print(f"{record['sub_class']} → {record['super_class']}")

    result = session.run("""
        MATCH (p:OntologyProperty)-[:DOMAIN]->(d), (p)-[:RANGE]->(r)
        RETURN p.name AS prop, d.name AS domain, r.name AS range, p.type AS type
    """)
    print("\n=== Neo4j本体属性约束 ===")
    for record in result:
        print(f"属性：{record['prop']}，域：{record['domain']}，范围：{record['range']}，类型：{record['type']}")

driver.close()
