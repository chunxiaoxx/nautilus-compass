"""Build structured session summary cards for the LongMemEval-S haystack.

Preregistration: docs/plans/2026-09-02-summary-layer-preregistration.md §2.1.

Each unique session (deduped by session_id) gets one card:
  [Session <id> · <date>]
  USER FACTS: one bullet per fact, entities/amounts/counts/dates preserved
  ASSISTANT: what the assistant did/said/recommended
  TOPICS: 3-5 keywords

Design constraint: countability first — ms questions are counting questions,
so bullets must keep quantities as separate lines, no paragraph prose.

LLM rides the ARK coding plan endpoint (plan quota, not metered API).
Cache file is the single source of truth; rerun resumes where it left off.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

HERE = Path(__file__).parent
DEFAULT_DS = Path.home() / (
    ".cache/huggingface/hub/datasets--xiaowu0162--longmemeval"
    "/snapshots/2ec2a557f339b6c0369619b1ed5793734cc87533/longmemeval_s")
CACHE = HERE / "_e2e_diag" / "session_summaries.json"

API_BASE = os.environ.get("ZMM_LLM_BASE_URL",
                          "https://ark.cn-beijing.volces.com/api/coding/v3")
API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("ZMM_SUMMARY_MODEL", "doubao-seed-2-0-pro-260215")
BACKOFF = [2, 5, 15, 30]
MAX_SESSION_CHARS = 9000  # ~2.5k tokens in; LongMemEval-S sessions mostly fit


def session_text(session: list[dict]) -> str:
    parts = [f"[{t.get('role', '?')}] {t.get('content', '')}" for t in session]
    return "\n".join(parts)[:MAX_SESSION_CHARS]


def content_hash(session: list[dict]) -> str:
    return hashlib.sha1(
        json.dumps(session, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()[:16]


PROMPT = """Summarize this conversation session into a strict card format.

RULES:
- USER FACTS: one bullet per concrete fact the USER stated or did. Preserve every
  entity name, quantity, amount, date, and place as its own bullet. Never merge
  two facts into one bullet (downstream tasks COUNT these bullets).
- ASSISTANT: one bullet per thing the assistant recommended/did/suggested.
- TOPICS: 3-5 comma-separated keywords.
- Do not paraphrase numbers away. Keep original wording for names.
- Output ONLY the card, no preamble.

Format:
USER FACTS:
- ...
ASSISTANT:
- ...
TOPICS: ...

Session:
{session}"""


def call_llm(prompt: str) -> str:
    for b in BACKOFF:
        try:
            r = requests.post(
                f"{API_BASE.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}",
                         "Content-Type": "application/json"},
                json={"model": MODEL,
                      "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 800, "temperature": 0.1,
                      # summarization needs no reasoning · 14s vs 120s+ per card
                      "thinking": {"type": "disabled"}},
                timeout=180)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(b); continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"] or ""
        except (requests.RequestException, KeyError):
            time.sleep(b)
    raise RuntimeError("LLM call exhausted backoff")


def load_cache() -> dict:
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    tmp.replace(CACHE)  # atomic · pkl-card死根因同款教训


def collect_unique_sessions(ds_path: Path) -> dict[str, list[dict]]:
    """session_id -> session turns, deduped across the 500-question pool."""
    data = json.loads(ds_path.read_text(encoding="utf-8"))
    uniq: dict[str, list[dict]] = {}
    for q in data:
        ids = q.get("haystack_session_ids", [])
        sess = q.get("haystack_sessions", [])
        for sid, s in zip(ids, sess):
            if sid not in uniq:
                uniq[sid] = s
    return uniq


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", type=Path,
                    default=Path(os.environ.get("ZMM_LONGMEMEVAL_PATH",
                                                str(DEFAULT_DS))))
    ap.add_argument("--limit", type=int, default=0, help="build only N (smoke)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--ids-file", type=Path, default=None,
                    help="only build sessions whose id is in this file "
                         "(one per line); derived from prior top5 retrieval")
    args = ap.parse_args()

    if not API_KEY:
        raise SystemExit("OPENAI_API_KEY not set (source ~/.claude/.cache/"
                         ".fde_api_secrets.env first)")

    uniq = collect_unique_sessions(args.dataset)
    if args.ids_file:
        wanted = {l.strip() for l in
                  args.ids_file.read_text(encoding="utf-8").splitlines() if l.strip()}
        missing = wanted - set(uniq)
        if missing:
            raise SystemExit(f"ids-file has {len(missing)} ids not in dataset "
                             f"(e.g. {sorted(missing)[:3]})")
        uniq = {sid: s for sid, s in uniq.items() if sid in wanted}
    cache = load_cache()
    # Invalidate stale entries if content changed (hash mismatch)
    todo = [sid for sid, s in uniq.items()
            if cache.get(sid, {}).get("hash") != content_hash(s)]
    if args.limit:
        todo = todo[:args.limit]
    print(f"unique sessions: {len(uniq)} · cached: {len(cache)} · todo: {len(todo)}")

    done = fail = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(call_llm, PROMPT.format(session=session_text(uniq[sid]))): sid
                for sid in todo}
        for fut in as_completed(futs):
            sid = futs[fut]
            try:
                card = fut.result().strip()
                if "USER FACTS" not in card:  # format sanity gate
                    card = "USER FACTS:\n" + card
                cache[sid] = {"hash": content_hash(uniq[sid]), "card": card,
                              "model": MODEL}
                done += 1
            except Exception as e:
                fail += 1
                print(f"  FAIL {sid}: {e}")
            if (done + fail) % 10 == 0:
                save_cache(cache)
                print(f"  {done} done / {fail} fail · {time.time()-t0:.0f}s",
                      flush=True)
    save_cache(cache)
    print(f"final: {done} new / {fail} fail · cache total {len(cache)} · "
          f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
