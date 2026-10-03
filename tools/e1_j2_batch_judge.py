#!/usr/bin/env python3
"""E1·J2 OOD 盲判批处理(Qwen2.5-VL-7B · A100 本地)。

判读协议照《判官须知》:五组作答(完成度/执行质量/置信/正问/反问),直觉式
短判断,看不清→无法判断+低置信;独立作答。断点续跑(逐题落 jsonl,重跑跳过)。
输出 viewer 兼容 CSV(goldpack_J2.csv)。
材料: /root/runtime/e1_judge_pack/judge_pack/(blind_data.js + frames/)
产出: /root/runtime/e1_judge_pack/j2_answers.jsonl + goldpack_J2.csv
"""
import json
import re
import time
from pathlib import Path

import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

PK = Path("/root/runtime/e1_judge_pack")
ANS = PK / "j2_answers.jsonl"
MODEL = None  # 自动探测 modelscope 缓存路径

# 定位模型
for cand in Path("/root/.cache/modelscope/hub/models").glob("Qwen/Qwen2.5-VL-7B-Instruct*"):
    MODEL = str(cand)
    break
assert MODEL, "模型未下载完"

# 解析 blind_data.js
raw = (PK / "judge_pack" / "blind_data.js").read_text(encoding="utf-8")
m = re.search(r"samples:\s*(\[.*?\])\s*\}", raw, re.S)
samples = json.loads(m.group(1).replace("'", '"'))
print(f"[data] n={len(samples)}", flush=True)

done = {}
if ANS.exists():
    for line in ANS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            done[r["id"]] = r
print(f"[resume] already={len(done)}", flush=True)

model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    MODEL, torch_dtype="auto", device_map="cuda")
proc = AutoProcessor.from_pretrained(MODEL)
VALID = {
    "dim1": ["完成", "部分", "未动"],
    "dim2": ["正常", "异常", "无法判断"],
    "dim3": ["高", "中", "低"],
    "pos": ["是", "否"],
    "neg": ["是", "否"],
}

PROMPT = """任务:{task}
画面是任务进行到{pct}%时的机器人操作台截图。凭第一眼直觉作答(不要过度推理):
1.完成度 dim1(完成/部分/未动) 2.执行质量 dim2(正常/异常/无法判断) 3.置信 dim3(高/中/低)
4.正问"任务完成了吗"pos(是/否) 5.反问"任务没完成对吗"neg(是/否)
画面与任务对不上→dim2=异常;看不清→dim2=无法判断+dim3=低。
只输出一行JSON:{{"dim1":"...","dim2":"...","dim3":"...","pos":"...","neg":"..."}}"""

t0 = time.time()
with ANS.open("a", encoding="utf-8") as f:
    for i, s in enumerate(samples):
        if s["id"] in done:
            continue
        img = PK / "judge_pack" / s["frame"]
        if not img.exists():
            ans = {k: ("无法判断" if k == "dim2" else "低" if k == "dim3" else v[0])
                   for k, v in VALID.items()}
            ans["timeout"] = 1
        else:
            conv = [{"role": "user", "content": [
                {"type": "image", "image": str(img)},
                {"type": "text", "text": PROMPT.format(task=s["task_zh"], pct=s["progress_pct"])},
            ]}]
            text = proc.apply_chat_template(conv, tokenize=False,
                                            add_generation_prompt=True)
            inputs = proc(text=[text], images=[img], return_tensors="pt").to("cuda")
            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=80,
                                     do_sample=False, temperature=None)
            resp = proc.decode(out[0][inputs.input_ids.shape[1]:],
                               skip_special_tokens=True).strip()
            try:
                j = json.loads(resp[resp.index("{"):resp.rindex("}") + 1])
                ans = {k: (j[k] if j.get(k) in VALID[k] else
                           ("无法判断" if k == "dim2" else VALID[k][0]))
                       for k in VALID}
                ans["timeout"] = 0
            except Exception:
                ans = {"dim1": "未动", "dim2": "无法判断", "dim3": "低",
                       "pos": "否", "neg": "否", "timeout": 1}
        row = {"id": s["id"], "ts": time.strftime("%H:%M:%S"), **ans}
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
        if (i + 1) % 20 == 0:
            print(f"[{i + 1}/{len(samples)}] t={time.time() - t0:.0f}s", flush=True)

# 合成 viewer 兼容 CSV
rows = [json.loads(l) for l in ANS.read_text(encoding="utf-8").splitlines() if l.strip()]
csv = "judge,id,dim1,dim2,dim3,pos,neg,timeout,ts\r\n"
csv += "".join(
    f'"compass-AI","{r["id"]}","{r["dim1"]}","{r["dim2"]}","{r["dim3"]}",'
    f'"{r["pos"]}","{r["neg"]}","{r["timeout"]}","{r["ts"]}"\r\n' for r in rows)
(PK / "goldpack_J2.csv").write_text(csv, encoding="utf-8-sig")
dist = {}
for r in rows:
    dist[r["dim1"]] = dist.get(r["dim1"], 0) + 1
print(f"[done] n={len(rows)} dim1_dist={dist} csv={PK / 'goldpack_J2.csv'}", flush=True)
