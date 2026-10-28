#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读数收集器 · 快筛判定器的上游环(管道化 2026-10-27)

从 items 目录树收集 qwen/opus 读数 → 输出 quickscreen_verdict.py 兼容 JSON:
  {"CS-XXX": {"qwen3.8max": [1,0,...], "opus5.5": [1,...]}, ...}
单轮得分口径: tests 全对=1 否则=0(词典 v2 A 口径·轮二值,与快筛器一致)。

用法:
  python3 collect_for_quickscreen.py --items-dir <dir> [--items-dir <dir2> ...] > qs.json
  python3 collect_for_quickscreen.py --v5 --scratch   # 快捷: v5 items + compass 改造件 scratch
"""
import argparse, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s5_json import latest_batch as take_latest_batch, load_s5_json  # noqa: E402

HOME = Path.home()


def dirs_from_args(a):
    if a.v5:
        yield Path(HOME / "Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items")
    if a.scratch:
        yield Path("/tmp/cs_decoy_20261027/codesense/items")
        yield Path("/tmp/cs_decoy_509/codesense/items")
        yield Path("/tmp/cs004b/codesense/items")
        yield Path("/tmp/cs514b/codesense/items")  # 与 pipeline_report.SCRATCHES 对齐
    for d in a.items_dir:
        yield Path(d)


def is_empty_output(result: dict) -> bool:
    """F-016: 模型完结空输出(content empty),不是基建失败。

    content empty = 模型跑完没交补丁,按词典 v2 A 记 0。
    HTTP/urlopen/429/504 等基建失败仍返回 False,调用方跳过,避免把
    新批基建空窗当成「全 0」把旧批真读数冲掉(CS-004B 实证:4 份
    content empty 被当无读数跳过 → 旧批 0.4643 漏进 latest_batch)。
    """
    return str(result.get("error") or "").startswith("content empty")


def score_of(result: dict):
    """词典 v2 A 口径: 全对=1 否则=0。F-016: 完结空输出记 0,基建失败仍 None。"""
    s = result.get("score")
    if s is None:
        return 0.0 if is_empty_output(result) else None
    return 1.0 if s == 1.0 else 0.0


def collect(dirs, newer_than_hours=None, latest_batch=True):
    """F-009 纪律强化: 同题读数按 mtime 聚簇(间隔>1h 分批),默认只取**最新批**——
    跨时段读数永不混算(审计 A1 根修;简单时间窗不够,批次才是判读单位)。"""
    cutoff = time.time() - newer_than_hours * 3600 if newer_than_hours else 0
    raw: dict[str, dict[str, list]] = {}
    for d in dirs:
        if not d.exists():
            continue
        for item in sorted(d.glob("CS-*")):
            s5 = item / "_s5"
            if not s5.exists():
                continue
            ent = raw.setdefault(item.name, {"qwen3.8max": [], "opus5.5": []})
            for pat in ("qwen3.8max", "opus5.5"):
                for f in sorted(s5.glob(f"{pat}_run*_result.json")):
                    try:
                        mt = f.stat().st_mtime
                    except OSError:
                        continue
                    if mt < cutoff:
                        continue
                    r = load_s5_json(f)
                    if not r:
                        continue
                    sc = score_of(r)
                    if sc is not None:
                        ent[pat].append((mt, sc))
    out = {}
    for name, models in raw.items():
        ent = {}
        for pat, files in models.items():
            picked = take_latest_batch(files) if latest_batch else files
            ent[pat] = [sc for _, sc in picked]
        if ent["qwen3.8max"] or ent["opus5.5"]:
            out[name] = ent
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--items-dir", action="append", default=[])
    ap.add_argument("--v5", action="store_true")
    ap.add_argument("--scratch", action="store_true", help="compass 改造件 scratch(515B/509B/004B)")
    ap.add_argument("--newer-than-hours", type=float, default=0.0,
                    help="mtime 窗(小时);0=不过滤。跨时段不混算由 latest_batch 承担(F-010)")
    ap.add_argument("--selfcheck", action="store_true", help="F-016 score_of 断言,不收集")
    a = ap.parse_args()
    if a.selfcheck:
        assert score_of({"score": 1.0}) == 1.0
        assert score_of({"score": 0.4643}) == 0.0
        assert score_of({"score": None, "error": "content empty·reasoning_tail=x"}) == 0.0
        assert score_of({"score": None, "error": "HTTP Error 429: Too Many Requests"}) is None
        assert score_of({"score": None, "error": "<urlopen error [Errno 8] nodename"}) is None
        assert score_of({"score": None}) is None
        print("selfcheck ok")
        raise SystemExit(0)
    data = collect(list(dirs_from_args(a)), a.newer_than_hours)
    json.dump(data, sys.stdout, ensure_ascii=False, indent=1)
    print()
