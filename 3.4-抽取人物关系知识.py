import spacy
import jieba

# 初始化中文NLP模型
nlp = spacy.load("zh_core_web_sm")

# 原始非结构化文本
raw_text = "张三，男，30岁，毕业于北京大学计算机系，现就职于阿里巴巴，担任高级工程师，与李四是大学同学，李四的研究方向是人工智能。"

# 步骤1：文本预处理（分词、去停用词）
stop_words = {"的", "于", "现", "担任", "是", "与"}
seg_words = [word for word in jieba.lcut(raw_text) if word.strip() and word not in stop_words]
processed_text = " ".join(seg_words)
print("预处理后的文本：", processed_text)

# 步骤2：实体抽取（识别人物、机构、专业等实体）
doc = nlp(processed_text)
entities = []
for ent in doc.ents:
    # 筛选核心实体类型（人物、组织、专业）
    if ent.label_ in ["PERSON", "ORG", "WORK_OF_ART"]:
        entities.append({"实体名称": ent.text, "实体类型": ent.label_})
print("\n抽取的实体：")
for ent in entities:
    print(ent)

# 步骤3：关系抽取（基于规则匹配人物关系）
relations = []
# 定义关系匹配规则
relation_patterns = [
    ("张三", "李四", "大学同学"),
    ("张三", "北京大学", "毕业于"),
    ("张三", "阿里巴巴", "就职于"),
    ("李四", "人工智能", "研究方向")
]

# 匹配文本中的关系
for subj, obj, rel in relation_patterns:
    if subj in raw_text and obj in raw_text:
        relations.append({"主体": subj, "关系": rel, "客体": obj})
print("\n抽取的关系：")
for rel in relations:
    print(rel)

# 步骤4：整理为知识图谱三元组格式（主体-关系-客体）
kg_triples = [(rel["主体"], rel["关系"], rel["客体"]) for rel in relations]
print("\n知识图谱三元组：")
for triple in kg_triples:
    print(f"{triple[0]} -> {triple[1]} -> {triple[2]}")