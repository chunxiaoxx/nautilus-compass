#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORG-FUEL v0 判定段:369 候选判例 × NACRE judge(实例 v1)三态判。
输出:verdicts.jsonl(逐条) + 判定统计。bf16(部署纪律:只许 bf16/fp16)。
"""
import json
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = "/root/vdd4/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master"
ADAPTER = "/root/vdd4/adapters/best_lora"
CAND = "/root/vdd4/robust_exp/candidates_letters.jsonl"
OUT = "/root/vdd4/robust_exp/fuel_verdicts_letters.jsonl"

JUDGE_TMPL = """You are a verification judge. Decide whether the following
organization decision-and-outcome record constitutes a VALID reusable
precedent case (it must contain: a concrete judgment or action, AND a
concrete verified outcome). Records without a concrete outcome are invalid.

Record:
{content}

Verdict (one word: pass / fail / insufficient_evidence):"""

rows = [json.loads(l) for l in open(CAND, encoding="utf-8") if l.strip()]
print(f"candidates={len(rows)}", flush=True)

tok = AutoTokenizer.from_pretrained(BASE)
m = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                         device_map={"": 0})
m = PeftModel.from_pretrained(m, ADAPTER); m.eval()


def judge(text: str) -> str:
    prompt = JUDGE_TMPL.format(content=text[:1400])
    enc = tok(prompt, return_tensors="pt", truncation=True,
              max_length=768).to(m.device)
    with torch.no_grad():
        out = m.generate(**enc, max_new_tokens=6, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    t = tok.decode(out[0][enc.input_ids.shape[1]:], skip_special_tokens=True).strip().lower()
    for lab in ("pass", "fail", "insufficient_evidence"):
        if t.startswith(lab):
            return lab
    for lab in ("pass", "fail", "insufficient_evidence"):
        if lab in t.split()[:3]:
            return lab
    return "insufficient_evidence"


stats = {"pass": 0, "fail": 0, "insufficient_evidence": 0}
with open(OUT, "w", encoding="utf-8") as f:
    for i, r in enumerate(rows):
        v = judge(r["situation"])
        r["judge_verdict"] = v
        stats[v] += 1
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
        if (i + 1) % 50 == 0:
            print(f"{i+1}/{len(rows)} {stats}", flush=True)
print("FINAL:", stats, flush=True)
