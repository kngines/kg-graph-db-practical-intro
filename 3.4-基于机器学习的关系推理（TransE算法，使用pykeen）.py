import numpy as np
from pykeen import datasets, models, evaluation
from pykeen.triples import TriplesFactory
from pykeen.pipeline import pipeline  # 使用pipeline替代手动训练

# 步骤1：构建小型知识图谱数据集（使用上述三元组）
triples = [
    ("张三", "毕业于", "北京大学"),
    ("张三", "就职于", "阿里巴巴"),
    ("张三", "大学同学", "李四"),
    ("李四", "研究方向", "人工智能"),
    ("张三", "校友", "北京大学")
]

# 将三元组列表转换为 numpy 数组
triples_array = np.array(triples)
tf = TriplesFactory.from_labeled_triples(triples_array)

# 直接使用整个数据集进行训练，不进行分割
training_factory = tf
testing_factory = tf  # 使用相同的数据集作为测试集

# 步骤2-3：使用pipeline进行模型训练
result = pipeline(
    model='TransE',
    training=training_factory,
    testing=testing_factory,
    model_kwargs=dict(embedding_dim=50),
    epochs=100,
    random_seed=42,
    training_kwargs=dict(
        batch_size=8,
        use_tqdm=True
    )
)

# 获取训练好的模型
model = result.model

# 步骤4：模型评估（知识补全任务）
evaluator = evaluation.RankBasedEvaluator()
metrics = evaluator.evaluate(
    model=model,
    mapped_triples=testing_factory.mapped_triples,
    batch_size=8
)
print("\nTransE模型评估指标（MRR：平均倒数排名）：", metrics.get_metric("mean_reciprocal_rank"))

# 步骤5：推理隐含关系（预测"李四"与"北京大学"的关系）
from pykeen.predict import predict_target

predictions = predict_target(
    model=model,
    head="李四",
    relation=None,
    tail="北京大学",
    triples_factory=tf
)

# 查看预测结果的结构，获取前3个预测结果
if hasattr(predictions, 'scores') and hasattr(predictions, 'relations'):
    # 如果predictions有scores和relations属性
    top_indices = predictions.scores.argsort(descending=True)[:3]
    print("\n预测李四与北京大学的关系（Top3）：")
    for idx in top_indices:
        relation_label = predictions.relations[idx]
        score = predictions.scores[idx]
        print(f"关系：{relation_label}, 得分：{score:.4f}")
elif hasattr(predictions, '__iter__'):
    # 如果predictions是可迭代的
    top_predictions = []
    for i, pred in enumerate(predictions):
        if i >= 3:
            break
        top_predictions.append(pred)

    print("\n预测李四与北京大学的关系（Top3）：")
    for pred in top_predictions:
        print(f"关系：{pred.relation_label}, 得分：{pred.score:.4f}")
else:
    # 直接处理整个predictions对象
    print("\n预测李四与北京大学的关系：")
    print(predictions)

# 从TargetPredictions对象中提取DataFrame
df = predictions.df
# 按得分排序并获取前3个
top_3 = df.nlargest(3, 'score')

print("\n预测李四与北京大学的关系（Top3）：")
for _, row in top_3.iterrows():
    print(f"关系：{row['relation_label']}, 得分：{row['score']:.4f}")


# relation_id：关系的内部ID编号
# score：预测得分（负数，值越大表示预测越可能）
# relation_label：关系标签名称
# 第一名："毕业于"（得分：-9.123250）- 最可能的关系
# 第二名："研究方向"（得分：-10.063671）
# 第三名："校友"（得分：-10.582248）