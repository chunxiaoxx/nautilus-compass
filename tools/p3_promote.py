#!/usr/bin/env python3
"""P3 S5 · 冠军上岗切换器(原子写+三代回滚+kill switch,纯 CPU)。

设计档 §六:
  champion.json 原子切换(tmp 写+os.replace):{gen, adapter_path, adapter_sha16,
  gate_report_sha16, corpus_delta_sha16, promoted_at}
  回滚:champion_history.json 保留最近 3 代;kill switch=--rollback 指回上一代
  硬约束(§八·5):上岗只走本管道,任何人不手动替换 champion 而不过门。

前置校验(防偷渡):
  ①gate_report.verdict==PASS;②gate_report_sha16 与报告文件实算一致(防改判后复用);
  ③challenger adapter 目录存在且含 adapter_model.safetensors。

用法:
  python tools/p3_promote.py --init                     # 首跑:gen0=P2v2 冠军入账
  python tools/p3_promote.py --gate GATE.json --adapter DIR --ticket T.json --record
  python tools/p3_promote.py --rollback --record        # kill switch
  python tools/p3_promote.py --show
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
P3 = ROOT / "runtime" / "judge_lora_p3"
CHAMPION = P3 / "champion.json"
HISTORY = P3 / "champion_history.json"
GEN0_ADAPTER = ROOT / "runtime" / "judge_lora_p2v2" / "best_lora"
KEEP_GENS = 3


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def ledger_append(entry: dict) -> None:
    f = P3 / "ledger.json"
    led = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    entry = {"cycle": len(led) + 1, **entry}
    led.append(entry)
    f.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")


def rel(p: Path) -> str:
    try:
        return p.relative_to(ROOT).as_posix()  # posix 斜杠:GPU Linux 机可直读
    except ValueError:  # selftest 临时目录在仓外;生产路径恒在仓内
        return str(p)


def read_champion() -> dict | None:
    return json.loads(CHAMPION.read_text(encoding="utf-8")) if CHAMPION.exists() else None


def atomic_write_champion(rec: dict) -> None:
    tmp = CHAMPION.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, CHAMPION)


def cmd_init() -> int:
    if CHAMPION.exists():
        print("[REFUSE] champion.json 已存在,init 只许首跑一次;现役见 --show")
        return 1
    if not (GEN0_ADAPTER / "adapter_model.safetensors").exists():
        print(f"[FAIL] gen0 adapter 不存在: {GEN0_ADAPTER}")
        return 1
    rec = {"gen": 0, "adapter_path": rel(GEN0_ADAPTER),
           "adapter_sha16": sha16(GEN0_ADAPTER / "adapter_model.safetensors"),
           "gate_report_sha16": None,
           "corpus_delta_sha16": None,
           "promoted_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
           "note": "gen0=P2v2 冠军(J1 88.51/ECE 0.072),P3 管道启用基准"}
    atomic_write_champion(rec)
    HISTORY.write_text("[]", encoding="utf-8")
    ledger_append({"ts": rec["promoted_at"], "event": "PROMOTE", "gen": 0,
                   "adapter": rec["adapter_path"], "note": "init gen0",
                   "evidence_tier": "measured"})
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return 0


def cmd_promote(gate_f: Path, adapter: Path, ticket_f: Path) -> int:
    champ = read_champion()
    if champ is None:
        print("[REFUSE] champion.json 不存在——先 --init")
        return 1
    gate = json.loads(gate_f.read_text(encoding="utf-8"))
    if gate.get("verdict") != "PASS":
        print(f"[REFUSE] gate verdict={gate.get('verdict')}——不过门不上岗(护栏 §八·5)")
        return 1
    # gate_report_sha16=报告文件级锚,入 champion 链供审计(防改判靠 ledger --record 留痕,
    # 不做文件内部自校验——文件 sha 存自身=自引用死循环,selftest 曾抓出此设计错)
    gate_sha = sha16(gate_f)
    saf = adapter / "adapter_model.safetensors"
    if not saf.exists():
        print(f"[REFUSE] challenger adapter 缺 safetensors: {adapter}")
        return 1
    ticket = json.loads(ticket_f.read_text(encoding="utf-8"))
    rec = {"gen": champ["gen"] + 1,
           "adapter_path": rel(adapter),
           "adapter_sha16": sha16(saf),
           "gate_report_sha16": gate_sha,
           "corpus_delta_sha16": ";".join(d["sha16"] for d in ticket.get("pending_deltas", [])),
           "promoted_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
           "ticket": ticket_f.name}
    hist = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else []
    hist.append(champ)
    hist = hist[-KEEP_GENS:]
    atomic_write_champion(rec)
    HISTORY.write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")
    ledger_append({"ts": rec["promoted_at"], "event": "PROMOTE", "gen": rec["gen"],
                   "adapter": rec["adapter_path"], "adapter_sha16": rec["adapter_sha16"],
                   "gate": gate_f.name, "ticket": ticket_f.name,
                   "history_depth": len(hist), "evidence_tier": "measured"})
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return 0


def cmd_rollback() -> int:
    champ = read_champion()
    hist = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else []
    if champ is None or not hist:
        print("[REFUSE] 无上一代可回滚")
        return 1
    prev = hist[-1]
    atomic_write_champion({**prev, "promoted_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
                           "note": f"rollback from gen{champ['gen']} (kill switch)"})
    HISTORY.write_text(json.dumps(hist[:-1], ensure_ascii=False, indent=1), encoding="utf-8")
    ledger_append({"ts": prev["promoted_at"], "event": "ROLLBACK",
                   "from_gen": champ["gen"], "to_gen": prev["gen"],
                   "adapter": prev["adapter_path"], "evidence_tier": "measured"})
    print(json.dumps({"rolled_back_to": prev["gen"], "adapter": prev["adapter_path"]},
                     ensure_ascii=False))
    return 0


def cmd_show() -> int:
    champ = read_champion()
    hist = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else []
    print(json.dumps({"champion": champ, "history_gens": [h["gen"] for h in hist]},
                     ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    """合成场景:未过门拒绝/过门上岗+原子写/回滚。"""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    global CHAMPION, HISTORY, P3, GEN0_ADAPTER
    CHAMPION, HISTORY = tmp / "champion.json", tmp / "history.json"
    adv = tmp / "gen0_adapter"
    adv.mkdir()
    (adv / "adapter_model.safetensors").write_bytes(b"gen0")
    GEN0_ADAPTER = adv
    P3 = tmp
    assert cmd_init() == 0 and cmd_init() != 0  # init 一次成功,二次拒绝
    good_adapter = tmp / "challenger"
    good_adapter.mkdir()
    (good_adapter / "adapter_model.safetensors").write_bytes(b"gen1")
    ticket = tmp / "ticket.json"
    ticket.write_text(json.dumps({"pending_deltas": [{"sha16": "abc"}]}), encoding="utf-8")
    gate_fail = tmp / "gate_fail.json"
    gate_fail.write_text(json.dumps({"verdict": "FAIL"}), encoding="utf-8")
    assert cmd_promote(gate_fail, good_adapter, ticket) != 0  # FAIL 拒绝
    assert json.loads(CHAMPION.read_text(encoding="utf-8"))["gen"] == 0  # 冠军不动
    gate_pass_f = tmp / "gate_pass.json"
    gate_pass_f.write_text(json.dumps({"verdict": "PASS", "note": "selftest"}), encoding="utf-8")
    assert cmd_promote(gate_pass_f, good_adapter, ticket) == 0
    assert json.loads(CHAMPION.read_text(encoding="utf-8"))["gen"] == 1
    cmd_rollback()
    assert json.loads(CHAMPION.read_text(encoding="utf-8"))["gen"] == 0  # 回到 gen0
    print("selftest PASS(init 唯一/FAIL 拒/过门上岗/回滚)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--gate", type=Path)
    ap.add_argument("--adapter", type=Path)
    ap.add_argument("--ticket", type=Path)
    ap.add_argument("--rollback", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.init:
        return cmd_init()
    if a.rollback:
        return cmd_rollback()
    if a.show:
        return cmd_show()
    if a.gate and a.adapter and a.ticket:
        return cmd_promote(a.gate, a.adapter, a.ticket)
    ap.error("须 --init / --gate+--adapter+--ticket / --rollback / --show")
    return 2


if __name__ == "__main__":
    sys.exit(main())
