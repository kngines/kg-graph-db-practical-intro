from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD

# 1. 定义命名空间（简化URI书写）
EX = Namespace("http://example.org/")  # 自定义命名空间
BOOK = Namespace("http://example.org/books/")
PERSON = Namespace("http://example.org/people/")

# 手动定义Schema.org命名空间
SCHEMA = Namespace("http://schema.org/")

# 2. 初始化RDF图并添加三元组
g = Graph()

# 声明资源类型（Schema.org标准类）
g.add((BOOK["1001"], RDF.type, SCHEMA.Book))  # 图书1001是Schema.org的Book类实例
g.add((PERSON["2001"], RDF.type, SCHEMA.Person))  # 人物2001是Schema.org的Person类实例

# 图书属性（Schema.org标准属性）
g.add((BOOK["1001"], SCHEMA.name, Literal("Neo4j图数据库与知识图谱", datatype=XSD.string)))
g.add((BOOK["1001"], SCHEMA.publicationYear, Literal(2025, datatype=XSD.int)))
g.add((BOOK["1001"], SCHEMA.author, PERSON["2001"]))  # 图书-作者关系

# 人物属性
g.add((PERSON["2001"], SCHEMA.name, Literal("张三", datatype=XSD.string)))
g.add((PERSON["2001"], SCHEMA.profession, Literal("知识图谱工程师", datatype=XSD.string)))

# 3. 序列化输出（Turtle格式）
print("=== RDF Turtle格式输出 ===")
turtle_data = g.serialize(format="turtle")  # 移除.decode("utf-8")
print(turtle_data)

# 4. SPARQL查询：获取图书及作者信息
print("\n=== SPARQL查询结果 ===")
query = """
PREFIX schema: <http://schema.org/>
PREFIX ex: <http://example.org/>

SELECT ?bookName ?authorName
WHERE {
    ?book a schema:Book ;
          schema:name ?bookName ;
          schema:author ?author .
    ?author a schema:Person ;
            schema:name ?authorName .
}
"""
for row in g.query(query):
    print(f"图书名称：{row.bookName}，作者：{row.authorName}")

# 5. 保存RDF文件
g.serialize(destination="book_author.rdf", format="turtle")
print("\nRDF文件已保存为 book_author.rdf")
