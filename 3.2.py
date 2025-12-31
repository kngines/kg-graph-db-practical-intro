# 导入rdflib核心模块
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, FOAF  # FOAF是通用的人物/文档描述本体

# 1. 定义命名空间（符合链接数据URI唯一标识原则）
# 自定义人物命名空间，使用HTTP URI作为实体唯一标识
PERSON = Namespace("http://example.org/persons/")
# 自定义书籍命名空间，对应《图数据库与知识图谱：从入门到实践》相关实体
BOOK = Namespace("http://example.org/books/")

# 2. 创建RDF图（存储链接数据三元组的容器）
rdf_graph = Graph()

# 3. 添加RDF三元组（符合链接数据的RDF描述原则和跨实体链接原则）
# 三元组1：张三是一个自然人（主体：张三，谓词：类型，客体：Person）
zhangsan_uri = URIRef(PERSON["ZhangSan"])
rdf_graph.add((zhangsan_uri, RDF.type, FOAF.Person))

# 三元组2：张三的中文姓名是“张三”
rdf_graph.add((zhangsan_uri, FOAF.name, Literal("张三", lang="zh")))

# 三元组3：张三的职业是“软件工程师”
rdf_graph.add((zhangsan_uri, FOAF.title, Literal("软件工程师")))

# 三元组4：《图数据库与知识图谱》是一份文档（主体：书籍，谓词：类型，客体：Document）
graph_book_uri = URIRef(BOOK["GraphDBBook"])
rdf_graph.add((graph_book_uri, RDF.type, FOAF.Document))

# 三元组5：书籍的标题是《图数据库与知识图谱：从入门到实践》
rdf_graph.add((graph_book_uri, FOAF.title, Literal("图数据库与知识图谱：从入门到实践")))

# 三元组6：张三撰写了该书籍（体现链接数据的跨实体互联原则）
rdf_graph.add((zhangsan_uri, FOAF.made, graph_book_uri))

# 4. 序列化输出RDF数据（Turtle格式，更易读）
print("===== 链接数据（RDF三元组）- Turtle格式 =====")
# print(rdf_graph.serialize(format="turtle").decode("utf-8"))
print(rdf_graph.serialize(format="turtle"))


# 5. SPARQL查询（检索张三撰写的书籍信息，对应语义网查询能力）
sparql_query = """
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX person: <http://example.org/persons/>
    PREFIX book: <http://example.org/books/>

    SELECT ?author_name ?book_title
    WHERE {
        # 匹配作者信息
        ?author a foaf:Person ;
                foaf:name ?author_name ;
                foaf:made ?book .
        # 匹配书籍信息
        ?book a foaf:Document ;
              foaf:title ?book_title .
        # 过滤指定作者（张三）
        FILTER (?author = person:ZhangSan)
    }
"""

# 执行SPARQL查询并输出结果
print("===== SPARQL查询结果（张三撰写的书籍） =====")
query_results = rdf_graph.query(sparql_query)
for row in query_results:
    print(f"作者姓名：{row.author_name}")
    print(f"书籍名称：{row.book_title}")

# 6. 保存RDF数据到本地文件（为后续转换知识图谱做准备）
rdf_graph.serialize(destination="linked_data_graph.rdf", format="xml")
print("\n===== 链接数据已保存到本地文件：linked_data_graph.rdf =====")