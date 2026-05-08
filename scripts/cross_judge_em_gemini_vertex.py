#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-judge EverMemBench predictions with Gemini (Vertex AI) vs DeepSeek V4-flash.

Sister of cross_judge_em_claude.py · same JSONL input · same κ output ·
swaps the LLM family from Anthropic to Google for an independent
inter-judge agreement signal.

Auth: Google Cloud service-account JSON via google-auth + raw HTTP.
Endpoint: us-central1 Vertex AI publishers/google/models endpoint.

Cost: ~$1.50 with gemini-2.5-pro for n=100 (rough · billed by usage).
Time: ~5-8 min for n=100 sequential.

Usage:
    set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json
    python cross_judge_em_gemini_vertex.py [JSONL] [N] [--model gemini-2.5-pro]
Defaults: JSONL=paper/results/em_bge_v3_per_question.jsonl  N=100  model=gemini-2.5-pro
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DEFAULT_MODEL = "gemini-2.5-pro"
DEFAULT_LOCATION = "us-central1"
SEED = 20260507
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


def get_oauth_token(sa_json_path):
    from google.oauth2 import service_account
    import google.auth.transport.requests as gar

    creds = service_account.Credentials.from_service_account_file(
        sa_json_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    creds.refresh(gar.Request())
    return creds.token, creds.expiry, creds


def maybe_refresh_token(creds):
    """Refresh token if it has expired or is close to expiring (5 min buffer)."""
    import google.auth.transport.requests as gar
    from datetime import datetime, timedelta

    if creds.expiry is None or creds.expiry - datetime.utcnow() < timedelta(minutes=5):
        creds.refresh(gar.Request())
    return creds.token


def call_gemini_vertex(token, project, location, model, pred, gold):
    """Single Vertex AI Gemini generateContent call · returns text or empty string."""
    url = (
        f"https://{location}-aiplatform.googleapis.com/v1/"
        f"projects/{project}/locations/{location}/"
        f"publishers/google/models/{model}:generateContent"
    )
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{
            "role": "user",
            "parts": [{"text": f"PREDICTED: {pred}\nGROUND_TRUTH: {gold}\nVerdict:"}],
        }],
        # gemini-2.5-pro reserves "thoughts" tokens out of max_output_tokens; budget enough
        "generationConfig": {"maxOutputTokens": 256, "temperature": 0.0},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                obj = json.loads(r.read())
                cands = obj.get("candidates") or []
                if not cands:
                    return ""
                content = cands[0].get("content") or {}
                parts = content.get("parts") or []
                texts = [p.get("text", "") for p in parts if "text" in p]
                return "".join(texts).strip()
        except urllib.error.HTTPError as e:
            if attempt == 2 or (e.code < 500 and e.code != 429):
                err = e.read()[:300].decode("utf-8", errors="replace")
                raise RuntimeError(f"HTTP {e.code}: {err}")
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
    if head == "CORRECT":
        return True
    if head == "INCORRECT":
        return False
    return None


