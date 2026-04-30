#!/usr/bin/env python3
"""zenmind-mem feedback CLI · adaptive anchor learning loop (E).

Usage:
  feedback list                    # 列出最近 alerts (5 条)
  feedback log <alert_id> fp|tp    # 标 alert: false positive / true positive
  feedback retrain                 # 消费 feedback.jsonl · 生成 anchors_adapted.json
  feedback stats                   # 看 feedback 数据统计

Workflow:
  1. hook 触发 alert → log 到 .cache/usage.jsonl
  2. 用户标 alert: zenmind-mem feedback log a-12345678 fp
  3. 累计 ≥10 条 feedback 后跑 retrain
  4. retrain 生成 anchors_adapted.json (审过即可替换 anchors.json)

Design:
  · FP (false positive: alert 错了, prompt 实际 aligned)
    → 把这 prompt 加入 positive_anchors (反向训练)
    → 或: 看 max_neg_hit anchor 是否过敏感 · 高 FP rate anchor 标 deprecate
  · TP (true positive: alert 真) → 加入 negative_anchors (强化)
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

PLUGIN = Path.home() / ".claude" / "plugins" / "zenmind-mem"
USAGE_LOG = PLUGIN / ".cache/usage.jsonl"
FEEDBACK_LOG = PLUGIN / ".cache/feedback.jsonl"
ANCHORS_PATH = PLUGIN / "anchors.json"
ADAPTED_PATH = PLUGIN / "anchors_adapted.json"


def load_alerts() -> list[dict]:
    if not USAGE_LOG.exists():
        return []
    alerts = []
    with open(USAGE_LOG, encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("event") == "drift_alert" and rec.get("alert_id"):
                alerts.append(rec)
    return alerts


def load_feedback() -> dict:
    """Returns: {alert_id: verdict ('fp'/'tp')}."""
    if not FEEDBACK_LOG.exists():
        return {}
    out = {}
    with open(FEEDBACK_LOG, encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                out[rec["alert_id"]] = rec["verdict"]
            except Exception:
                continue
    return out


def cmd_list(args):
    alerts = load_alerts()
    feedback = load_feedback()
    pending = [a for a in alerts if a.get("alert_id") not in feedback]

    # v0.7.1 · active learning: --boundary 优先显示边界 case (score 在 [-0.05, 0.05] 之间)
    # 标这些比标 random 更高效 (5 条 boundary ≈ 50 条 random 提升 AUC)
    if args.boundary:
        # 先 sort by abs(score) ascending (距离阈值最近)
        pending = sorted(pending, key=lambda a: abs(a.get("score", 0)))
        print(f"=== drift alerts (boundary-sampled · top {args.limit} by ambiguity) ===\n")
    else:
        print(f"=== drift alerts: {len(alerts)} total · {len(feedback)} labeled · {len(pending)} pending ===\n")

    for a in pending[:args.limit] if args.boundary else pending[-args.limit:]:
        aid = a.get("alert_id", "?")
        score = a.get("score", 0)
        boundary_marker = " 🎯BOUNDARY" if abs(score) < 0.05 else ""
        print(f"[{aid}]  ts={a.get('ts', '?')[:19]}  score={score:+.3f}  cos={a.get('max_neg_hit', 0):.3f}{boundary_marker}")
        print(f"       neg_anchor: {a.get('neg_anchor', '?')[:80]}")
        print(f"       prompt: {(a.get('user_prompt') or a.get('query') or '?')[:100]}")
        print()


def cmd_log(args):
    if args.verdict not in ("fp", "tp"):
        print(f"❌ verdict 必须是 fp 或 tp", file=sys.stderr)
        sys.exit(1)
    rec = {
        "alert_id": args.alert_id,
        "verdict": args.verdict,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"✅ logged {args.alert_id} = {args.verdict}")


def cmd_stats(args):
    alerts = load_alerts()
    feedback = load_feedback()
    fp_n = sum(1 for v in feedback.values() if v == "fp")
    tp_n = sum(1 for v in feedback.values() if v == "tp")
    print(f"=== zenmind-mem feedback stats ===")
    print(f"  total alerts: {len(alerts)}")
    print(f"  labeled: {len(feedback)} ({fp_n} FP · {tp_n} TP)")
    if len(feedback) > 0:
        prec = tp_n / len(feedback)
        print(f"  precision = {prec:.3f}")
    # 按 anchor 统计 FP rate · 找过敏感的 anchor
    by_anchor = defaultdict(lambda: {"total": 0, "fp": 0, "tp": 0})
    for a in alerts:
        aid = a.get("alert_id")
        anc = (a.get("neg_anchor") or "")[:60]
        if not aid or not anc: continue
        by_anchor[anc]["total"] += 1
        if aid in feedback:
            by_anchor[anc][feedback[aid]] += 1
    if by_anchor:
        print(f"\n  per-anchor (≥1 labeled):")
        for anc, m in sorted(by_anchor.items(), key=lambda x: -(x[1]["fp"] / max(1, x[1]["total"]))):
            if m["total"] == 0: continue
            labeled = m["fp"] + m["tp"]
            if labeled == 0: continue
            print(f"    fp={m['fp']:2d}/labeled={labeled:2d} (total fired {m['total']:2d})  '{anc}'")


def _normalize_anchor(item):
    """Convert legacy str | new dict → unified dict."""
    if isinstance(item, str):
        return {"text": item, "weight": 1.0, "tp": 0, "fp": 0}
    return {
        "text": item.get("text", ""),
        "weight": float(item.get("weight", 1.0)),
        "tp": int(item.get("tp", 0)),
        "fp": int(item.get("fp", 0)),
    }


def _run_eval_drift(anchors_path: Path) -> float | None:
    """Run eval_drift.py with given anchors · return ROC AUC, or None if fail."""
    import subprocess as sp
    import re
    env = os.environ.copy()
    env["ZMM_ANCHORS_PATH_OVERRIDE"] = str(anchors_path)
    try:
        out = sp.run(
            [sys.executable, "-u", str(PLUGIN / "tests/eval_drift.py")],
            cwd=str(PLUGIN), env=env,
            capture_output=True, timeout=300, encoding="utf-8", errors="replace",
        )
        m = re.search(r"ROC AUC\s*=\s*([\d.]+)", out.stdout)
        return float(m.group(1)) if m else None
    except Exception as e:
        print(f"  eval failed: {e}", file=sys.stderr)
        return None


def cmd_retrain(args):
    alerts = load_alerts()
    feedback = load_feedback()
    if len(feedback) < args.min_feedback:
        print(f"⚠️ only {len(feedback)} labeled · 至少 {args.min_feedback} 条再 retrain")
        sys.exit(1)

    # Build alert_id → alert lookup
    alert_by_id = {a["alert_id"]: a for a in alerts if a.get("alert_id")}

    # Collect FP/TP grouped by anchor
    fp_prompts = []
    tp_prompts = []
    fp_anchor_count = defaultdict(int)
    tp_anchor_count = defaultdict(int)
    for aid, verdict in feedback.items():
        a = alert_by_id.get(aid)
        if not a: continue
        prompt = (a.get("user_prompt") or a.get("query") or "").strip()
        if not prompt: continue
        anchor_key = (a.get("neg_anchor") or "")[:60]
        if verdict == "fp":
            fp_prompts.append(prompt[:200])
            fp_anchor_count[anchor_key] += 1
        elif verdict == "tp":
            tp_prompts.append(prompt[:200])
            tp_anchor_count[anchor_key] += 1

    # Load + normalize existing anchors
    raw = json.loads(ANCHORS_PATH.read_text(encoding="utf-8"))
    pos = [_normalize_anchor(x) for x in raw["positive_anchors"]]
    neg = [_normalize_anchor(x) for x in raw["negative_anchors"]]

    # === v0.7.1 weighted update ===
    # neg anchor weight 调整: 每条 FP -> weight ×= 0.7, 每条 TP -> weight ×= 1.1 (cap [0.05, 2.0])
    # 连续 5 次 FP 后 weight ≤ 0.17 → 实际 deprecated (cosine 系数太低无影响)
    for n in neg:
        key = n["text"][:60]
        fp_n = fp_anchor_count.get(key, 0)
        tp_n = tp_anchor_count.get(key, 0)
        n["fp"] += fp_n
        n["tp"] += tp_n
        new_w = n["weight"] * (0.7 ** fp_n) * (1.1 ** tp_n)
        n["weight"] = round(max(0.05, min(2.0, new_w)), 3)

    # FP prompts → 加 positive_anchors (reinforce 它们是 aligned)
    existing_pos_text = {p["text"] for p in pos}
    for p in fp_prompts:
        if p not in existing_pos_text:
            pos.append({"text": p, "weight": 1.0, "tp": 1, "fp": 0})
    # TP prompts → 加 negative_anchors (reinforce 抓这些 pattern)
    existing_neg_text = {n["text"] for n in neg}
    for p in tp_prompts:
        if p not in existing_neg_text:
            neg.append({"text": p, "weight": 1.2, "tp": 1, "fp": 0})  # 新加的 anchor 起步 weight 1.2

    deprecated = [n["text"][:60] for n in neg if n["weight"] <= 0.17]

    out = {
        "comment": (
            f"v0.7.1 adapted from feedback (n={len(feedback)} labeled · "
            f"+{len(fp_prompts)} pos prompts +{len(tp_prompts)} neg prompts) · "
            f"{len(deprecated)} anchors weight-decayed below 0.17 (effectively deprecated)"
        ),
        "positive_anchors": pos,
        "negative_anchors": neg,
    }
    ADAPTED_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ wrote {ADAPTED_PATH}")
    print(f"   pos: {len(raw['positive_anchors'])} → {len(pos)} (+{len(fp_prompts)} from FP feedback)")
    print(f"   neg: {len(raw['negative_anchors'])} → {len(neg)} (+{len(tp_prompts)} from TP feedback)")
    print(f"   weight-decayed neg (≤0.17): {len(deprecated)}")
    for d in deprecated[:5]:
        print(f"     '{d}'")

    # === Eval gate ===
    if args.no_eval:
        print(f"\n⚠️ --no-eval skipped · 手动跑: python tests/eval_drift.py")
        return
    print(f"\n=== Eval gate · 跑 baseline AUC + adapted AUC 对比 ===")
    baseline_auc = _run_eval_drift(ANCHORS_PATH)
    adapted_auc = _run_eval_drift(ADAPTED_PATH)
    if baseline_auc is None or adapted_auc is None:
        print(f"❌ eval failed · adapted file 仍写出 · 手动验证")
        return
    delta = adapted_auc - baseline_auc
    print(f"  baseline AUC: {baseline_auc:.4f}")
    print(f"  adapted  AUC: {adapted_auc:.4f}  (Δ {delta:+.4f})")
    if delta < -0.01:
        print(f"\n🔴 REJECT: adapted retrogresses by {abs(delta):.3f} AUC. NOT shipping.")
        print(f"   review feedback labels · 可能用户标错了")
        return
    elif delta < 0.005:
        print(f"\n🟡 marginal: Δ AUC < 0.005 · 不强烈推荐 ship · 等更多 feedback")
    else:
        print(f"\n🟢 PROMOTE: Δ AUC = {delta:+.4f} 显著正向 · ship 命令:")
        print(f"  cp {ANCHORS_PATH} {ANCHORS_PATH}.bak.$(date +%Y%m%d-%H%M%S)")
        print(f"  mv {ADAPTED_PATH} {ANCHORS_PATH}")
        print(f"  rm {PLUGIN}/.cache/anchors.pkl")
        print(f"  bash {PLUGIN}/daemon_stop.sh && bash {PLUGIN}/daemon_start.sh")


def main():
    ap = argparse.ArgumentParser(prog="zenmind-mem-feedback")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="show pending alerts")
    p_list.add_argument("--limit", type=int, default=10)
    p_list.add_argument("--boundary", action="store_true",
                        help="active learning · prioritize alerts near decision boundary")

    p_log = sub.add_parser("log", help="label alert as fp/tp")
    p_log.add_argument("alert_id")
    p_log.add_argument("verdict", choices=("fp", "tp"))

    p_stats = sub.add_parser("stats", help="precision + per-anchor FP rate")

    p_retrain = sub.add_parser("retrain", help="weighted retrain + eval gate")
    p_retrain.add_argument("--min-feedback", type=int, default=5)
    p_retrain.add_argument("--no-eval", action="store_true",
                           help="skip eval_drift gate · 直接写 adapted")

    args = ap.parse_args()
    {"list": cmd_list, "log": cmd_log, "stats": cmd_stats, "retrain": cmd_retrain}[args.cmd](args)


if __name__ == "__main__":
    main()
