#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MEMX 站3 · 因果倒置三向归因器 v0(R398)。

输入失败事件文本,对记忆库做两路探测(recall+dedup 宽扫),输出三向归因:
  A 记忆缺口   — recall 空 且 dedup unique      → 产出定向补写任务
  B 记忆错误   — recall 有命中但 fact_status 弱 → 产出降级+勘误任务
  C 检索失效   — recall 空但 dedup 命中(存在未召回)→ 产出 E1 调优信号
  NONE 非记忆因 — 命中且 fact_status=measured(行为层问题,出记忆域)
归因记录追加 runtime/memx/attributions.jsonl。判据零放宽:归因只分类,不改记忆。
"""
import argparse
import json
import socket
import sys
import time
from datetime import date
from pathlib import Path

TOKEN = (Path.home() / ".claude" / ".cache" / "compass_daemon_token").read_text(encoding="utf-8").strip()
PROJ = "C--Users-chunx-Projects-nautilus-compass"
OUT = Path(__file__).resolve().parent.parent / "runtime/memx/attributions.jsonl"
WEAK_STATUS = {"", "inferred", "heard"}


def daemon_req(payload: dict, timeout: float = 120.0) -> dict:
    payload = dict(payload, token=TOKEN)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect(("127.0.0.1", 9876))
        s.sendall(json.dumps(payload, ensure_ascii=False).encode("utf-8") + b"\n")
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
    return json.loads(buf.decode("utf-8"))


def classify(recall_hits: list, dedup: dict) -> tuple:
    """纯函数:两路探测结果 → (归因码, 任务列表)。可单测。
    相关性门限:recall 是 top-k 无阈值返回,低于 REL_MIN 的命中视为噪声不计。"""
    REL_MIN = 0.60
    relevant = [h for h in recall_hits if float(h.get("score") or 0) >= REL_MIN]
    dedup_verdict = dedup.get("verdict")
    if not relevant:
        if dedup_verdict in ("merge", "gray"):
            return "C", ["E1 调优信号:入库条目未被 recall 命中,查改写/嵌入差(入 held-out 集)"]
        return "A", ["定向补写任务:库内无相关先例,补写该失败模式的条目(dedup 后入)"]
    measured = [h for h in relevant if h.get("fact_status", "") == "measured"]
    if measured:
        return "NONE", ["非记忆因:相关命中含 measured 级条目(记忆有正确先例)——属行为层,转判读/流程线"]
    weak = "、".join(h.get("path", "?")[-40:] for h in relevant[:3])
    return "B", [f"降级+勘误任务:相关命中 fact_status 均弱({weak})——人工核后降级/修正(errata 通道)"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", help="失败事件描述文本")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        cases = [
            ([], {"verdict": "unique"}, "A"),
            ([], {"verdict": "gray"}, "C"),
            ([{"fact_status": "inferred", "path": "x.md", "score": 0.4}],
             {"verdict": "unique"}, "A"),  # 低分命中=噪声,仍判缺口
            ([{"fact_status": "inferred", "path": "x.md", "score": 0.8}],
             {"verdict": "gray"}, "B"),
            ([{"fact_status": "measured", "path": "x.md", "score": 0.8}],
             {"verdict": "unique"}, "NONE"),
            ([{"fact_status": "", "path": "x.md", "score": 0.9}],
             {"verdict": "merge"}, "B"),
        ]
        for hits, dedup, want in cases:
            got, _ = classify(hits, dedup)
            assert got == want, f"{hits}+{dedup.get('verdict')} => {got} != {want}"
        print(f"SELFTEST: PASS {len(cases)}/{len(cases)}")
        return 0
    if not args.event:
        print("--event required(或 --selftest)")
        return 2

    rec = daemon_req({"action": "recall", "project": PROJ, "query": args.event, "top_k": 5})
    if not rec.get("ok"):
        print("recall error:", rec.get("error"))
        return 1
    hits = rec.get("recall") or []
    dedup = daemon_req({"action": "dedup_check", "project": PROJ, "text": args.event,
                        "threshold_gray": "0.65"})
    code, tasks = classify(hits, dedup)
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "event": args.event[:300],
        "recall_n": len(hits),
        "recall_top": [(h.get("path", "")[-45:], h.get("fact_status", "")) for h in hits[:3]],
        "dedup_verdict": dedup.get("verdict"),
        "dedup_top": (dedup.get("hits") or [{}])[0].get("score"),
        "attribution": code,
        "tasks": tasks,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"ATTRIBUTION: {code} | recall_n={len(hits)} dedup={dedup.get('verdict')}")
    for t in tasks:
        print("  task:", t)
    print("->", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
