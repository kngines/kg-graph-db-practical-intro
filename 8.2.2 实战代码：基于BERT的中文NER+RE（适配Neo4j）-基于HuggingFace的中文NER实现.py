from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import os

# 忽略pynvml弃用警告（可选）
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# 在文件开头添加镜像源设置
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 修复后的完整代码段
MODEL_NAME = "ckiplab/bert-base-chinese-ner"
LOCAL_MODEL_PATH = "./models/bert-base-chinese-ner"

# 确保本地模型目录存在
os.makedirs(LOCAL_MODEL_PATH, exist_ok=True)

# 尝试多种加载方式
tokenizer = None
model = None

try:
    # 首先检查本地是否有模型文件
    # 如果本地目录为空或文件不完整，从网络下载
    if not os.path.exists(os.path.join(LOCAL_MODEL_PATH, "config.json")):
        print("本地模型文件不存在或不全，开始从网络下载...")
        # 从网络下载并保存到本地
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)

        # 保存到本地
        tokenizer.save_pretrained(LOCAL_MODEL_PATH)
        model.save_pretrained(LOCAL_MODEL_PATH)
        print(f"模型已下载并保存到本地: {LOCAL_MODEL_PATH}")
    else:
        # 从本地加载
        tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_PATH, local_files_only=True)
        model = AutoModelForTokenClassification.from_pretrained(LOCAL_MODEL_PATH, local_files_only=True)
        print(f"成功从本地加载中文NER模型: {LOCAL_MODEL_PATH}")

except Exception as e:
    print(f"加载模型时出错: {e}")
    try:
        # 备用方案：直接从网络加载（不保存到本地）
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)
        print("成功从网络加载中文NER模型（临时使用）")
    except Exception as e2:
        print(f"网络加载也失败: {e2}")
        print("请检查网络连接或手动下载模型")
        print(
            f"可以运行: from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('{MODEL_NAME}').save_pretrained('{LOCAL_MODEL_PATH}')")
        print(
            f"然后运行: from transformers import AutoModelForTokenClassification; AutoModelForTokenClassification.from_pretrained('{MODEL_NAME}').save_pretrained('{LOCAL_MODEL_PATH}')")

# NER标注映射（B-开头=实体开始，I-开头=实体内部，O=非实体）
label_map = {
    0: "O", 1: "B-PER", 2: "I-PER", 3: "B-ORG", 4: "I-ORG", 5: "B-LOC", 6: "I-LOC"
}


def extract_entities(text):
    """提取文本中的中文实体（人名PER/机构ORG/地名LOC）"""
    global tokenizer, model

    # 检查模型是否已加载
    if tokenizer is None or model is None:
        print("错误：模型未加载，无法执行实体提取")
        return []

    # 编码文本
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    # 模型推理
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
    logits = outputs.logits
    predictions = torch.argmax(logits, dim=2)

    # 解析实体
    tokens = tokenizer.convert_ids_to_tokens(input_ids[0])
    entities = []
    current_entity = None
    current_type = None

    for token, pred in zip(tokens, predictions[0]):
        label = label_map[pred.item()]
        if token in ["[CLS]", "[SEP]"]:
            continue

        # 处理实体开始
        if label.startswith("B-"):
            if current_entity:
                entities.append((current_entity, current_type))
            current_entity = token.replace("##", "")  # 处理分词后的子词
            current_type = label.split("-")[1]
        # 处理实体内部
        elif label.startswith("I-") and current_entity:
            current_entity += token.replace("##", "")
        # 非实体，结束当前实体
        elif label == "O" and current_entity:
            entities.append((current_entity, current_type))
            current_entity = None
            current_type = None

    # 处理最后一个实体
    if current_entity:
        entities.append((current_entity, current_type))

    return entities


# 测试NER
text = "马云于1999年创立阿里巴巴，公司总部位于杭州余杭区。"

# 在模型加载成功后获取正确的标签映射
if tokenizer is not None and model is not None:
    # 尝试从模型配置中获取标签映射
    if hasattr(model.config, 'id2label'):
        label_map = model.config.id2label
    elif hasattr(model.config, 'label2id'):
        # 反转 label2id 映射
        label_map = {v: k for k, v in model.config.label2id.items()}
    else:
        # 使用 ckiplab 模型的默认标签映射
        label_map = {
            0: "B-ORG", 1: "I-ORG", 2: "B-PER", 3: "I-PER",
            4: "B-LOC", 5: "I-LOC", 6: "O"
        }

    print("=== 中文NER结果 ===")
    entities = extract_entities(text)
    for entity, ent_type in entities:
        print(f"实体：{entity}，类型：{ent_type}")