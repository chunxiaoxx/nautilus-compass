#!/usr/bin/env python3
"""Reproduce the local rerank latency/recall trade-off without changing prod config.

The benchmark reads the same locally gated memory directory as Compass, builds
one dense candidate order, and sends that identical candidate order to the
same-host MPS reranker with several context/candidate settings. It is a probe,
not an acceptance claim: expected-card hit@5 and config overlap are useful
signals, while customer or LongMemEval acceptance needs a separate fixed set.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import socket
import sys
import time
from pathlib import Path

# Keep this benchmark on the local embed proxy and never start a second daemon.
os.environ.setdefault("COMPASS_EMBED_PROXY", "http://127.0.0.1:8400")
os.environ.setdefault("COMPASS_PROD_RERANK", "0")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import daemon  # noqa: E402


PROJECT = "-Users-chunxiao-wang-Projects-nautilus-compass"
MEMORY_DIR = Path.home() / ".claude" / "projects" / PROJECT / "memory"
RERANK_TOKEN = Path.home() / "bge-embed" / "rerank_token"

CASES = [
    ("召回噪声 distill 污染", "recall-noise-76pct-distill-pollution-20261117.md"),
    ("记忆库噪声计数口径", "memory-counting-basis-noise-cards-r572-20261118.md"),
    ("Compass CI lint 回归修复", "ci-lint-regression-r573-20261119.md"),
    ("Mac mini rerank 迁移", "rerank-macmini-migration-r561.md"),
    ("HF NFS 缓存召回故障", "recall-down-nfs-hf-cache-20261118.md"),
    ("cloud BGE daemon 停用", "cloud-bge-daemon-stopped-20261107.md"),
    ("BGE 模型选择对拍", "emb-bakeoff-bge-stays-20260925.md"),
    ("Compass MCP dogfood bridge", "session-contract-dogfood-bridge-20260822.md"),
    ("daemon pylibs 根因", "compass-daemon-pylibs-rootcause-20260830.md"),
    ("Compass 四优先级路线", "compass-strategy-four-priorities-20260910.md"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rpc(request: dict, timeout: float = 90.0) -> dict:
    token = RERANK_TOKEN.read_text(encoding="utf-8").strip()
    request = dict(request, token=token)
    with socket.create_connection(("127.0.0.1", 8401), timeout=10) as conn:
        conn.sendall((json.dumps(request, ensure_ascii=False) + "\n").encode())
        conn.settimeout(timeout)
        buf = bytearray()
        while b"\n" not in buf:
            chunk = conn.recv(65536)
            if not chunk:
                break
            buf.extend(chunk)
    return json.loads(bytes(buf).split(b"\n", 1)[0])


def rerank(query: str, candidates: list[tuple[float, dict]], max_length: int) -> tuple[list[dict], float, dict]:
    docs = [entry.get("embed_text") or entry.get("description") or "" for _, entry in candidates]
    started = time.perf_counter()
    response = rpc({
        "action": "rerank",
        "query": query,
        "docs": docs,
        "max_length": max_length,
        "activation": "sigmoid",
        "batch_size": 4,
    })
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    if not response.get("ok"):
        raise RuntimeError(response.get("error", "rerank failed"))
    scores = response.get("scores") or []
    if len(scores) != len(candidates):
        raise RuntimeError(f"score count {len(scores)} != candidates {len(candidates)}")
    ordered = [entry for (_, entry), _ in sorted(zip(candidates, scores), key=lambda pair: -float(pair[1]))]
    return ordered[:5], elapsed_ms, {
        "server_ms": response.get("ms"),
        "device": response.get("device"),
        "revision": response.get("revision"),
        "max_length": response.get("max_length"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path,
                        default=Path("runtime/cross-dialog-receipts/20261119-rerank-ab.json"))
    args = parser.parse_args()
    if not MEMORY_DIR.is_dir():
        raise SystemExit(f"memory directory missing: {MEMORY_DIR}")

    entries = daemon.get_memory_entries(MEMORY_DIR)
    entries = [entry for entry in entries if entry.get("embedding")]
    embedder = daemon.get_embedder()
    health = rpc({"action": "health"})
    if not health.get("ok"):
        raise SystemExit(f"reranker health failed: {health}")

    configs = {
        "dense": None,
        "30x8192": (30, 8192),
        "30x512": (30, 512),
        "16x512": (16, 512),
    }
    rows = []
    for query, expected in CASES:
        query_vec = embedder.encode(query)
        dense = [(float(score), entry) for score, entry in zip(
            daemon.cosine_batch(query_vec, [entry["embedding"] for entry in entries]), entries)]
        dense.sort(key=lambda pair: -pair[0])
        eligible_names = {entry["path"] for _, entry in dense}
        row = {
            "query": query,
            "expected": expected,
            "expected_available": expected in eligible_names,
            "configs": {},
        }
        for name, spec in configs.items():
            if spec is None:
                ordered = [entry for _, entry in dense[:5]]
                elapsed_ms = None
                meta = {"candidate_count": 5, "max_length": None}
            else:
                candidate_count, max_length = spec
                ordered, elapsed_ms, meta = rerank(query, dense[:candidate_count], max_length)
                meta.update({"candidate_count": candidate_count, "max_length": max_length})
            names = [entry["path"] for entry in ordered]
            row["configs"][name] = {
                "top5": names,
                "expected_rank": names.index(expected) + 1 if expected in names else None,
                "hit_at_5": expected in names,
                "elapsed_ms": elapsed_ms,
                "meta": meta,
            }
        rows.append(row)

    def hit_rate(name: str, available_only: bool = False) -> float | None:
        selected = [row for row in rows if row["expected_available"]] if available_only else rows
        if not selected:
            return None
        return round(sum(row["configs"][name]["hit_at_5"] for row in selected) / len(selected), 4)

    def median_latency(name: str) -> float | None:
        vals = sorted(row["configs"][name]["elapsed_ms"] for row in rows
                      if row["configs"][name]["elapsed_ms"] is not None)
        return round(vals[len(vals) // 2], 2) if vals else None

    result = {
        "schema": "compass-rerank-ab/1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project": PROJECT,
        "memory_dir": str(MEMORY_DIR),
        "memory_dir_sha256_unavailable": True,
        "eligible_entries": len(entries),
        "reranker_health": {k: health.get(k) for k in (
            "model", "device", "revision", "max_length_supported", "batch_size_limit")},
        "cases": len(rows),
        "summary": {
            name: {
                "hit_at_5_all_cases": hit_rate(name),
                "hit_at_5_when_expected_card_is_eligible": hit_rate(name, available_only=True),
                "median_server_elapsed_ms": median_latency(name),
            }
            for name in configs
        },
        "expected_card_coverage": {
            "available": sum(row["expected_available"] for row in rows),
            "unavailable_due_to_memory_gate": sum(not row["expected_available"] for row in rows),
        },
        "interpretation": "Hit@5 uses expected local memory cards as a regression signal; it is not customer or LongMemEval acceptance.",
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "summary": result["summary"], "eligible_entries": len(entries)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
