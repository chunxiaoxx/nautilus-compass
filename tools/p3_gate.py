#!/usr/bin/env python3
"""P3 S4 · 回归门判读器(G1 零翻转/G2 宪法地板/G3 U 守恒,纯 CPU)。

设计档 §五(判据预注册,只许更严):
  G1 零退化   REG-100 上 correct→incorrect 翻转数==0(逐条对照冠军)
  G2 宪法地板 test149 J1 binary acc≥0.85 且 J2 ECE(10bin)≤0.10
  G3 U 守恒   test149 U 预测率变化 ≤±2pt(对照冠军)
口径对齐 tools/train_judge_lora.py evaluate()(P2v2 冻结口径,门上不漂移):
  J1 = 金标非 U 子集上三词 softmax argmax 正确率;J2 = 全三态 confidence 10 等宽桶
  ECE,末桶含 1.0;pred/conf 由 S3 训练机产出,本脚本只判读。

输入:预测 JSONL 行={id, split:"reg100"|"test", pred:"pass"|"fail"|"insufficient_evidence", conf}
用法:python tools/p3_gate.py --champion preds.jsonl --challenger preds.jsonl
      --ticket runtime/judge_lora_p3/ticket_0001.json [--record]
输出:runtime/judge_lora_p3/gate_<ticket_id>.json + [--record 时] ledger 追加
自测:python tools/p3_gate.py --selftest
"""
from __future__ import annotations

