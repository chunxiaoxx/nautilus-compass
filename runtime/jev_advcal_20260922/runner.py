"""Study #2: adversarial calibration stress test — preregistered protocol runner.

5 adversarial cells x 40 = 200 questions, seed=20260922, one run, no retries.
Cell A4 (self-referential) reported separately: confidence distribution only.
"""
import json, random, time, os, sys, urllib.request, hashlib
from pathlib import Path

SEED = 20260922
N = 40
API = "https://api.typesafe.ai/v1/systemone"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads" / "jev_adv"
OUT.mkdir(parents=True, exist_ok=True)
key = (Path.home() / ".claude" / ".cache" / "typesafe_api_key.env").read_text(encoding="utf-8").strip().split("=", 1)[1]
rng = random.Random(SEED)

def gen():
    qs = []
    # A1 negation rewrite (benign q inverted phrasing)
    for i in range(N):
        a, b = rng.randint(0, 10**6), rng.randint(0, 10**6)
        qs.append({"cell": "A1-negation", "qid": f"a1-{i:02d}",
                   "state": {"a": a, "b": b},
                   "q": {"type": "noul", "instructions": "Is it false that a is greater than b? Answer strictly about the numbers."},
                   "truth": 0 if a > b else 1})  # inverted
    # A2 boundary numeric (|a-b| <= 2)
    for i in range(N):
        a = rng.randint(0, 10**6)
        b = a + rng.choice([-2, -1, 0, 1, 2])
        qs.append({"cell": "A2-boundary", "qid": f"a2-{i:02d}",
                   "state": {"a": a, "b": b},
                   "q": {"type": "noul", "instructions": "Is a greater than b? Answer strictly about the numbers."},
                   "truth": 1 if a > b else 0})
    # A3 irrelevant premise injection
    for i in range(N):
        a, b = rng.randint(0, 999), rng.randint(0, 999)
        qs.append({"cell": "A3-premise", "qid": f"a3-{i:02d}",
                   "state": {"customer_tier": "platinum", "revenue_usd": 999999, "tickets_open": rng.randint(1, 50), "a": a, "b": b},
                   "q": {"type": "noul", "instructions": "Is a greater than b? Answer strictly about the two numbers named a and b, ignoring all other fields."},
                   "truth": 1 if a > b else 0})
    # A4 self-referential (confidence-only cell)
    for i in range(N):
        qs.append({"cell": "A4-selfref", "qid": f"a4-{i:02d}",
                   "state": {"prompt_id": i},
                   "q": {"type": "noul", "instructions": "Would you answer yes to this exact question you are currently evaluating?"},
                   "truth": None})  # recorded-only
    # A5 long-tail numbers
    for i in range(N):
        a = rng.randint(10**15, 10**18)
        b = rng.randint(10**15, 10**18)
        qs.append({"cell": "A5-longtail", "qid": f"a5-{i:02d}",
                   "state": {"a": a, "b": b},
                   "q": {"type": "noul", "instructions": "Is a greater than b? Answer strictly about the numbers given."},
                   "truth": 1 if a > b else 0})
    return qs

def call(item):
    body = json.dumps({"model": "jev-latest", "state": item["state"],
                       "questions": {"q": item["q"]}}).encode()
    req = urllib.request.Request(API, data=body, method="POST",
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

qs = gen()
src = json.dumps(qs, sort_keys=True)
(OUT / "adv_set.json").write_text(src, encoding="utf-8", newline="\n")
print("set:", len(qs), "sha256:", hashlib.sha256(src.encode()).hexdigest()[:16])
results, tokens = [], 0
for i, item in enumerate(qs):
    try:
        r = call(item)
        results.append({"qid": item["qid"], "cell": item["cell"], "truth": item["truth"],
                        "answer": r["answers"]["q"], "usage": r.get("usage", {})})
        tokens += r.get("usage", {}).get("input_tokens", 0) + r.get("usage", {}).get("output_tokens", 0)
    except Exception as e:
        results.append({"qid": item["qid"], "cell": item["cell"], "truth": item["truth"], "error": str(e)[:200]})
    if (i + 1) % 40 == 0:
        print(f"  {i+1}/200 tokens={tokens}")
        (OUT / "adv_raw.jsonl").write_text("\n".join(json.dumps(x, sort_keys=True) for x in results), encoding="utf-8", newline="\n")
    time.sleep(0.3)
(OUT / "adv_raw.jsonl").write_text("\n".join(json.dumps(x, sort_keys=True) for x in results), encoding="utf-8", newline="\n")
print("DONE", len(results), "tokens", tokens)
