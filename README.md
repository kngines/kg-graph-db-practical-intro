# 知识图谱与Neo4j实战项目

## 项目概述

本项目是一个完整的知识图谱构建与应用实战项目，涵盖了从RDF/OWL本体构建、中文NER/RE、多源数据融合到Neo4j图数据库存储与查询的全流程。

## 项目结构

### 1. RDF/OWL本体构建模块
- **[7.1.2 实战1：用rdflib创建RDF三元组.py](..\7.1.2%20实战1：用rdflib创建RDF三元组.py)** - 使用rdflib创建RDF三元组
- **[7.1.3 实战2：将RDF三元组导入Neo4j.py](..\7.1.3%20实战2：将RDF三元组导入Neo4j.py)** - RDF三元组导入Neo4j
- **[7.2.3 实战1：用rdflib定义RDFS-OWL本体.py](..\7.2.3%20实战1：用rdflib定义RDFS-OWL本体.py)** - RDFS-OWL本体定义
- **[7.2.4 实战2：将OWL本体导入Neo4j.py](..\7.2.4%20实战2：将OWL本体导入Neo4j.py)** - OWL本体导入Neo4j
- **[7.4.3 实战1：基于Schema.org构建图书知识图谱并导入Neo4j.py](..\7.4.3%20实战1：基于Schema.org构建图书知识图谱并导入Neo4j.py)** - Schema.org标准图谱构建
- **[7.4.4 实战2：基于FOAF构建人物关系图谱并导入Neo4j.py](..\7.4.4%20实战2：基于FOAF构建人物关系图谱并导入Neo4j.py)** - FOAF人物关系图谱
- **[7.5.3 实战1：RDF→Neo4j属性图（批量转换工具）.py](..\7.5.3%20实战1：RDF→Neo4j属性图（批量转换工具）.py)** - RDF批量转换工具

### 2. 中文NER/RE模块
- **[8.2.2 实战代码：基于BERT的中文NER+RE（适配Neo4j）-基于HuggingFace的中文NER实现.py](..\8.2.2%20实战代码：基于BERT的中文NER+RE（适配Neo4j）-基于HuggingFace的中文NER实现.py)** - 中文实体识别
- **[8.2.2 实战代码：基于BERT的中文NER+RE（适配Neo4j）-基于HuggingFace的中文关系抽取.py](..\8.2.2%20实战代码：基于BERT的中文NER+RE（适配Neo4j）-基于BERT的中文关系抽取.py)** - 中文关系抽取
- **[8.2.2 实战代码：基于BERT的中文NER+RE（适配Neo4j）-抽取结果导入Neo4j.py](..\8.2.2%20实战代码：基于BERT的中文NER+RE（适配Neo4j）-抽取结果导入Neo4j.py)** - 结果导入Neo4j

### 3. 数据融合与存储模块
- **[8.1.1-从MySQL导入结构化数据到Neo4j.py](..\8.1.1-从MySQL导入结构化数据到Neo4j.py)** - MySQL数据导入Neo4j
- **[8.3.2 实战代码：Neo4j实体对齐与消歧.py](..\8.3.2%20实战代码：Neo4j实体对齐与消歧.py)** - 实体对齐与消歧
- **[8.5.2 实战代码：端到端Pipeline.py](..\8.5.2%20实战代码：端到端Pipeline.py)** - 端到端数据处理管道

### 4. 图算法与分析模块
- **[6.5.2 实战：Python（py2neo+NetworkX）实现相似度与链接预测.py](..\6.5.2%20实战：Python（py2neo+NetworkX）实现相似度与链接预测.py)** - 相似度与链接预测
- **[6.6.2 性能优化最佳实践-2. 增量计算（避免全量重算，提升效率）.py](..\6.6.2%20性能优化最佳实践-2.%20增量计算（避免全量重算，提升效率）.py)** - 增量计算优化
- **[6.6.2 性能优化最佳实践-3. 批量执行与任务调度.py](..\6.6.2%20性能优化最佳实践-3.%20批量执行与任务调度.py)** - 批量执行与调度
- **[6.6.4 生产落地案例：用户分群与个性化推荐.py](..\6.6.4%20生产落地案例：用户分群与个性化推荐.py)** - 用户分群与推荐

## 技术栈

### 主要依赖
- **图数据库**：Neo4j
- **Python库**：py2neo, NetworkX, rdflib
- **NLP**：transformers, torch
- **数据处理**：pandas, numpy
- **数据库**：mysql-connector-python, SQLAlchemy

### 本体标准
- **RDF**：Resource Description Framework
- **OWL**：Web Ontology Language
- **Schema.org**：结构化数据标准
- **FOAF**：Friend of a Friend

## 项目特点

1. **完整的知识图谱构建流程**：从数据源到最终应用的端到端实现
2. **多源数据融合**：支持结构化、半结构化、非结构化数据处理
3. **中文NLP支持**：基于BERT的中文实体识别与关系抽取
4. **性能优化**：包含增量计算、批量处理等优化策略
5. **实际应用场景**：用户分群、个性化推荐等生产级应用

## 使用说明

### 环境准备
```bash
pip install neo4j py2neo networkx rdflib transformers torch pandas mysql-connector-python sqlalchemy
```


### 运行顺序
1. 首先运行RDF/OWL本体构建相关脚本
2. 然后执行数据导入与融合脚本
3. 最后运行图算法分析与应用脚本

## 注意事项

1. **Neo4j连接**：确保Neo4j数据库正常运行并配置正确的连接参数
2. **模型下载**：中文NER/RE脚本需要从HuggingFace下载预训练模型
3. **数据准备**：部分脚本依赖MySQL数据库中的示例数据
4. **网络访问**：RDF相关脚本可能需要访问Schema.org等外部本体

## 应用场景

- **企业知识图谱构建**
- **用户关系分析**
- **个性化推荐系统**
- **实体对齐与消歧**
- **图数据挖掘与分析**