#!/usr/bin/env python3
"""FRAME.yaml 自动同步器(A1 工具化 · 2026-10-04 用户拍板)。

职责:从三处真源机械拼装 FRAME.yaml 动态字段,消灭手抄同步性 commit:
- waiting_on ← HANDOFF_*.md 在途时钟表(死线未过条目)
- deliverable ← git log 近 3 天 feat/docs 主件 subject
FRAME=对外快照;HANDOFF=交接(人写);queue=日志(轮次)。三档分工,一处真源派生。

用法:python scripts/frame_autosync.py          # 漂移检查+写出(有变才写)
      python scripts/frame_autosync.py --check  # 只查漂移(退出码 2=漂移)
"""
from __future__ import annotations

import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAME = ROOT / "FRAME.yaml"
HANDOFF = sorted(ROOT.glob("HANDOFF_*.md"))[-1] if ROOT.glob("HANDOFF_*.md") else None
TODAY = dt.date.today()


def waiting_on() -> str:
    if HANDOFF is None:
        return "(无 HANDOFF)"
    out = []
    for line in HANDOFF.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*\*(.+?)\*", line)
        d = re.search(r"\*?\*?(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2})", line)
        if not (m and d):
            continue
        raw = d.group(1)
        if "/" in raw:
            mo, dy = map(int, raw.split("/"))
            dl = dt.date(TODAY.year if mo <= TODAY.month else TODAY.year - 1, mo, dy)
        else:
            dl = dt.date.fromisoformat(raw)
        if dl >= TODAY:
            out.append(f"{m.group(1).strip('* ')[:40]}(死线{raw})")
    return "/".join(out[:5]) if out else "(无在途死线件)"


def deliverable() -> str:
    r = subprocess.run(
        ["git", "log", "--since=3.days", "--format=%s"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    subs = [s for s in r.stdout.splitlines()
            if s.startswith(("feat", "docs")) and "R8" not in s and "chore" not in s][:4]
    subs = [s[:70] for s in subs]
    return ";".join(subs) if subs else "(近3天无主件)"


def render() -> str:
    return (f"name: compass\n"
            f"status: active\n"
            f"waiting_on: {waiting_on()}\n"
            f"deliverable: {deliverable()}\n"
            f"# 由 scripts/frame_autosync.py 生成({dt.date.today()});手改会被覆盖,改 HANDOFF/queue 而非此处\n")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    new = render()
    old = FRAME.read_text(encoding="utf-8") if FRAME.exists() else ""
    core = lambda t: "\n".join(l for l in t.splitlines() if not l.startswith("#"))
    if core(old) == core(new):
        print("[ok] FRAME.yaml 无漂移")
        return 0
    if "--check" in sys.argv:
        print("[drift] FRAME.yaml 与真源不一致")
        return 2
    FRAME.write_text(new, encoding="utf-8")
    print(f"[updated] {FRAME.name}:\n{new}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
