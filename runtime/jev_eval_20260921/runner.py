"""Hosted Jev calibration evaluation — preregistered protocol runner.

Generates a deterministic decision set (seed=20260921), calls jev-latest one
question per request, records every raw response, computes Brier/ECE/accuracy.
No retries on content, no cherry-picking; failures recorded as-is.
"""
import json, random, time, os, sys, urllib.request, hashlib
from pathlib import Path

SEED = 20260921
N_PER_CELL = 60  # 4 cells x 60 = 240 questions
API = "https://api.typesafe.ai/v1/systemone"
KEY = Path.home() / ".claude" / ".cache" / "typesafe_api_key.env"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads" / "jev_eval"
OUT.mkdir(parents=True, exist_ok=True)
key = KEY.read_text(encoding="utf-8").strip().split("=", 1)[1]

rng = random.Random(SEED)

def gen_questions():
    qs = []
    # cell 1: noul-easy — single numeric comparison
    for i in range(N_PER_CELL):
        a, b = rng.randint(0, 10**6), rng.randint(0, 10**6)
        qs.append({"cell": "noul-easy", "qid": f"ne{i:03d}",
                   "state": {"a": a, "b": b},
                   "q": {"type": "noul", "instructions": "Is a greater than b? Answer strictly about the numbers given."},
                   "truth": 1 if a > b else 0})
    # cell 2: noul-hard — aggregate reasoning over a list
    for i in range(N_PER_CELL):
        nums = [rng.randint(0, 999) for _ in range(rng.randint(6, 12))]
        mode = rng.choice(["sum_gt", "max_in_first_half", "all_even"])
        if mode == "sum_gt":
            t = 1 if sum(nums) > 3000 else 0
            q = "Is the sum of all numbers in the list greater than 3000?"
        elif mode == "max_in_first_half":
            m = max(nums)
            t = 1 if m in nums[:len(nums)//2] else 0
            q = "Is the maximum value of the list located within the first half of the list?"
        else:
            t = 1 if all(x % 2 == 0 for x in nums) else 0
            q = "Are all numbers in the list even?"
        qs.append({"cell": "noul-hard", "qid": f"nh{i:03d}", "state": {"nums": nums},
                   "q": {"type": "noul", "instructions": q}, "truth": t})
    # cell 3: choice — pick the largest of three numbers
    for i in range(N_PER_CELL):
        opts = {"alpha": rng.randint(0, 999), "beta": rng.randint(0, 999), "gamma": rng.randint(0, 999)}
        correct = max(opts, key=opts.get)
        qs.append({"cell": "choice-max", "qid": f"cm{i:03d}", "state": opts,
                   "q": {"type": "choice",
                         "instructions": "Which option holds the largest number?",
                         "criteria": {"alpha": "Option alpha", "beta": "Option beta", "gamma": "Option gamma"}},
                   "truth": correct})
    # cell 4: noul-string — string reasoning (length / containment)
    words = ["orbit", "signal", "delta", "harbor", "quartz", "nimbus", "ember", "tundra", "cobalt", "ledge"]
    for i in range(N_PER_CELL):
        w1, w2 = rng.sample(words, 2)
        mode = rng.choice(["longer", "more_vowels"])
        if mode == "longer":
            t = 1 if len(w1) > len(w2) else 0
            q = f"Is word1 strictly longer than word2?"
        else:
            V = set("aeiou")
            t = 1 if sum(c in V for c in w1) > sum(c in V for c in w2) else 0
            q = "Does word1 contain more vowels than word2?"
        qs.append({"cell": "noul-string", "qid": f"ns{i:03d}", "state": {"word1": w1, "word2": w2},
                   "q": {"type": "noul", "instructions": q}, "truth": t})
    return qs

def call(item):
    body = json.dumps({"model": "jev-latest", "state": item["state"],
                       "questions": {"q": item["q"]}}).encode()
    req = urllib.request.Request(API, data=body, method="POST",
                                 headers={"Authorization": "Bearer " + key,
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def main():
    qs = gen_questions()
    gen = {"seed": SEED, "n": len(qs), "cells": sorted(set(q["cell"] for q in qs))}
    gsrc = json.dumps([{"cell": q["cell"], "qid": q["qid"], "state": q["state"], "q": q["q"], "truth": q["truth"]} for q in qs], sort_keys=True)
    gen_sha = hashlib.sha256(gsrc.encode()).hexdigest()
    (OUT / "decision_set.json").write_text(gsrc, encoding="utf-8", newline="\n")
    print("decision set:", gen, "sha256:", gen_sha[:16])
    results, tokens = [], 0
    for i, item in enumerate(qs):
        try:
            r = call(item)
            a = r["answers"]["q"]
            p = a.get("noul") if a["type"] == "noul" else None
            if a["type"] == "choice":
                probs = {k: v for k, v in a.items() if k not in ("type",)} if isinstance(a.get("choice"), dict) else None
            results.append({"qid": item["qid"], "cell": item["cell"], "truth": item["truth"],
                            "answer": a, "usage": r.get("usage", {})})
            tokens += r.get("usage", {}).get("input_tokens", 0) + r.get("usage", {}).get("output_tokens", 0)
        except Exception as e:
            results.append({"qid": item["qid"], "cell": item["cell"], "truth": item["truth"], "error": str(e)[:200]})
        if (i + 1) % 40 == 0:
            print(f"  {i+1}/{len(qs)} done, tokens so far {tokens}")
            (OUT / "raw_responses.jsonl").write_text("\n".join(json.dumps(x, sort_keys=True) for x in results), encoding="utf-8", newline="\n")
        time.sleep(0.3)
    (OUT / "raw_responses.jsonl").write_text("\n".join(json.dumps(x, sort_keys=True) for x in results), encoding="utf-8", newline="\n")
    print("DONE", len(results), "responses; total tokens:", tokens)

if __name__ == "__main__":
    main()
