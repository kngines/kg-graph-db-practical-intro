from neo4j import GraphDatabase
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import XSD  # 移除SCHEMA导入

# 手动定义Schema.org命名空间
SCHEMA = Namespace("http://schema.org/")

# 1. 连接Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "123456"))

# 2. 构建Schema.org标准RDF
g = Graph()
BOOK = Namespace("http://example.org/books/")
ORG = Namespace("http://example.org/orgs/")

# 图书信息（Schema.org标准）
g.add((BOOK["1001"], SCHEMA.type, SCHEMA.Book))
g.add((BOOK["1001"], SCHEMA.name, Literal("Neo4j图数据库与知识图谱", datatype=XSD.string)))
g.add((BOOK["1001"], SCHEMA.publisher, ORG["5001"]))
g.add((BOOK["1001"], SCHEMA.datePublished, Literal("2025-01-01", datatype=XSD.date)))

# 出版商信息（Schema.org标准）
g.add((ORG["5001"], SCHEMA.type, SCHEMA.Publisher))
g.add((ORG["5001"], SCHEMA.name, Literal("图灵出版社", datatype=XSD.string)))
g.add((ORG["5001"], SCHEMA.address, Literal("北京市海淀区", datatype=XSD.string)))


# 3. RDF转Neo4j属性图
def schema_to_neo4j(tx, subj, pred, obj):
    subj_id = subj.split("/")[-1]
    pred_name = pred.split("/")[-1]

    # 处理主体节点
    subj_type = [o.split("/")[-1] for o in g.objects(subj, SCHEMA.type)][0]
    tx.run(f"""
        MERGE (n:{subj_type} {{id: $subj_id}})
        SET n.uri = $subj_uri
    """, subj_id=subj_id, subj_uri=str(subj))

    # 处理客体
    if isinstance(obj, Namespace):
        obj_id = obj.split("/")[-1]
        obj_type = [o.split("/")[-1] for o in g.objects(obj, SCHEMA.type)][0]
        tx.run(f"""
            MERGE (m:{obj_type} {{id: $obj_id}})
            SET m.uri = $obj_uri
        """, obj_id=obj_id, obj_uri=str(obj))
        tx.run(f"""
            MATCH (n:{subj_type} {{id: $subj_id}}), (m:{obj_type} {{id: $obj_id}})
            MERGE (n)-[r:{pred_name}]->(m)
        """, subj_id=subj_id, obj_id=obj_id, pred_name=pred_name)
    else:
        tx.run(f"""
            MATCH (n:{subj_type} {{id: $subj_id}})
            SET n.{pred_name} = $obj_value
        """, subj_id=subj_id, pred_name=pred_name, obj_value=str(obj))


# 4. 导入Neo4j
with driver.session() as session:
    for s, p, o in g:
        session.execute_write(schema_to_neo4j, s, p, o)

# 5. 验证结果
with driver.session() as session:
    result = session.run("""
        MATCH (b:Book)-[r:publisher]->(p:Publisher)
        RETURN b.name AS book_name, p.name AS publisher_name, p.address AS publisher_addr
    """)
    print("\n=== Schema.org本体导入Neo4j结果 ===")
    for record in result:
        print(f"图书：{record['book_name']}，出版商：{record['publisher_name']}，地址：{record['publisher_addr']}")

driver.close()