import argparse
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
P3 = ROOT / "runtime" / "judge_lora_p3"
LABELS = ("pass", "fail", "insufficient_evidence")
U = "insufficient_evidence"
G1_MAX_FLIP = 0
G2_MIN_ACC, G2_MAX_ECE = 0.85, 0.10
G3_MAX_U_PT = 2.0
RETRAIN_LIMIT = 2


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def load_gold() -> tuple[dict, dict]:
    reg = {json.loads(l)["id"]: json.loads(l)["truth_label"]
           for l in (CORPUS / "reg100.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    test = {json.loads(l)["id"]: json.loads(l)["truth_label"]
            for l in (CORPUS / "split_test.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    return reg, test


def load_preds(p: Path) -> dict:
    out = {}
    for l in p.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            out[(r["split"], r["id"])] = (r["pred"], float(r.get("conf", 0.0)))
    return out


def ece_10bin(pairs: list[tuple[float, float]]) -> float:
    """pairs=(conf, correct 0/1);10 等宽桶,末桶含 1.0——对齐 P2v2 evaluate()。"""
    n = len(pairs)
    if n == 0:
        return 0.0
    e = 0.0
    for b in range(10):
        lo, hi = b / 10, (b + 1) / 10
        m = [k for k, (c, _) in enumerate(pairs) if lo <= c < hi + (1e-9 if b == 9 else 0)]
        if m:
            acc = sum(pairs[k][1] for k in m) / len(m)
            e += len(m) / n * abs(acc - sum(pairs[k][0] for k in m) / len(m))
    return e


def metrics(preds: dict, gold: dict, split: str) -> dict:
    tri_acc_pairs, n_ok = [], 0
    bin_ok = bin_n = 0
    u_pred = 0
    for (sp, sid), (pred, conf) in preds.items():
        if sp != split or sid not in gold:
            continue
        ok = pred == gold[sid]
        tri_acc_pairs.append((conf, 1.0 if ok else 0.0))
        n_ok += 1
        u_pred += pred == U
        if gold[sid] != U:
            bin_n += 1
            bin_ok += ok
    return {"n_scored": n_ok,
            "tri_acc": round(sum(c for _, c in tri_acc_pairs) / n_ok, 4) if n_ok else None,
            "ece_10bin": round(ece_10bin(tri_acc_pairs), 4),
            "binary_acc": round(bin_ok / bin_n, 4) if bin_n else None,
            "binary_n": bin_n,
            "u_rate_pt": round(100.0 * u_pred / n_ok, 2) if n_ok else None}


def run_gate(champ_f: Path, chall_f: Path) -> dict:
    gold_reg, gold_test = load_gold()
    champ, chall = load_preds(champ_f), load_preds(chall_f)
    # G1:REG-100 逐条对照,correct→incorrect 翻转
    flips = []
    for (sp, sid), (cp, _) in champ.items():
        if sp != "reg100" or sid not in gold_reg:
            continue
        q = chall.get((sp, sid))
        if q is None:
            flips.append({"id": sid, "error": "challenger 缺帧"})
            continue
        if cp == gold_reg[sid] and q[0] != gold_reg[sid]:
            flips.append({"id": sid, "champion": cp, "challenger": q[0], "gold": gold_reg[sid]})
    m_champ_t = metrics(champ, gold_test, "test")
    m_chall_t = metrics(chall, gold_test, "test")
    g1 = {"flips": flips, "n_flips": len(flips), "max_allowed": G1_MAX_FLIP,
          "pass": len(flips) <= G1_MAX_FLIP}
    g2 = {"challenger_binary_acc": m_chall_t["binary_acc"], "min_acc": G2_MIN_ACC,
          "challenger_ece": m_chall_t["ece_10bin"], "max_ece": G2_MAX_ECE,
          "pass": (m_chall_t["binary_acc"] or 0) >= G2_MIN_ACC
                  and m_chall_t["ece_10bin"] <= G2_MAX_ECE}
    du = (m_chall_t["u_rate_pt"] - m_champ_t["u_rate_pt"]) if \
        m_chall_t["u_rate_pt"] is not None and m_champ_t["u_rate_pt"] is not None else None
    g3 = {"champion_u_rate_pt": m_champ_t["u_rate_pt"], "challenger_u_rate_pt": m_chall_t["u_rate_pt"],
          "delta_pt": round(du, 2) if du is not None else None, "max_pt": G3_MAX_U_PT,
          "pass": du is not None and abs(du) <= G3_MAX_U_PT}
    passed = g1["pass"] and g2["pass"] and g3["pass"]
    return {"gates": {"G1_zero_flip": g1, "G2_constitution_floor": g2, "G3_u_conservation": g3},
            "metrics_champion_test": m_champ_t, "metrics_challenger_test": m_chall_t,
            "regression_only_upgrades": sum(
                1 for (sp, sid), (cp, _) in champ.items()
                if sp == "reg100" and sid in gold_reg and cp != gold_reg[sid]
                and chall.get((sp, sid), (None,))[0] == gold_reg[sid]),
            "verdict": "PASS" if passed else "FAIL",
            "verdict_note": ("三门全绿,可提交 S5 上岗" if passed else
                             "FAIL——挑战者入 rejected/,冠军不动;修配方重训=新 cycle,"
                             f"同 delta 刷门限 {RETRAIN_LIMIT} 次")}


def selftest() -> int:
    """合成三场景:全同 PASS / 含翻转 FAIL / U 漂移 FAIL。"""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    reg, test = load_gold()

    def write_preds(path: Path, mutate=None, u_mutate=None):
        rows = []
        for sid, g in reg.items():
            pred, conf = g, 0.9
            if mutate:
                pred, conf = mutate(sid, g)
            rows.append({"split": "reg100", "id": sid, "pred": pred, "conf": conf})
        for sid, g in test.items():
            pred, conf = g, 0.9
            if u_mutate:
                pred, conf = u_mutate(sid, g)
            rows.append({"split": "test", "id": sid, "pred": pred, "conf": conf})
        path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    # 场景1:挑战者=冠军 → PASS
    write_preds(tmp / "a.jsonl")
    write_preds(tmp / "b.jsonl")
    r1 = run_gate(tmp / "a.jsonl", tmp / "b.jsonl")
    assert r1["verdict"] == "PASS", r1
    # 场景2:一帧 correct→incorrect → G1 FAIL
    bad = [sid for sid, g in reg.items() if g != "fail"][0]
    write_preds(tmp / "c.jsonl", mutate=lambda sid, g: ("fail", 0.9) if sid == bad else (g, 0.9))
    r2 = run_gate(tmp / "a.jsonl", tmp / "c.jsonl")
    assert r2["verdict"] == "FAIL" and r2["gates"]["G1_zero_flip"]["n_flips"] == 1, r2
    # 场景3:U 率 +5pt → G3 FAIL
    some = [sid for sid, g in test.items() if g != U][:10]
    r3 = run_gate(tmp / "a.jsonl", write_preds_ret(tmp, "d.jsonl",
                  u_mutate=lambda sid, g: (U, 0.4) if sid in some else (g, 0.9)))
    assert r3["verdict"] == "FAIL" and not r3["gates"]["G3_u_conservation"]["pass"], r3
    print("selftest 3/3 PASS(全同 PASS/单帧翻转 FAIL/U 漂移 FAIL)")
    return 0


def write_preds_ret(tmp: Path, name: str, mutate=None, u_mutate=None) -> Path:
    reg, test = load_gold()
    rows = [{"split": "reg100", "id": sid, "pred": g, "conf": 0.9} for sid, g in reg.items()]
    for sid, g in test.items():
        pred, conf = (u_mutate(sid, g) if u_mutate else (g, 0.9))
        rows.append({"split": "test", "id": sid, "pred": pred, "conf": conf})
    p = tmp / name
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--champion", type=Path)
    ap.add_argument("--challenger", type=Path)
    ap.add_argument("--ticket", type=Path)
    ap.add_argument("--record", action="store_true", help="结果入 ledger")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.champion and a.challenger):
        ap.error("--champion/--challenger 必填(或 --selftest)")
    r = run_gate(a.champion, a.challenger)
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
           "gate_version": "p3_gate_v1(P3 设计档 §五,判据只许更严)",
           "champion_sha16": sha16(a.champion), "challenger_sha16": sha16(a.challenger),
           "ticket_id": a.ticket.name if a.ticket else None, **r,
           "evidence_tier": "measured"}
    f = P3 / f"gate_{a.ticket.name.replace('.json', '') if a.ticket else 'adhoc'}.json"
    f.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.record and a.ticket:
        led_f = P3 / "ledger.json"
        led = json.loads(led_f.read_text(encoding="utf-8")) if led_f.exists() else []
        led.append({"cycle": len(led) + 1, "ts": out["ts"], "event": "GATE",
                    "ticket": a.ticket.name, "verdict": r["verdict"],
                    "n_flips": r["gates"]["G1_zero_flip"]["n_flips"],
                    "binary_acc": r["metrics_challenger_test"]["binary_acc"],
                    "ece": r["metrics_challenger_test"]["ece_10bin"],
                    "evidence_tier": "measured"})
        led_f.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:1200])
    print(f"[save] {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
