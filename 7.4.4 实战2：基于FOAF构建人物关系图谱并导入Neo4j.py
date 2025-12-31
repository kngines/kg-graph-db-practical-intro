from neo4j import GraphDatabase
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import FOAF, XSD, RDF  # 添加RDF导入

# 1. 连接Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "123456"))

# 2. 构建FOAF本体RDF
g = Graph()
PERSON = Namespace("http://example.org/people/")

# 人物1：张三
g.add((PERSON["2001"], RDF.type, FOAF.Person))
g.add((PERSON["2001"], FOAF.name, Literal("张三", datatype=XSD.string)))
g.add((PERSON["2001"], FOAF.mbox, Literal("zhangsan@example.com", datatype=XSD.string)))  # 修正：使用FOAF.mbox
g.add((PERSON["2001"], FOAF.knows, PERSON["2002"]))  # 张三认识李四

# 人物2：李四
g.add((PERSON["2002"], RDF.type, FOAF.Person))
g.add((PERSON["2002"], FOAF.name, Literal("李四", datatype=XSD.string)))
g.add((PERSON["2002"], FOAF.interest, Literal("知识图谱", datatype=XSD.string)))

# 3. FOAF RDF转Neo4j属性图
def foaf_to_neo4j(tx, subj, pred, obj):
    subj_id = subj.split("/")[-1]

    # 清理属性名称，确保符合Neo4j命名规范
    def clean_prop_name(uri):
        # 提取最后部分
        prop_name = uri.split("/")[-1].split("#")[-1]
        # 移除特殊字符，只保留字母、数字和下划线
        import re
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', prop_name)
        # 如果以数字开头，添加前缀
        if cleaned and cleaned[0].isdigit():
            cleaned = f"prop_{cleaned}"
        return cleaned or "property"  # 默认属性名

    pred_name = clean_prop_name(str(pred))

    # 主体节点
    tx.run(f"""
        MERGE (n:Person {{id: $subj_id}})
        SET n.uri = $subj_uri
    """, subj_id=subj_id, subj_uri=str(subj))

    # 客体处理
    if isinstance(obj, Namespace):
        obj_id = obj.split("/")[-1]
        tx.run(f"""
            MERGE (m:Person {{id: $obj_id}})
            SET m.uri = $obj_uri
        """, obj_id=obj_id, obj_uri=str(obj))
        tx.run(f"""
            MATCH (n:Person {{id: $subj_id}}), (m:Person {{id: $obj_id}})
            MERGE (n)-[r:{pred_name}]->(m)
        """, subj_id=subj_id, obj_id=obj_id, pred_name=pred_name)
    else:
        tx.run(f"""
            MATCH (n:Person {{id: $subj_id}})
            SET n.{pred_name} = $obj_value
        """, subj_id=subj_id, pred_name=pred_name, obj_value=str(obj))

# 4. 导入Neo4j
with driver.session() as session:
    for s, p, o in g:
        session.execute_write(foaf_to_neo4j, s, p, o)

# 5. 验证结果
with driver.session() as session:
    result = session.run("""
        MATCH (p1:Person)-[r:knows]->(p2:Person)
        RETURN p1.name AS person1, p2.name AS person2, p1.mbox AS person1_email, p2.interest AS person2_interest
    """)
    print("\n=== FOAF本体导入Neo4j结果 ===")
    for record in result:
        print(f"{record['person1']} 认识 {record['person2']}")
        print(f"{record['person1']} 的邮箱：{record['person1_email']}")
        print(f"{record['person2']} 的兴趣：{record['person2_interest']}")


driver.close()
