from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD

# 1. 初始化RDF图
g = Graph()

# 2. 定义命名空间（模式层基础，避免URI冲突）
# 自定义命名空间：http://example.org/ KG/
KG = Namespace("http://example.org/KG/")
g.bind("kg", KG)  # 绑定命名空间前缀

# 3. 定义模式层（通过RDFS定义类、属性、关系类型）
## 3.1 定义类（Concept/Class）
Person = KG.Person
Company = KG.Company
Movie = KG.Movie
g.add((Person, RDF.type, RDFS.Class))
g.add((Company, RDF.type, RDFS.Class))
g.add((Movie, RDF.type, RDFS.Class))

## 3.2 定义数据属性（描述实体的基础属性）
name = KG.name
age = KG.age
industry = KG.industry
release_year = KG.release_year
# 定义属性的定义域（对应类）和值域（数据类型/类）
g.add((name, RDFS.domain, Person))  # name属性的定义域是Person类
g.add((name, RDFS.range, XSD.string))  # name属性的值域是字符串类型
g.add((age, RDFS.domain, Person))
g.add((age, RDFS.range, XSD.integer))  # age属性的值域是整数类型
g.add((industry, RDFS.domain, Company))
g.add((industry, RDFS.range, XSD.string))
g.add((release_year, RDFS.domain, Movie))
g.add((release_year, RDFS.range, XSD.integer))

## 3.3 定义对象属性（关系类型，关联两个实体）
worksAt = KG.worksAt
created = KG.created
produced = KG.produced
g.add((worksAt, RDF.type, RDF.Property))
g.add((worksAt, RDFS.domain, Person))  # worksAt的定义域是Person
g.add((worksAt, RDFS.range, Company))  # worksAt的值域是Company
g.add((created, RDFS.domain, Person))
g.add((created, RDFS.range, Movie))
g.add((produced, RDFS.domain, Company))
g.add((produced, RDFS.range, Movie))

# 4. 填充数据层（创建RDF三元组，实例化实体、关系与属性值）
## 4.1 定义实体URI（唯一标识）
zhangsan = KG.ZhangSan
liucixin = KG.LiuCixin
alibaba = KG.Alibaba
wandering_earth = KG.WanderingEarth

## 4.2 添加实体实例（声明实体所属的类）
g.add((zhangsan, RDF.type, Person))
g.add((liucixin, RDF.type, Person))
g.add((alibaba, RDF.type, Company))
g.add((wandering_earth, RDF.type, Movie))

## 4.3 添加数据属性值（实体-属性-属性值）
g.add((zhangsan, name, Literal("张三", datatype=XSD.string)))
g.add((zhangsan, age, Literal(30, datatype=XSD.integer)))
g.add((liucixin, name, Literal("刘慈欣", datatype=XSD.string)))
g.add((liucixin, age, Literal(59, datatype=XSD.integer)))
g.add((alibaba, name, Literal("阿里巴巴集团", datatype=XSD.string)))
g.add((alibaba, industry, Literal("互联网", datatype=XSD.string)))
g.add((wandering_earth, name, Literal("《流浪地球》", datatype=XSD.string)))
g.add((wandering_earth, release_year, Literal(2019, datatype=XSD.integer)))

## 4.4 添加关系实例（实体-关系-实体）
g.add((zhangsan, worksAt, alibaba))
g.add((liucixin, created, wandering_earth))
g.add((alibaba, produced, wandering_earth))

# 5. 序列化输出（保存为RDF标准格式，支持TTL/XML/N3等）
g.serialize(destination="kg_schema_data.ttl", format="turtle")
print("RDF知识图谱（模式层+数据层）已保存为kg_schema_data.ttl")

# 6. 查询验证
print("\n=== 查询所有Person类的实体及其姓名 ===")
q = """
PREFIX kg: <http://example.org/KG/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?person ?name
WHERE {
  ?person rdf:type kg:Person .
  ?person kg:name ?name .
}
"""
for row in g.query(q):
    print(f"实体URI: {row.person}, 姓名: {row.name}")

print("\n=== 查询《流浪地球》的创作者 ===")
q2 = """
PREFIX kg: <http://example.org/KG/>
SELECT ?creator ?creator_name
WHERE {
  ?creator kg:created kg:WanderingEarth .
  ?creator kg:name ?creator_name .
}
"""
for row in g.query(q2):
    print(f"创作者URI: {row.creator}, 创作者姓名: {row.creator_name}")