from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD

# 手动定义Schema.org命名空间
SCHEMA = Namespace("http://schema.org/")

# 1. 定义命名空间
EX = Namespace("http://example.org/ontology/")

# 2. 初始化本体图
g = Graph()

# 3. 定义类及继承关系
g.add((EX.EBook, RDF.type, OWL.Class))
g.add((EX.EBook, RDFS.subClassOf, SCHEMA.Book))  # 电子书是图书的子类
g.add((EX.PrintBook, RDF.type, OWL.Class))
g.add((EX.PrintBook, RDFS.subClassOf, SCHEMA.Book))  # 纸质书是图书的子类

# 4. 定义类约束（不相交）
g.add((EX.EBook, OWL.disjointWith, EX.PrintBook))  # 电子书和纸质书不相交

# 5. 定义对象属性及约束
# 主作者属性（函数型：一个图书仅一个主作者）
g.add((EX.mainAuthor, RDF.type, OWL.ObjectProperty))
g.add((EX.mainAuthor, RDFS.domain, SCHEMA.Book))
g.add((EX.mainAuthor, RDFS.range, SCHEMA.Person))
g.add((EX.mainAuthor, RDF.type, OWL.FunctionalProperty))  # 修正：FunctionalProperty的正确用法

# 逆属性：写作（wroteBook是mainAuthor的逆属性）
g.add((EX.wroteBook, RDF.type, OWL.ObjectProperty))
g.add((EX.wroteBook, OWL.inverseOf, EX.mainAuthor))

# 6. 定义数据属性及约束
g.add((EX.downloadCount, RDF.type, OWL.DatatypeProperty))
g.add((EX.downloadCount, RDFS.domain, EX.EBook))
g.add((EX.downloadCount, RDFS.range, XSD.int))  # 下载量是整数

# 7. 定义个体等价
g.add((EX.ZhangSan, RDF.type, SCHEMA.Person))
g.add((EX.ZhangSan, OWL.sameAs, URIRef("http://example.org/people/2001")))  # 等价于之前的张三

# 8. 添加实例数据
g.add((EX.Book1001, RDF.type, EX.EBook))
g.add((EX.Book1001, SCHEMA.name, Literal("Neo4j图数据库与知识图谱", datatype=XSD.string)))
g.add((EX.Book1001, EX.mainAuthor, EX.ZhangSan))
g.add((EX.Book1001, EX.downloadCount, Literal(10000, datatype=XSD.int)))

# 9. 序列化本体为OWL/XML格式（兼容Protégé）
g.serialize(destination="book_ontology.owl", format="xml")
print("本体已保存为 book_ontology.owl")

# 10. SPARQL推理查询：获取所有电子书的主作者
query = """
PREFIX ex: <http://example.org/ontology/>
PREFIX schema: <http://schema.org/>

SELECT ?bookName ?authorUri
WHERE {
    ?book a ex:EBook ;
          schema:name ?bookName ;
          ex:mainAuthor ?author .
    ?author owl:sameAs ?authorUri .
}
"""
print("\n=== 本体推理查询结果 ===")
for row in g.query(query):
    print(f"电子书：{row.bookName}，主作者URI：{row.authorUri}")