def cohen_kappa(a, b):
    n = len(a)
    if n == 0:
        return 0.0
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[k] / n) * (cb[k] / n) for k in set(list(ca) + list(cb)))
    if pe >= 1.0:
        return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1 - pe)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", nargs="?", default="paper/results/em_bge_v3_per_question.jsonl")
    ap.add_argument("n", nargs="?", type=int, default=100)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--location", default=DEFAULT_LOCATION)
    ap.add_argument("--sa-json", default=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""))
    args = ap.parse_args()

    if not args.sa_json:
        print("ERROR: provide --sa-json or set GOOGLE_APPLICATION_CREDENTIALS env", file=sys.stderr)
        sys.exit(2)

    sa_path = Path(args.sa_json)
    if not sa_path.exists():
        print(f"ERROR: sa-json not found: {sa_path}", file=sys.stderr)
        sys.exit(2)

    sa = json.loads(sa_path.read_text(encoding="utf-8"))
    project = sa.get("project_id")
    if not project:
        print("ERROR: project_id missing from sa-json", file=sys.stderr)
        sys.exit(2)

    in_path = Path(args.jsonl)
    if not in_path.exists():
        print(f"ERROR: input not found: {in_path}", file=sys.stderr)
        sys.exit(2)

    rows = load_jsonl(in_path)
    if not rows:
        print(f"ERROR: no rows in {in_path}", file=sys.stderr)
        sys.exit(2)

    sample = stratified_sample(rows, args.n, SEED)
    print(f"[info] loaded {len(rows)} rows · sampled {len(sample)}")
    print(f"[info] model={args.model} location={args.location} project={project}")

    token, _expiry, creds = get_oauth_token(str(sa_path))
    print(f"[info] OAuth token minted (sa={sa.get('client_email')})")

    out_dir = Path("paper/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    per_path = out_dir / "em_cross_judge_gemini_per_question.jsonl"
    summary_path = out_dir / "em_cross_judge_gemini_summary.json"

    results, t0 = [], time.time()
    with open(per_path, "w", encoding="utf-8") as fout:
        for i, rec in enumerate(sample, 1):
            pred, gold = str(rec.get("pred", "")), str(rec.get("gold", ""))
            ds_ok = bool(rec.get("ok", False))
            tok = maybe_refresh_token(creds)
            try:
                text = call_gemini_vertex(tok, project, args.location, args.model, pred, gold)
            except Exception as e:
                text = f"ERROR:{e}"
            verdict = parse_verdict(text)
            row = {
                "topic": rec.get("topic"),
                "qa_id": rec.get("qa_id"),
                "Q": rec.get("Q"),
                "gold": gold,
                "pred": pred,
                "deepseek_ok": ds_ok,
                "gemini_raw": text,
                "gemini_ok": verdict,
            }
            results.append(row)
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            fout.flush()
            if i % 10 == 0 or i == len(sample):
                print(f"[progress] {i}/{len(sample)}  elapsed={time.time()-t0:.0f}s")

    parsed = [r for r in results if r["gemini_ok"] is not None]
    n = len(parsed)
    ds_acc = sum(1 for r in parsed if r["deepseek_ok"]) / n if n else 0.0
    gm_acc = sum(1 for r in parsed if r["gemini_ok"]) / n if n else 0.0
    a = ["C" if r["deepseek_ok"] else "I" for r in parsed]
    b = ["C" if r["gemini_ok"] else "I" for r in parsed]
    kappa = cohen_kappa(a, b)
    ds_yes_gm_no = [r for r in parsed if r["deepseek_ok"] and not r["gemini_ok"]]
    ds_no_gm_yes = [r for r in parsed if not r["deepseek_ok"] and r["gemini_ok"]]

    def ex(r):
        return {
            "topic": r["topic"], "qa_id": r["qa_id"],
            "Q": (r["Q"] or "")[:100], "gold": (r["gold"] or "")[:100],
            "pred": (r["pred"] or "")[:100],
            "deepseek": r["deepseek_ok"], "gemini": r["gemini_ok"],
        }

    summary = {
        "model": args.model,
        "input_jsonl": str(in_path),
        "sample_n": len(sample),
        "parsed_n": n,
        "unparsed_n": len(results) - n,
        "deepseek_acc": round(ds_acc, 4),
        "gemini_acc": round(gm_acc, 4),
        "cohen_kappa": round(kappa, 4),
        "disagree_total": len(ds_yes_gm_no) + len(ds_no_gm_yes),
        "deepseek_yes_gemini_no": len(ds_yes_gm_no),
        "deepseek_no_gemini_yes": len(ds_no_gm_yes),
        "examples_deepseek_yes_gemini_no": [ex(r) for r in ds_yes_gm_no[:10]],
        "examples_deepseek_no_gemini_yes": [ex(r) for r in ds_no_gm_yes[:10]],
        "elapsed_sec": round(time.time() - t0, 1),
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print()
    print(f"=== cross-judge summary ({args.model}) ===")
    print(f"  sample_n          : {len(sample)}")
    print(f"  parsed            : {n}  (unparsed={len(results)-n})")
    print(f"  deepseek_acc      : {ds_acc:.4f}")
    print(f"  gemini_acc        : {gm_acc:.4f}")
    print(f"  cohen_kappa       : {kappa:.4f}")
    print(f"  disagreements     : {summary['disagree_total']}")
    print(f"    DS=Y / Gemini=N : {len(ds_yes_gm_no)}")
    print(f"    DS=N / Gemini=Y : {len(ds_no_gm_yes)}")
    print(f"  per-question  -> {per_path}")
    print(f"  summary       -> {summary_path}")


if __name__ == "__main__":
    main()
