#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A+ 情境改写查询生成器 v2(tokenizers 直编,绕 transformers5.16 AutoTokenizer 坑)。

非思考模式=手拼 <think>\n\n</think> 前缀。输出 A_plus_queries.json。
"""
import glob
import json
import os
import random
import re

import torch
from tokenizers import Tokenizer
from transformers import AutoModelForCausalLM

CORPUS_DIR = "/root/vdf/emb_bakeoff"
MODEL = "/root/vdd4/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master"
OUT = "/root/vdf/emb_bakeoff/A_plus_queries_v2.json"
N = 30
SYS = "你是评测集构建器。给定一条过去的工作记忆记录,写出:如果 agent 再次遇到完全相同的情况,它会输入的一句话情境查询。要求:只输出查询本身;用与记录相同的语言(以中文为主,保留英文错误码/工具名);不超过60字;不要复述记录原文措辞,要换成当事人当下的口吻。"

# v2 清洗(R437 归因发现一:15/30 条带指令回显/模板前缀 → 污染工作集)
BAD_MARKS = ("如果 agent", "如果再次", "情境查询", "查询:", "查询：", "评测集", "记忆记录")
PICK_SEPS = ("：", ":", "“", "\"", "「", "『")


def clean_query(resp: str) -> str:
    resp = resp.split("</think>")[-1].strip().splitlines()[0][:120] if resp.strip() else ""
    for _ in range(2):  # 最多剥两层
        hit = next((m for m in BAD_MARKS if m in resp), None)
        if not hit:
            break
        sep = next((s for s in PICK_SEPS if s in resp), None)
        resp = resp.split(sep, 1)[1].strip() if sep and resp.index(sep) > resp.index(hit) else ""
    return resp.strip(' "\'「」『』。.').strip()


def valid_query(q: str) -> bool:
    return len(q) >= 8 and len(q) <= 80 and not any(m in q for m in BAD_MARKS)


def parse_md(path: str) -> tuple:
    t = open(path, encoding="utf-8", errors="replace").read()
    if t.startswith("---"):
        m = re.match(r"---\n.*?\n---\n?", t, re.S)
        if m:
            t = t[m.end():]
    return os.path.basename(path), t.strip()[:2000]


def main():
    corpus = []
    for p in sorted(glob.glob(CORPUS_DIR + "/*.md")):
        name, body = parse_md(p)
        if name.upper() in ("MEMORY.MD", "INDEX.MD") or len(body) < 50:
            continue
        corpus.append({"name": name, "body": body})
    random.seed(42)
    sample = random.sample(corpus, min(N * 3, len(corpus)))  # 候选池 3x:清洗拒绝后仍有余量

    tok = Tokenizer.from_file(MODEL + "/tokenizer.json")
    im_start = tok.token_to_id("<|im_start|>")
    im_end = tok.token_to_id("<|im_end|>")
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16).to("cuda").eval()

    out = []
    for i, c in enumerate(sample):
        if len(out) >= N:
            break
        prompt = (f"<|im_start|>system\n{SYS}<|im_end|>\n"
                  f"<|im_start|>user\n记忆记录:\n{c['body'][:800]}<|im_end|>\n"
                  f"<|im_start|>assistant\n<think>\n\n</think>\n\n")
        ids = tok.encode(prompt).ids + [im_start]
        enc = torch.tensor([ids]).to("cuda")
        q = ""
        for attempt in range(3):  # 清洗拒绝后重试
            with torch.no_grad():
                gen = model.generate(enc, max_new_tokens=80, do_sample=True,
                                     temperature=0.7 + 0.2 * attempt, top_p=0.9)
            resp = tok.decode(gen[0][len(ids):].tolist(), skip_special_tokens=True)
            q = clean_query(resp)
            if valid_query(q):
                break
            q = ""
        if not q:
            print(f"[{i+1}/{len(sample)}] {c['name'][:28]} -> REJECTED(3 attempts)", flush=True)
            continue
        out.append({"gold": c["name"], "text": q})
        print(f"[{i+1}/{len(sample)}] {c['name'][:28]} -> {q[:46]}", flush=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("WROTE", OUT, len(out))


if __name__ == "__main__":
    main()
