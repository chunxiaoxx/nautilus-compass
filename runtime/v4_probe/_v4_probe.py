# -*- coding: utf-8 -*-
"""V4 效用闭环探针(实例端)——分辨率单变量隔离实验。

承:v4_probe_criteria.lock.json + docs/plans/2026-10-04-v4效用闭环探针预注册草案-v0.md
设计:同一 ckpt(step2000)+同一 60 对 held-out 池,仅输入图像三档(native/d128/d96),
GT 不变;主判据 drop128>=0.15 → 效用损害成立。
自校验:native 档 vs eval_report 0.8667 偏差>0.03 → 探针 RED 先证伪自己。
用法: nohup python v4_probe.py > v4_probe.log 2>&1 < /dev/null &
产物: /root/vdd3/gen4_v2/v4_report.json + .v4_done 锁
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import torch
from PIL import Image
from peft import PeftModel
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
from qwen_vl_utils import process_vision_info

OUT = Path("/root/vdd3/gen4_v2")
BASE = "/root/sysmodels/Qwen2.5-VL-7B-Instruct"
CKPT = sorted((OUT / "checkpoints").glob("step*"), key=lambda p: int(p.name[4:]))[-1]
DONE = OUT / ".v4_done"
ARMS = {"native": None, "d128": 128, "d96": 96}
JSON_RE = __import__("re").compile(r"\{[^{}]*\}")


def infer(model, proc, img: Image.Image, prompt: str) -> str:
    msgs = [{"role": "user", "content": [
        {"type": "image", "image": img}, {"type": "text", "text": prompt}]}]
    txt = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    image_data, _ = process_vision_info(msgs)
    inputs = proc(text=[txt], images=image_data, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=64, do_sample=False)
    return proc.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)


def parse_bool(s: str, key: str):
    m = JSON_RE.search(s or "")
    if not m:
        return None
    try:
        return bool(json.loads(m.group()).get(key))
    except Exception:
        return None


def downsize(img: Image.Image, short: int) -> Image.Image:
    w, h = img.size
    scale = short / min(w, h)
    return img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)


def main() -> int:
    if DONE.exists():
        print("V4_ALREADY_DONE")
        return 0
    t0 = time.time()
    proc = AutoProcessor.from_pretrained(BASE, max_pixels=768 * 28 * 28)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        BASE, torch_dtype=torch.bfloat16, device_map="auto")
    model = PeftModel.from_pretrained(model, str(CKPT))
    model.eval()

    rows = [json.loads(l) for l in (OUT / "eval_set.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    prompt = rows[0]["prompt"]
    # 盲探针:d96 帧 vs 灰图,输出须不同(3/3 gate)
    blind_ok = 0
    for r in rows[:3]:
        img = Image.open(r["image"]).convert("RGB")
        a = infer(model, proc, downsize(img, 96), prompt)
        b = infer(model, proc, Image.new("RGB", img.size, (128, 128, 128)), prompt)
        blind_ok += int(a != b)
    print(f"V4_BLIND_PROBE {blind_ok}/3", flush=True)

    detail = []
    acc = {k: [0, 0] for k in ARMS}
    for i, r in enumerate(rows):
        img = Image.open(r["image"]).convert("RGB")
        gold = r["gold"]["hand_present"]
        row = {"i": i, "frame": r.get("frame"), "gold": gold}
        for arm, short in ARMS.items():
            im = img if short is None else downsize(img, short)
            ph = parse_bool(infer(model, proc, im, prompt), "hand_present")
            if ph is not None:
                acc[arm][0] += int(ph == gold)
                acc[arm][1] += 1
            row[arm] = ph
        detail.append(row)
        print(f"{i+1}/{len(rows)} {row}", flush=True)

    a_native = acc["native"][0] / acc["native"][1] if acc["native"][1] else None
    a_128 = acc["d128"][0] / acc["d128"][1] if acc["d128"][1] else None
    a_96 = acc["d96"][0] / acc["d96"][1] if acc["d96"][1] else None
    drop128 = round(a_native - a_128, 4) if a_native is not None and a_128 is not None else None
    drop96 = round(a_native - a_96, 4) if a_native is not None and a_96 is not None else None

    report = {
        "case": "v4_utility_probe", "ckpt": CKPT.name,
        "criteria_lock": "v4_probe_criteria.lock.json",
        "blind_probe": f"{blind_ok}/3",
        "acc": {k: round(v[0] / v[1], 4) if v[1] else None for k, v in acc.items()},
        "n": {k: v[1] for k, v in acc.items()},
        "drop128": drop128, "drop96": drop96,
        "V4_J1_gate": ">=0.15 established / <0.05 not_established / else partial",
        "self_check_native": {
            "ref": 0.8667,
            "delta": round(abs(a_native - 0.8667), 4) if a_native is not None else None,
            "gate": "<=0.03 pass; RED=probe fault, falsify probe first"},
        "elapsed_s": round(time.time() - t0, 1),
    }
    (OUT / "v4_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "v4_detail.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in detail), encoding="utf-8")
    DONE.write_text(json.dumps({"done_at": time.strftime("%F %T")}), encoding="utf-8")
    print("V4_DONE", json.dumps({k: report[k] for k in ["acc", "drop128", "drop96", "self_check_native"]}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
