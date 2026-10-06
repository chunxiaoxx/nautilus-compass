#!/usr/bin/env python3
"""E1 复考 runner(PREFOR_E1_RECHECK_20261006 §三 v4 定版口径,零逻辑改动)。
判分器=Qwen2.5-VL-3B(4bit 略——A100 bf16 加载,注明口径差异;如需严格 4bit 再降)。
双包:main(498,blind=main_blind_data.js)+OOD(400,blind=judge_pack/blind_data.js)。
判读逻辑/PROMPT/VALID/容错=tools/e1_j2_batch_judge_3b.py v4 定版逐行照抄(commit 0ab4e735)。
逐条落 jsonl 断点续跑;GPU 守门>2G 退出。产出 *_recheck.csv 供 ER1 与交卷正本逐条比对。"""
import json
import re
import subprocess
import time
from pathlib import Path

from PIL import Image as PILImage
import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

BASE = Path("/root/vdd4/e1_recheck/unpack")
MODEL = "/root/vdd4/modelscope/models/Qwen--Qwen2.5-VL-3B-Instruct/snapshots/master"

PACKS = [
    {"tag": "main", "blind": BASE / "main_blind_data.js", "frames": BASE / "mainpack",
     "ans": BASE / "j2_answers_main_4bit.jsonl", "csv": BASE / "goldpack_J2_main_recheck4bit.csv"},
    {"tag": "ood", "blind": BASE / "judge_pack" / "blind_data.js", "frames": BASE / "judge_pack",
     "ans": BASE / "j2_answers_ood_4bit.jsonl", "csv": BASE / "goldpack_J2_ood_recheck4bit.csv"},
]

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
Answer in Chinese values. 输出格式(按画面实况选值):{{"dim1":"<完成|部分|未动>","dim2":"<正常|异常|无法判断>","dim3":"<高|中|低>","pos":"<是|否>","neg":"<是|否>"}}
只输出一行JSON,不要任何其他文字"""


def gpu_busy_gib():
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True)
    return int(out.stdout.strip().splitlines()[0]) / 1024


def parse_samples(blind: Path):
    raw = blind.read_text(encoding="utf-8")
    m = re.search(r"samples:\s*(\[.*?\])\s*\}", raw, re.S)
    return json.loads(m.group(1))


def judge_pack(model, proc, pk: dict):
    samples = parse_samples(pk["blind"])
    done = {}
    if pk["ans"].exists():
        for line in pk["ans"].read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done[r["id"]] = r
    print(f"[{pk['tag']}] n={len(samples)} resume={len(done)}", flush=True)
    t0 = time.time()
    with pk["ans"].open("a", encoding="utf-8") as f:
        for i, s in enumerate(samples):
            if s["id"] in done:
                continue
            img = pk["frames"] / s["frame"]
            if not img.exists():
                ans = {k: ("无法判断" if k == "dim2" else "低" if k == "dim3" else v[0])
                       for k, v in VALID.items()}
                ans["timeout"] = 1
            else:
                conv = [{"role": "user", "content": [
                    {"type": "image", "image": str(img)},
                    {"type": "text", "text": PROMPT.format(task=s.get("task_en") or s["task_zh"],
                                                           pct=s["progress_pct"])},
                ]}]
                text = proc.apply_chat_template(conv, tokenize=False, add_generation_prompt=True)
                inputs = proc(text=[text], images=[PILImage.open(img).convert("RGB")],
                              return_tensors="pt").to("cuda")
                with torch.no_grad():
                    out = model.generate(**inputs, max_new_tokens=80, do_sample=False, temperature=None)
                resp = proc.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
                try:
                    blob = resp[resp.index("{"):resp.rindex("}") + 1] if "{" in resp and "}" in resp else resp
                    try:
                        j = json.loads(blob)
                    except Exception:
                        j = {}
                        for k, pat in (("dim1", "完成|部分|未动"), ("dim2", "正常|异常|无法判断"),
                                       ("dim3", "高|中|低"), ("pos", "是|否"), ("neg", "是|否")):
                            mm = re.search(rf'{k}"\s*[:：]\s*["“]?({pat})', resp)
                            if mm:
                                j[k] = mm.group(1)
                        if not j:
                            raise ValueError("no fields")
                    j = json.loads(json.dumps(j))
                    ans = {k: (j[k] if j.get(k) in VALID[k] else
                               ("无法判断" if k == "dim2" else VALID[k][0])) for k in VALID}
                    ans["timeout"] = 0
                except Exception:
                    ans = {"dim1": "未动", "dim2": "无法判断", "dim3": "低",
                           "pos": "否", "neg": "否", "timeout": 1}
            row = {"id": s["id"], "ts": time.strftime("%H:%M:%S"), **ans}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            if (i + 1) % 20 == 0:
                print(f"[{pk['tag']} {i + 1}/{len(samples)}] t={time.time() - t0:.0f}s", flush=True)
    rows = [json.loads(l) for l in pk["ans"].read_text(encoding="utf-8").splitlines() if l.strip()]
    csv = "judge,id,dim1,dim2,dim3,pos,neg,timeout,ts\r\n"
    csv += "".join(
        f'"compass-AI","{r["id"]}","{r["dim1"]}","{r["dim2"]}","{r["dim3"]}",'
        f'"{r["pos"]}","{r["neg"]}","{r["timeout"]}","{r["ts"]}"\r\n' for r in rows)
    pk["csv"].write_text(csv, encoding="utf-8-sig")
    dist = {}
    for r in rows:
        dist[r["dim1"]] = dist.get(r["dim1"], 0) + 1
    print(f"[{pk['tag']} done] n={len(rows)} dim1={dist} csv={pk['csv']}", flush=True)


def main():
    if gpu_busy_gib() > 2.0:
        print(f"[GATE] GPU busy ({gpu_busy_gib():.1f}GiB) — abort")
        return 1
    print(f"[GATE] GPU idle — start", flush=True)
    from transformers import BitsAndBytesConfig
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL, quantization_config=bnb, device_map="cuda")
    proc = AutoProcessor.from_pretrained(MODEL)
    for pk in PACKS:
        judge_pack(model, proc, pk)
    print("E1-RECHECK-ALL-DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
