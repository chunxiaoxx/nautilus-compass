#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-judge EverMemBench predictions with Claude vs DeepSeek V4-flash.

Cost: ~$0.50 with Sonnet 4.6, ~$0.05 with Haiku 4.5. Time: ~3 min for n=100
sequential. Run after evermembench_bge.py completes.

Usage:
    ANTHROPIC_API_KEY=sk-ant-... python cross_judge_em_claude.py [JSONL] [N]
Defaults: JSONL=paper/results/em_bge_v3_per_question.jsonl  N=100
"""
import json, os, random, sys, time, urllib.request, urllib.error
from collections import defaultdict, Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Switch to "claude-haiku-4-5" for ~10x cost savings (see report at end)
MODEL = "claude-sonnet-4-6"
SEED = 20260507
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
SYSTEM = (
    "You are a strict QA judge. Output exactly one of CORRECT or INCORRECT. "
    "CORRECT = predicted answer conveys the same factual content as ground "
    "truth. INCORRECT otherwise. No explanation."
)


def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def stratified_sample(rows, n, seed):
    by_topic = defaultdict(list)
    for r in rows:
        by_topic[r.get("topic", "unknown")].append(r)
    topics = sorted(by_topic.keys())
    if not topics:
        return []
    per = max(1, n // len(topics))
    rng = random.Random(seed)
    out = []
    for t in topics:
        bucket = list(by_topic[t])
        rng.shuffle(bucket)
        out.extend(bucket[:per])
    if len(out) < n:
        seen = {id(r) for r in out}
        leftover = [r for r in rows if id(r) not in seen]
        rng.shuffle(leftover)
        out.extend(leftover[: n - len(out)])
    return out[:n]


def call_claude_sdk(client, pred, gold):
    msg = client.messages.create(
        model=MODEL, max_tokens=8, system=SYSTEM,
        messages=[{"role": "user",
                   "content": f"PREDICTED: {pred}\nGROUND_TRUTH: {gold}\nVerdict:"}],
    )
    return msg.content[0].text if msg.content else ""


def call_claude_http(api_key, pred, gold):
    body = json.dumps({
        "model": MODEL, "max_tokens": 8, "system": SYSTEM,
        "messages": [{"role": "user",
                      "content": f"PREDICTED: {pred}\nGROUND_TRUTH: {gold}\nVerdict:"}],
    }).encode()
    req = urllib.request.Request(ANTHROPIC_URL, data=body, headers={
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
    }, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                obj = json.loads(r.read())
                blocks = obj.get("content", [])
                if blocks and isinstance(blocks, list):
                    return blocks[0].get("text", "")
                return ""
        except urllib.error.HTTPError as e:
            if attempt == 2 or (e.code < 500 and e.code != 429):
                raise
            time.sleep(2 ** attempt)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    return ""


def parse_verdict(text):
    if not text:
        return None
    t = text.strip().upper()
    if "CORRECT" in t and "INCORRECT" not in t:
        return True
    if "INCORRECT" in t:
        return False
    head = t.split()[0] if t.split() else ""
    if head == "CORRECT": return True
    if head == "INCORRECT": return False
    return None


def cohen_kappa(a, b):
    n = len(a)
    if n == 0: return 0.0
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[k] / n) * (cb[k] / n) for k in set(list(ca) + list(cb)))
    if pe >= 1.0: return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1 - pe)


def main():
    jsonl_path = sys.argv[1] if len(sys.argv) > 1 else "paper/results/em_bge_v3_per_question.jsonl"
    sample_n = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set.", file=sys.stderr)
        print("  export ANTHROPIC_API_KEY=sk-ant-...   (or set on Windows)", file=sys.stderr)
        sys.exit(2)

    in_path = Path(jsonl_path)
    if not in_path.exists():
        print(f"ERROR: input not found: {in_path}", file=sys.stderr)
        sys.exit(2)

    rows = load_jsonl(in_path)
    if not rows:
        print(f"ERROR: no rows in {in_path}", file=sys.stderr)
        sys.exit(2)

    sample = stratified_sample(rows, sample_n, SEED)
    print(f"[info] loaded {len(rows)} rows · sampled {len(sample)} · model={MODEL}")

    use_sdk, client = False, None
    try:
        import anthropic  # type: ignore
        client = anthropic.Anthropic(api_key=api_key)
        use_sdk = True
        print("[info] using anthropic SDK")
    except ImportError:
        print("[info] anthropic SDK not installed · using stdlib HTTP")

    out_dir = Path("paper/results"); out_dir.mkdir(parents=True, exist_ok=True)
    per_path = out_dir / "em_cross_judge_claude_per_question.jsonl"
    summary_path = out_dir / "em_cross_judge_claude_summary.json"

    results, t0 = [], time.time()
    with open(per_path, "w", encoding="utf-8") as fout:
        for i, rec in enumerate(sample, 1):
            pred, gold = str(rec.get("pred", "")), str(rec.get("gold", ""))
            ds_ok = bool(rec.get("ok", False))
            try:
                text = call_claude_sdk(client, pred, gold) if use_sdk else call_claude_http(api_key, pred, gold)
            except Exception as e:
                text = f"ERROR:{e}"
            verdict = parse_verdict(text)
            row = {"topic": rec.get("topic"), "qa_id": rec.get("qa_id"),
                   "Q": rec.get("Q"), "gold": gold, "pred": pred,
                   "deepseek_ok": ds_ok, "claude_raw": text, "claude_ok": verdict}
            results.append(row)
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            if i % 10 == 0 or i == len(sample):
                print(f"[progress] {i}/{len(sample)}  elapsed={time.time()-t0:.0f}s")

    parsed = [r for r in results if r["claude_ok"] is not None]
    n = len(parsed)
    ds_acc = sum(1 for r in parsed if r["deepseek_ok"]) / n if n else 0.0
    cl_acc = sum(1 for r in parsed if r["claude_ok"]) / n if n else 0.0
    a = ["C" if r["deepseek_ok"] else "I" for r in parsed]
    b = ["C" if r["claude_ok"] else "I" for r in parsed]
    kappa = cohen_kappa(a, b)
    ds_yes_cl_no = [r for r in parsed if r["deepseek_ok"] and not r["claude_ok"]]
    ds_no_cl_yes = [r for r in parsed if not r["deepseek_ok"] and r["claude_ok"]]

    def ex(r):
        return {"topic": r["topic"], "qa_id": r["qa_id"],
                "Q": (r["Q"] or "")[:100], "gold": (r["gold"] or "")[:100],
                "pred": (r["pred"] or "")[:100],
                "deepseek": r["deepseek_ok"], "claude": r["claude_ok"]}

    summary = {
        "model": MODEL, "input_jsonl": str(in_path),
        "sample_n": len(sample), "parsed_n": n, "unparsed_n": len(results) - n,
        "deepseek_acc": round(ds_acc, 4), "claude_acc": round(cl_acc, 4),
        "cohen_kappa": round(kappa, 4),
        "disagree_total": len(ds_yes_cl_no) + len(ds_no_cl_yes),
        "deepseek_yes_claude_no": len(ds_yes_cl_no),
        "deepseek_no_claude_yes": len(ds_no_cl_yes),
        "examples_deepseek_yes_claude_no": [ex(r) for r in ds_yes_cl_no[:10]],
        "examples_deepseek_no_claude_yes": [ex(r) for r in ds_no_cl_yes[:10]],
        "elapsed_sec": round(time.time() - t0, 1),
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print()
    print(f"=== cross-judge summary ({MODEL}) ===")
    print(f"  sample_n          : {len(sample)}")
    print(f"  parsed            : {n}  (unparsed={len(results)-n})")
    print(f"  deepseek_acc      : {ds_acc:.4f}")
    print(f"  claude_acc        : {cl_acc:.4f}")
    print(f"  cohen_kappa       : {kappa:.4f}")
    print(f"  disagreements     : {summary['disagree_total']}")
    print(f"    DS=Y / Claude=N : {len(ds_yes_cl_no)}")
    print(f"    DS=N / Claude=Y : {len(ds_no_cl_yes)}")
    print(f"  per-question  -> {per_path}")
    print(f"  summary       -> {summary_path}")


if __name__ == "__main__":
    main()
