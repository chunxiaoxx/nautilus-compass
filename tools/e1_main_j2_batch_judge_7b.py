#!/usr/bin/env python3
"""E1·J2 主包盲判批处理·7B 升级版(Qwen2.5-VL-7B bf16 · 判官升级程序首跑)。

升级纪律:判据/PROMPT/解析与 3B v4 定版逐字零改动(判据不因模型升级而变——只许更严);
改动仅三处:模型路径(/root/sysmodels 7B)、输出文件名(_7b 后缀防覆盖 3B 断点)、版本注记。

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

from PIL import Image as PILImage

import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

PK = Path("/root/runtime/e1_judge_pack")
ANS = PK / "main_j2_answers_7b.jsonl"
MODEL = "/root/sysmodels/Qwen2.5-VL-7B-Instruct"
from pathlib import Path as _P
assert _P(MODEL).exists(), "7B 模型不在位"

# 解析 blind_data.js
import json as _json
raw_map = _json.loads((PK / "main_judge_taskcard_map_498.json").read_text(encoding="utf-8"))
raw = _json.dumps({"samples": [{"id": c["id"], "task_en": c["task_zh_fixed"], "progress_pct": c["progress_pct"]} for c in raw_map["cards"]]})
m = re.search(r"samples.: (\[.*\])", raw)
samples = json.loads(m.group(1))
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
输出格式(按画面实况选值):{{"dim1":"<完成|部分|未动>","dim2":"<正常|异常|无法判断>","dim3":"<高|中|低>","pos":"<是|否>","neg":"<是|否>"}}
只输出一行JSON,不要任何其他文字"""

t0 = time.time()
with ANS.open("a", encoding="utf-8") as f:
    for i, s in enumerate(samples):
        if s["id"] in done:
            continue
        img = PK / "main_pack" / "frames" / (s["id"] + ".jpg")
        if not img.exists():
            ans = {k: ("无法判断" if k == "dim2" else "低" if k == "dim3" else v[0])
                   for k, v in VALID.items()}
            ans["timeout"] = 1
        else:
            conv = [{"role": "user", "content": [
                {"type": "image", "image": str(img)},
                {"type": "text", "text": PROMPT.format(task=s["task_en"], pct=s["progress_pct"])},
            ]}]
            text = proc.apply_chat_template(conv, tokenize=False,
                                            add_generation_prompt=True)
            inputs = proc(text=[text], images=[PILImage.open(img).convert("RGB")],
                          return_tensors="pt").to("cuda")
            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=80,
                                     do_sample=False, temperature=None)
            resp = proc.decode(out[0][inputs.input_ids.shape[1]:],
                               skip_special_tokens=True).strip()
            try:
                import re as _re
                blob = resp[resp.index("{"):resp.rindex("}") + 1] if "{" in resp and "}" in resp else resp
                try:
                    j = json.loads(blob)
                except Exception:
                    j = {}
                    for k, pat in (("dim1", "完成|部分|未动"), ("dim2", "正常|异常|无法判断"),
                                   ("dim3", "高|中|低"), ("pos", "是|否"), ("neg", "是|否")):
                        mm = _re.search(rf'{k}"\s*[:：]\s*["“]?({pat})', resp)
                        if mm:
                            j[k] = mm.group(1)
                    if not j:
                        raise ValueError("no fields")
                j = json.loads(json.dumps(j))
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
    f'"compass-AI-7B","{r["id"]}","{r["dim1"]}","{r["dim2"]}","{r["dim3"]}",'
    f'"{r["pos"]}","{r["neg"]}","{r["timeout"]}","{r["ts"]}"\r\n' for r in rows)
(PK / "goldpack_main_J2_7b.csv").write_text(csv, encoding="utf-8-sig")
dist = {}
for r in rows:
    dist[r["dim1"]] = dist.get(r["dim1"], 0) + 1
print(f"[done] n={len(rows)} dim1_dist={dist} csv={PK / 'goldpack_J2.csv'}", flush=True)
