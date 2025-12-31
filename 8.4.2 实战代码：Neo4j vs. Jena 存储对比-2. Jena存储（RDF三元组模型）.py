# 环境准备：下载Apache Jena，配置JAVA环境
# pip install rdflib（Python操作RDF的库）
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS

# 1. 定义命名空间
ns = Namespace("http://example.org/knowledgegraph/")

# 2. 构建RDF图
g = Graph()

# 3. 添加三元组（主语-谓语-宾语）
# 实体：马云（PER）、阿里巴巴（ORG）
g.add((ns.马云, RDF.type, ns.PER))
g.add((ns.阿里巴巴, RDF.type, ns.ORG))
g.add((ns.杭州, RDF.type, ns.LOC))

# 关系：马云-创始人->阿里巴巴
g.add((ns.马云, ns.创始人, ns.阿里巴巴))
g.add((ns.阿里巴巴, ns.位于, ns.杭州))
g.add((ns.杭州, ns.属于, ns.浙江省))

# 4. 保存为RDF文件（可导入Jena Fuseki）
g.serialize(destination="kg_rdf.ttl", format="turtle")
print("RDF三元组保存完成，文件：kg_rdf.ttl")

# 5. SPARQL查询（模拟Jena查询）
query = """
    PREFIX ns: <http://example.org/knowledgegraph/>
    SELECT ?s ?p ?o WHERE {
        ?s ns:创始人 ?o .
    }
"""
results = g.query(query)
print("\n=== SPARQL查询结果 ===")
for row in results:
    print(f"{row.s} {row.p} {row.o}")