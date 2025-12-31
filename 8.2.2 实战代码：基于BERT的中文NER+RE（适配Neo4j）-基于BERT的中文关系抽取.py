import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 加载中文关系抽取模型（示例：自定义关系类型）
RE_MODEL_NAME = "./models/bert-base-chinese"
re_tokenizer = AutoTokenizer.from_pretrained(RE_MODEL_NAME)
# 定义关系类型（可根据业务扩展）
REL_LABELS = ["创始人", "位于", "属于", "无关系"]
re_model = AutoModelForSequenceClassification.from_pretrained(
    RE_MODEL_NAME, num_labels=len(REL_LABELS)
)


def extract_relation(text, entity1, entity2):
    """抽取两个实体间的关系"""
    # 构造输入：[CLS] 实体1 [SEP] 实体2 [SEP] 上下文 [SEP]
    input_text = f"{entity1}[SEP]{entity2}[SEP]{text}"
    inputs = re_tokenizer(
        input_text, return_tensors="pt", padding=True, truncation=True, max_length=128
    )

    # 模型推理（实际需用标注数据微调模型，此处为框架示例）
    with torch.no_grad():
        outputs = re_model(**inputs)
    logits = outputs.logits
    pred_idx = torch.argmax(logits, dim=1).item()
    return REL_LABELS[pred_idx]


# 定义测试文本
text = "马云于1999年创立阿里巴巴，公司总部位于杭州余杭区。"

# 测试RE
entity_pairs = [("马云", "阿里巴巴"), ("阿里巴巴", "杭州余杭区")]
print("\n=== 中文RE结果 ===")
for e1, e2 in entity_pairs:
    rel = extract_relation(text, e1, e2)
    print(f"实体对：({e1}, {e2})，关系：{rel}")
# 注：未微调的模型预测结果可能不准确，需使用标注数据集（如DuIE）微调
