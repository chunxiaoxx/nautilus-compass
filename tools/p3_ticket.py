#!/usr/bin/env python3
"""P3 S2 · 训练单生成器(触发门槛+预注册式训练单)。

设计档 §三:触发判据=delta 累计新增带白名单标签 ≥200(只许更严);
不足则本轮 SKIP 入 ledger,不攒人情。训练单 JSON=当轮 mini 预注册
(delta sha/基线 adapter/REG-100 sha/冻结超参/成本上限/判据引用)。
用法:python tools/p3_ticket.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "runtime" / "verdict_corpus"
DELTA = CORPUS / "delta"
P3 = ROOT / "runtime" / "judge_lora_p3"
LEDGER = P3 / "ledger.json"
GATE = 200
BASELINE_ADAPTER = ROOT / "runtime" / "judge_lora_p2v2" / "best_lora"
FROZEN_HPARAMS = {"lora_r": 16, "lora_alpha": 32, "seed": 20260930, "max_epochs": 5,
                  "verbalizer": "three_state_next_token", "replay_ratio": 1.0,
                  "replay_source": "split_train(冻结1162)",
                  "note": "承 P2v2 冻结配方;改配方=新预注册"}
COST_CAP_YUAN = 5.0


def sha16_path(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def load_ledger() -> list:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    return []


def append_ledger(entry: dict) -> None:
    led = load_ledger()
    led.append(entry)
    LEDGER.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> int:
    P3.mkdir(parents=True, exist_ok=True)
    deltas = sorted(DELTA.glob("delta_*.jsonl"))
    if not deltas:
        print("无 delta 批;SKIP")
        return 0
    cycle = len(load_ledger()) + 1
    total_new = 0
    parts = []
    for f in deltas:
        rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        total_new += len(rows)
        parts.append({"file": f.name, "n": len(rows), "sha16": sha16_path(f)})
    # cycle1=delta_0001 已由首轮人工记账(ledger.json 已含),从 cycle2 起只算未记账 delta
    ledger = load_ledger()
    accounted = {e.get("delta_id") for e in ledger}
    pending = [p for p in parts
               if p["file"] not in accounted
               and p["file"].rsplit(".", 1)[0] not in accounted]
    pending_n = sum(p["n"] for p in pending)
    ts = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    reg_m = CORPUS / "reg100_manifest.json"
    reg_sha = json.loads(reg_m.read_text(encoding="utf-8"))["reg100_sha16"] if reg_m.exists() else None
    entry = {"cycle": cycle, "ts": ts, "gate": f">={GATE} pending labelled",
             "pending_deltas": pending, "pending_n": pending_n,
             "evidence_tier": "measured"}
    if pending_n < GATE:
        entry.update({"ticket": "SKIP",
                      "verdict": f"SKIP——pending {pending_n}<{GATE},不攒人情不触发;"
                                 f"累计池 {total_new} 条(含已记账),流入速率以 ledger 为准"})
        append_ledger(entry)
        print(json.dumps(entry, ensure_ascii=False))
        return 0
    ticket = {
        "ticket_id": f"ticket_{cycle:04d}", "ts": ts, "status": "PENDING_APPROVAL",
        "pending_deltas": pending, "n_new": pending_n,
        "baseline_adapter": str(BASELINE_ADAPTER.relative_to(ROOT)),
        "baseline_adapter_sha16": sha16_path(BASELINE_ADAPTER / "adapter_model.safetensors"),
        "reg100_sha16": reg_sha,
        "hparams": FROZEN_HPARAMS, "cost_cap_yuan": COST_CAP_YUAN,
        "gates": "G1 REG-100 零 correct→incorrect 翻转 / G2 test149 acc≥85%+ECE≤0.10 / "
                 "G3 U 率±2pt(P3 设计档 §五,判据只许更严)",
        "reject_rule": "同 delta 重训限 2 次;修配方=断 20 连绿重新计数",
    }
    tf = P3 / f"ticket_{cycle:04d}.json"
    tf.write_text(json.dumps(ticket, ensure_ascii=False, indent=1), encoding="utf-8")
    entry.update({"ticket": "ISSUED", "ticket_file": tf.name})
    append_ledger(entry)
    print(json.dumps(entry, ensure_ascii=False))
    print(f"[save] {tf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
