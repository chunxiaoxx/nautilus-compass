#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORG-FUEL 扩容判定(R455): queue+memory 两新源 × NACRE judge 三态判。
口径与 _fuel_judge_docs.py 完全一致(同模板/bf16+LoRA 合规部署)。"""
import json
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = "/root/vdd4/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master"
ADAPTER = "/root/vdd4/adapters/best_lora"
PAIRS = [("/root/vdd4/robust_exp/candidates_queue.jsonl",
          "/root/vdd4/robust_exp/fuel_verdicts_queue.jsonl"),
         ("/root/vdd4/robust_exp/candidates_memory.jsonl",
          "/root/vdd4/robust_exp/fuel_verdicts_memory.jsonl")]

JUDGE_TMPL = """You are a verification judge. Decide whether the following
organization decision-and-outcome record constitutes a VALID reusable
precedent case (it must contain: a concrete judgment or action, AND a
concrete verified outcome). Records without a concrete outcome are invalid.

Record:
{content}

Verdict (one word: pass / fail / insufficient_evidence):"""

rows_by_file = {c: [json.loads(l) for l in open(c, encoding="utf-8") if l.strip()]
                for c, _ in PAIRS}
total = sum(len(v) for v in rows_by_file.values())
print(f"candidates total={total}", flush=True)

tok = AutoTokenizer.from_pretrained(BASE)
m = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                         device_map={"": 0})
m = PeftModel.from_pretrained(m, ADAPTER)
m.eval()


def judge(text: str) -> str:
    prompt = JUDGE_TMPL.format(content=text[:1400])
    enc = tok(prompt, return_tensors="pt", truncation=True, max_length=768).to(m.device)
    with torch.no_grad():
        out = m.generate(**enc, max_new_tokens=8, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    resp = tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
    resp = resp.strip().lower()
    for v in ("pass", "fail", "insufficient_evidence"):
        if resp.startswith(v):
            return v
    return "insufficient_evidence"


done = 0
for cand_path, out_path in PAIRS:
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows_by_file[cand_path]:
            v = judge(r.get("content") or r.get("situation") or "")
            r["judge_verdict"] = v
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            done += 1
            if done % 20 == 0:
                print(f"[{done}/{total}]", flush=True)
print("ALL DONE", flush=True)
