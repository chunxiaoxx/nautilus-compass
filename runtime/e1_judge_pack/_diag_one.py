from pathlib import Path
from PIL import Image as PILImage
import torch, json, re
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration, BitsAndBytesConfig
MODEL = str(sorted(Path("/root/.cache/modelscope/models").glob("Qwen--Qwen2.5-VL-3B-Instruct*/snapshots/*"))[0])
raw = Path("/root/runtime/e1_judge_pack/judge_pack/blind_data.js").read_text(encoding="utf-8")
s0 = json.loads(re.search(r"samples:\s*(\[.*?\])\s*\}", raw, re.S).group(1))[0]
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)
m = Qwen2_5_VLForConditionalGeneration.from_pretrained(MODEL, quantization_config=bnb, device_map="cuda")
proc = AutoProcessor.from_pretrained(MODEL)
PROMPT = open("/root/_diag_prompt.txt", encoding="utf-8").read()
img = Path("/root/runtime/e1_judge_pack/judge_pack") / s0["frame"]
conv = [{"role": "user", "content": [
    {"type": "image", "image": str(img)},
    {"type": "text", "text": PROMPT.format(task=s0["task_zh"], pct=s0["progress_pct"])}]}]
text = proc.apply_chat_template(conv, tokenize=False, add_generation_prompt=True)
print("[TEMPLATE]", repr(text[:200]))
inputs = proc(text=[text], images=[PILImage.open(img).convert("RGB")], return_tensors="pt").to("cuda")
print("[INPUTS] keys ok, ids:", inputs.input_ids.shape)
with torch.no_grad():
    out = m.generate(**inputs, max_new_tokens=80, do_sample=False)
resp = proc.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
print("[RESP]", repr(resp))
