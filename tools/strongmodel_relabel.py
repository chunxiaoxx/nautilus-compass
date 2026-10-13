#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""强模型重判 runner(R534 · STRONGMODEL_RELABEL_PREREG): MiniMax-M3 三态重判。

用法:
  python tools/strongmodel_relabel.py --pilot        # P0 先导:R532 盲评 58 条
  python tools/strongmodel_relabel.py --full         # P1 全批:v2 池 self_labeled 2519 条
key:env MINIMAX_API_KEY(绝不落仓)。
"""
import argparse
import json
import os
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROVIDERS = {
    "minimax": ("https://api.minimaxi.com/v1/chat/completions", "MiniMax-M3", "MINIMAX"),
    "glm": ("https://open.bigmodel.cn/api/paas/v4/chat/completions", "glm-4.5-air", "GLM_API_KEY"),
}
TMPL = """You are a verification judge. Decide whether the following
organization decision-and-outcome record constitutes a VALID reusable
precedent case.

Core test: the record must contain a concrete judgment or action, AND a
concrete verified outcome (numbers, status, artifacts, measured results).

Boundary rules (v1.1, operationalized):
- Plans / TODO lists / roadmaps without executed results = insufficient_evidence
- Design docs / strategy essays / pure descriptions without an executed
  action + verified outcome = fail
- Forwarding/handoff notes whose verdict is still pending = insufficient_evidence
- Monitoring ledgers / policy statements without a case outcome = fail
- A diagnosis with measured evidence (even small) = pass
- An executed fix with measured before/after = pass

Record:
{content}

Verdict (one word: pass / fail / insufficient_evidence):"""

LABELS = ("pass", "fail", "insufficient_evidence")


def load_key(provider="minimax"):
    env_name = PROVIDERS[provider][2]
    for cand in [os.environ.get(env_name),
                 _from_env_file(os.path.expanduser(f"~/.claude/.cache/{env_name.lower()}.env"), env_name),
                 _from_env_file(os.path.expanduser("~/nautilus-v5/.env"), env_name)]:
        if cand:
            return cand
    raise SystemExit(f"{env_name} not found")


def _from_env_file(p, name="MINIMAX_API_KEY"):
    if not os.path.exists(p):
        return None
    for l in open(p, encoding="utf-8", errors="ignore"):
        if l.strip().startswith(name):
            return l.split("=", 1)[1].strip()
    return None
def judge_one(key, content, retry=4, provider="minimax"):
    ep, model, _ = PROVIDERS[provider]
    prompt = TMPL.format(content=content[:1400])
    payload = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                          "temperature": 0, "max_tokens": 8192}).encode()
    last = None
    for i in range(retry):
        try:
            req = urllib.request.Request(ep, data=payload, method="POST",
                                         headers={"Authorization": f"Bearer {key}",
                                                  "Content-Type": "application/json"})
            r = json.loads(urllib.request.urlopen(req, timeout=180).read())
            txt = r["choices"][0]["message"]["content"] or ""
            txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.S).strip().lower()
            # v1.2 解析:标签词可能在推理段之后;取"verdict"/"answer"行或最后一次出现
            m = re.search(r"(?:verdict|answer)\s*[:\-]*\s*(pass|fail|insufficient_evidence)", txt)
            if m:
                return m.group(1)
            hits = [v for v in LABELS if v in txt]
            if hits:
                # 全文都出现时取最靠后(结论通常在末尾)
                return max(hits, key=lambda v: txt.rfind(v))
            return "unparsed:" + txt[:60]
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            time.sleep(10 * (i + 1))
    return "error:" + str(last)[:60]


def content_of(r):
    a = r.get("artifact") or {}
    for k in ("question", "response", "content", "model_answer", "official_truth",
              "answer_gold", "reason", "rationale"):
        v = a.get(k)
        if v and str(v).strip():
            return str(v)
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--provider", default="minimax", choices=list(PROVIDERS))
    ap.add_argument("--model", default=None)
    a = ap.parse_args()
    key = load_key(a.provider)
    if a.model:
        PROVIDERS[a.provider] = (PROVIDERS[a.provider][0], a.model, PROVIDERS[a.provider][2])
    global MODEL
    MODEL = PROVIDERS[a.provider][1]

    if a.pilot:
        rows = [json.loads(l) for l in open("runtime/org_fuel/selflabel_audit_sample.jsonl",
                                            encoding="utf-8")]
        rows = [r for r in rows if r.get("_content", "").strip()]
        out = f"runtime/org_fuel/strongmodel_pilot_r534_{a.provider}.jsonl"
        jobs = [{"id": r["id"], "content": r["_content"], "judge_verdict": r["judge_verdict"]}
                for r in rows]
    else:
        rows = [json.loads(l) for l in open("runtime/verdict_corpus/orgfuel_v2/split_train.jsonl",
                                            encoding="utf-8")] + \
               [json.loads(l) for l in open("runtime/verdict_corpus/orgfuel_v2/split_dev.jsonl",
                                            encoding="utf-8")]
        rows = [r for r in rows if not r.get("_src", "").startswith(("split_", "delta:"))]
        out = "runtime/org_fuel/strongmodel_relabel_r534.jsonl"
        jobs = [{"id": r["id"], "content": content_of(r), "judge_verdict": r["truth_label"],
                 "_src": r["_src"]} for r in rows]
    jobs = [j for j in jobs if j["content"].strip()]
    print(f"jobs={len(jobs)} model={MODEL}", flush=True)

    done = 0
    with open(out, "w", encoding="utf-8", newline="\n") as f, \
         ThreadPoolExecutor(max_workers=a.workers) as ex:
        def run(j):
            j["strongmodel_verdict"] = judge_one(key, j["content"], provider=a.provider)
            return j
        for res in ex.map(run, jobs):
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            f.flush()
            done += 1
            if done % 25 == 0:
                print(f"[{done}/{len(jobs)}]", flush=True)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
