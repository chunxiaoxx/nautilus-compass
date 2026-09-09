#!/usr/bin/env python3
"""J4 全局回归门:三条冻结 fact 查询 hit@3 + 延迟(RSI 环 #1)。

判据正本: compass 仓 docs/plans/2026-09-09-rsi-trial1-preregistered.md
用法:
  python ops/regression_gate.py                    # 对照基线跑(无基线则只报告)
  python ops/regression_gate.py --save-baseline    # 改动前固化基线
连接生产 daemon(9876 · 只读)· 与代码 worktree 无关。
"""
from __future__ import annotations

import json
import socket
import sys
import time
from pathlib import Path

CASES = [
    ("9876 daemon ping 协议要求", "daemon-9876-watchdog-rootcause-20260908.md"),
    ("PyPI nautilus-compass 发布", "pypi-311-published-20260906.md"),
    ("LME-V2 451 题基准归属", "lmev2-upstream-attribution-20260902.md"),
]
PROJECT = "C--Users-chunx-Projects-nautilus-compass"
BASELINE = Path(__file__).parent / "regression_gate_baseline.json"


def daemon_req(req: dict, timeout: float = 60.0) -> dict:
    token = (Path.home() / ".claude" / ".cache"
             / "compass_daemon_token").read_text(encoding="utf-8").strip()
    req["token"] = token
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect(("127.0.0.1", 9876))
        s.sendall(json.dumps(req, ensure_ascii=False).encode("utf-8") + b"\n")
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
    line, _, _ = buf.partition(b"\n")
    return json.loads(line.decode("utf-8"))


def main() -> int:
    results, all_ok = [], True
    for q, expect in CASES:
        t0 = time.time()
        resp = daemon_req({"action": "recall", "query": q, "project": PROJECT, "top_k": 3})
        ms = (time.time() - t0) * 1000
        if not resp.get("ok"):
            print(f"  [ERR ] {q[:30]} → daemon error: {resp.get('error')}")
            return 2
        hits = [r["path"] for r in resp.get("recall") or []]
        ok = expect in hits
        all_ok &= ok
        results.append({"query": q, "expect": expect, "hits": hits,
                        "hit_at3": ok, "ms": round(ms, 1)})
        print(f"  [{'PASS' if ok else 'FAIL'}] {q[:32]} → hit@3={hits} ({ms:.0f}ms)")

    verdict = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "all_ok": all_ok, "cases": results}
    if "--save-baseline" in sys.argv:
        BASELINE.write_text(json.dumps(verdict, ensure_ascii=False, indent=1),
                            encoding="utf-8")
        print(f"\n基线已固化: {BASELINE}")
    elif BASELINE.exists():
        base = json.loads(BASELINE.read_text(encoding="utf-8"))
        for c0, c1 in zip(base.get("cases", []), results):
            if c0.get("hit_at3") and not c1["hit_at3"]:
                print(f"  REGRESSION: {c0['query'][:32]} 基线过 · 现在丢")
                all_ok = False

    print(f"\nJ4 gate: {'GREEN' if all_ok else 'RED'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
