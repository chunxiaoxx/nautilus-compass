"""turbo ImportError 深挖:直接 import qwen3_5 模型模块,拿未截断的真实错误。"""
import traceback

print("== 1) 直接 import 模型模块 ==")
try:
    from transformers.models.qwen3_5 import modeling_qwen3_5 as m
    print("import ok:", m.__file__)
except Exception:
    traceback.print_exc()

print("\n== 2) AutoModelForCausalLM 完整链 ==")
try:
    from transformers import AutoModelForCausalLM
    model = AutoModelForCausalLM.from_pretrained(
        "/root/vdd2/models/Qwen3.8-14B-Turbo", dtype="bfloat16", device_map="cpu")
    print("loaded ok:", model.config.model_type)
except Exception:
    traceback.print_exc()
