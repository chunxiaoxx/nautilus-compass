#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NACRE v1 判分服务(T5.1 · OpenAI 风格薄壳 · port 19988 · A100)。

模型:Qwen3-1.7B + adapter(best_lora, sha16=dbcbab6f 与 HF 卡逐位一致)
POST /judge {"criteria":..., "artifact":...} → {"verdict": pass|fail|insufficient_evidence, "raw":...}
GET  /health → {"ok":true,...}
判据纪律:只推理不判读(标签即模型输出原文),置信/后处理归调用方。
"""
from fastapi import FastAPI
from pydantic import BaseModel
import peft  # noqa: F401  # adapter 加载需要
import torch
import re
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = "/root/vdd4/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master"
ADAPTER = "/root/vdd4/adapters/best_lora"
PROMPT_TMPL = """You are a verification judge. Given the criteria, the submitted
artifact, and the official reference, decide whether the response is correct.

{content}

Verdict (one word: pass / fail / insufficient_evidence):"""
LABELS = ["pass", "fail", "insufficient_evidence"]

app = FastAPI(title="NACRE judge v1", version="1.0.0")
_state = {"model": None, "tok": None}


def get_model():
    if _state["model"] is None:
        tok = AutoTokenizer.from_pretrained(BASE)
        model = AutoModelForCausalLM.from_pretrained(
            BASE, torch_dtype=torch.float16).to("cuda").eval()
        model = peft.PeftModel.from_pretrained(model, ADAPTER)
        _state["model"], _state["tok"] = model, tok
    return _state["model"], _state["tok"]


class JudgeIn(BaseModel):
    criteria: str = ""
    question: str = ""
    response: str = ""
    official_truth: str = ""
    max_new_tokens: int = 16


@app.get("/health")
def health():
    return {"ok": True, "model": "nacre-judge-v1", "adapter_sha16": "dbcbab6f",
            "base": "Qwen3-1.7B", "precision": "fp16"}


@app.post("/judge")
def judge(inp: JudgeIn):
    model, tok = get_model()
    parts = [f"criteria: {inp.criteria[:400]}"]
    if inp.question:
        parts.append(f"question: {inp.question[:800]}")
    parts.append(f"response: {inp.response[:2000]}")
    if inp.official_truth:
        parts.append(f"official_truth: {inp.official_truth[:800]}")
    prompt = PROMPT_TMPL.format(content="\n".join(parts))
    enc = tok(prompt, return_tensors="pt", truncation=True, max_length=2048).to("cuda")
    with torch.no_grad():
        gen = model.generate(**enc, max_new_tokens=inp.max_new_tokens,
                             do_sample=False, temperature=None, top_p=None, top_k=None)
    raw = tok.decode(gen[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
    verdict = next((l for l in LABELS if l in raw.lower()), "unparseable")
    return {"verdict": verdict, "raw": raw.strip()[:200],
            "adapter_sha16": "dbcbab6f", "precision": "fp16"}
