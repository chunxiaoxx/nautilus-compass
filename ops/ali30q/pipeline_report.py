#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""管道报告器 v0(甲方三门 + 快筛三判据 + 排产看板 · 2026-10-28)

每轮 loop 跑一次,输出:
  1. 逐候选题: 快筛三判据(22646) + 甲方三门(discrimination_jaccard) 合并判定
  2. 排产看板: 甲方 badpattern 配额 vs 现有候选 缺口矩阵 + 各题卡点 + 工时建议
落盘: v5 仓 codesense/runtime/pipeline_state/report.md(供各框循环消费)
"""
import json, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_for_quickscreen import score_of, SCRATCHES  # noqa: E402
from s5_json import latest_batch, load_s5_json  # noqa: E402

HOME = Path.home()
COMPASS = HOME / "Projects/nautilus-compass"
V5_ITEMS = HOME / "Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items"
OUT = HOME / "Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/runtime/pipeline_state"

# 候选题名单(交付候选池:快筛过筛或 CANDIDATE)
CANDIDATES = ["CS-513", "CS-007", "CS-303", "CS-507", "CS-511", "CS-105",
              "CS-004B", "CS-515B", "CS-202", "CS-203"]
# F-013: 队列 GOLD-PASS/施工题不在 CANDIDATES,但 latest_batch 退化会把历史金标冲掉
WATCH_DEGEN = ["CS-008", "CS-003", "CS-003B"]

def item_dirs(name):
    """所有存在的坐标(v5 items + scratch)。同名题可能拆在两个 scratch。"""
    found = []
    for f in [V5_ITEMS / name] + [s / name for s in SCRATCHES]:
        if f.exists() and f not in found:
            found.append(f)
    return found

def load_scores(dirs):
    """跨坐标合并读数(与 collect_for_quickscreen 同口径)。
    单目录 first-hit 会把「qwen=None 的 decoy」当成无读数(F-010)。
    F-011: 冲突 JSON 取 HEAD; F-009: 跨时段不混算。
    F-012/A7: 先跨目录合并再 latest_batch 一次,勿按目录各取最新再拼接。"""
    if isinstance(dirs, Path):
        dirs = [dirs]
    raw = {"qwen3.8max": [], "opus5.5": []}
    for item_dir in dirs:
        for m in raw:
            for f in sorted(item_dir.glob(f"_s5/{m}_run*_result.json")):
                d = load_s5_json(f)
                if not d:
                    continue
                sc = score_of(d)
                if sc is None:
                    continue
                try:
                    raw[m].append((f.stat().st_mtime, sc))
                except OSError:
                    continue
    return {m: [sc for _, sc in latest_batch(files)] for m, files in raw.items()}

def degen_batch_warnings():
    """F-013: 最新批 ≥3 模型原始分几乎相同且 <0.10 → 同仓退化批(非区分度)。"""
    warns = []
    for name in WATCH_DEGEN:
        dirs = item_dirs(name)
        if not dirs:
            continue
        raw: dict[str, list] = {}
        for item_dir in dirs:
            s5 = item_dir / "_s5"
            if not s5.exists():
                continue
            for f in sorted(s5.glob("*_result.json")):
                d = load_s5_json(f)
                if not d:
                    continue
                sc = d.get("score")
                if sc is None:
                    continue
                try:
                    scf = float(sc)
                    mt = f.stat().st_mtime
                except (TypeError, ValueError, OSError):
                    continue
                stem = f.name.split("_run")[0]
                raw.setdefault(stem, []).append((mt, scf))
        latest = {}
        for m, files in raw.items():
            batch = latest_batch(files)
            if batch:
                latest[m] = [sc for _, sc in batch]
        if len(latest) < 3:
            continue
        means = {m: sum(xs) / len(xs) for m, xs in latest.items()}
        # 至少 3 个模型均值彼此差 <1e-3 且都 <0.10
        cluster = []
        for m, v in means.items():
            if v < 0.10:
                cluster.append((m, round(v, 4)))
        if len(cluster) < 3:
            continue
        vs = [v for _, v in cluster]
        if max(vs) - min(vs) < 1e-3:
            models = ",".join(m for m, _ in cluster)
            warns.append(
                f"- ⚠ {name} 最新批退化: {models} 原始分≈{vs[0]} (≥3模型同分<0.10,疑同仓误跑;GOLD-PASS 勿被 latest_batch 冲掉)"
            )
    return warns


def richest_dir(dirs):
    """甲方三门仍吃单目录 ut_vector:优先有 qwen 二值读数,其次 opus,其次文件数。"""
    def key(d: Path):
        per = load_scores([d])
        n_files = len(list((d / "_s5").glob("*_result.json"))) if (d / "_s5").exists() else 0
        return (len(per["qwen3.8max"]), len(per["opus5.5"]), n_files)
    return max(dirs, key=key) if dirs else None

def quickscreen(per):
    q = per["qwen3.8max"]; o = per["opus5.5"]
    if not q: return None
    avg = sum(q) / len(q)
    c1 = 0 <= avg < 0.70
    # F-014 / 22646: c2 = opus **全** 1(不是 any)。审计原文「opus 不全 1」即此门。
    c2 = all(s == 1.0 for s in o) if o else None
    c3 = 0 < avg < 1.0
    return {"qwen_avg": round(avg, 3), "c1": c1, "c2": c2, "c3": c3,
            "pass": c1 and c2 and c3}

def client_gates(item_dir: Path):
    """甲方三门·只提 status(审计 A4)。按 JSON 抽字段,不靠 startswith 剥引号。"""
    r = subprocess.run([sys.executable, str(COMPASS / "ops/ali30q/discrimination_jaccard.py"),
                        str(item_dir)], capture_output=True, text=True, timeout=120)
    try:
        d = json.loads(r.stdout)
        parts = []
        for k in ("qwen_point", "sota_gap", "signature"):
            blk = d.get(k) or {}
            st = blk.get("status")
            if not st:
                continue
            # F-013: UNVERIFIED/FAIL 把缺口原因摊到看板;jaccard_note 只在其自身非 PASS 时用
            # F-015: signature 可能 jaccard_status=PASS 但 diversity/max_share 硬门 FAIL
            note = blk.get("reason") or ""
            if not note and k == "signature":
                bits = []
                if blk.get("diversity_pass") is False:
                    bits.append(f"diversity={blk.get('diversity')}<0.50")
                if blk.get("max_share_pass") is False:
                    bits.append(f"max_share={blk.get('max_share')}>0.50")
                if blk.get("jaccard_status") in ("UNVERIFIED", "FAIL"):
                    bits.append(blk.get("jaccard_note") or f"jaccard={blk.get('jaccard_status')}")
                note = "; ".join(bits)
            if st in ("UNVERIFIED", "FAIL") and note:
                parts.append(f"{k}={st}({note})")
            else:
                parts.append(f"{k}={st}")
        if d.get("overall"):
            parts.append(f"overall={d['overall']}")
        return "  " + " | ".join(parts) if parts else r.stdout.strip()[:120]
    except Exception:
        return r.stdout.strip()[:120]

def find_item(name):
    return richest_dir(item_dirs(name))

def main():
    import json as _json
    _lock = _json.load(open(HOME / "Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/runtime/pipeline_state/criteria_lock.json"))
    lines = ["# 管道报告(自动产 · " + __import__("time").strftime("%m-%d %H:%M") + ")",
             f"> 判据锁: {_lock.get('schema')}·sha16={_lock.get('self_sha16')}·冻结于{_lock.get('frozen_at','?')[:16]}——判据零放宽,变更须新版本",
             "> 证据分层: 本报告逐条结论按 [实测]/[推断]/[不可验] 标注;UNVERIFIED 处不猜", "",
             "## 候选题合并判定(快筛三判据 × 甲方三门)", ""]
    passing = []
    for name in CANDIDATES:
        dirs = item_dirs(name)
        if not dirs:
            lines.append(f"- {name}: ⚠ 目录未找到"); continue
        qs = quickscreen(load_scores(dirs))
        if qs is None:
            lines.append(f"- {name}: 无 qwen 读数"); continue
        d = richest_dir(dirs)
        extra = f"·dirs={len(dirs)}" if len(dirs) > 1 else ""
        qs_tag = ("✅过筛" if qs["pass"] else
                  (f"⏳候opus全1" if qs["c1"] and qs["c3"] and qs["c2"] is None else
                   (f"⏳opus门✗" if qs["c1"] and qs["c3"] else "❌未入带")))
        lines.append(
            f"### {name} — 快筛:{qs_tag} (qwen均值={qs['qwen_avg']}·c2opus全1={qs['c2']}{extra})"
        )
        cg = client_gates(d)
        lines.extend("  " + l for l in cg.split("\n") if l.strip())
        lines.append("")
        if qs["pass"]:
            passing.append(name)
    lines.append(f"## 快筛过筛 {len(passing)} 道: {', '.join(passing) or '无'}")
    degen = degen_batch_warnings()
    if degen:
        lines += ["", "## F-013 退化批哨兵"] + degen
    lines += ["", "## 排产缺口(甲方可交 = 快筛过筛 + 甲方三门全绿)",
              "- 目标 14 · 快筛过筛见上 · 甲方三门见逐题",
              "- 最大变量: 19 件深化(模板 ops/ali30q/DEEPEN_TEMPLATE.md 已投) + 判据裁决 + F-009 时段连跑", ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
