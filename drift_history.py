"""compass v0.8 · 🆕#1 Drift timeline · ASCII 可视化 AI 漂移历史.

claude-mem 没有的能力 — 让用户看 AI 在哪段 session 开始偏离意图.

Usage:
  python drift_history.py [days=30] [--project NAME] [--top N]

Output:
  · 总体 green/yellow/red 计数
  · 按日 ASCII timeline (· · ! · X)
  · TOP red sessions 详情 (含 drift_signals)
"""
from __future__ import annotations

import io
import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except Exception:
    pass

PROJECTS = Path.home() / ".claude" / "projects"


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    fm: dict = {}
    in_signals = False
    signals: list[str] = []
    for line in text[4:end].splitlines():
        if in_signals:
            m = re.match(r"\s*-\s*(.+)", line)
            if m:
                signals.append(m.group(1).strip().strip('"').strip("'"))
                continue
            in_signals = False
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip(); v = v.strip()
            if k == "drift_signals":
                if v == "[]" or v == "":
                    in_signals = True if not v else False
                    fm["drift_signals"] = [] if v == "[]" else []
                elif v.startswith("["):
                    inner = v.strip("[]")
                    if inner:
                        fm["drift_signals"] = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
                    else:
                        fm["drift_signals"] = []
                else:
                    fm["drift_signals"] = [v.strip('"').strip("'")]
            else:
                fm[k] = v.strip('"').strip("'")
    if signals and "drift_signals" in fm and not fm["drift_signals"]:
        fm["drift_signals"] = signals
    return fm


def collect_sessions(days: int, project_filter: str | None = None) -> list[dict]:
    cutoff = (datetime.now() - timedelta(days=days)).timestamp()
    rows = []
    if not PROJECTS.exists():
        return rows
    for proj in PROJECTS.iterdir():
        if not proj.is_dir():
            continue
        if project_filter and project_filter not in proj.name:
            continue
        memdir = proj / "memory"
        if not memdir.exists():
            continue
        for f in memdir.glob("session_*.md"):
            try:
                mtime = f.stat().st_mtime
                if mtime < cutoff:
                    continue
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            fm = parse_frontmatter(text)
            rows.append({
                "path": f,
                "project": proj.name,
                "mtime": mtime,
                "name": fm.get("name", "?"),
                "drift": fm.get("drift", "?"),
                "drift_signals": fm.get("drift_signals", []),
                "type": fm.get("type", "?"),
                "concept": fm.get("concept", "?"),
            })
    return sorted(rows, key=lambda r: r["mtime"])


GLYPH = {"green": "·", "yellow": "!", "red": "X", "?": "?"}
COLOR = {"green": "\033[32m", "yellow": "\033[33m", "red": "\033[31m", "?": "\033[37m"}
RESET = "\033[0m"


def print_summary(rows: list[dict], days: int):
    if not rows:
        print(f"No sessions in last {days} days")
        return
    counts = Counter(r["drift"] for r in rows)
    total = len(rows)
    drift_pct = lambda c: f"{100*c/total:.0f}%" if total else "0%"
    print(f"\n📊 Drift History · last {days}d · {total} sessions across {len(set(r['project'] for r in rows))} projects\n")
    print(f"  {COLOR['green']}● green{RESET}   {counts.get('green',0):3d}  {drift_pct(counts.get('green',0))}  AI 一次到位")
    print(f"  {COLOR['yellow']}● yellow{RESET}  {counts.get('yellow',0):3d}  {drift_pct(counts.get('yellow',0))}  小绕弯及时纠正")
    print(f"  {COLOR['red']}● red{RESET}     {counts.get('red',0):3d}  {drift_pct(counts.get('red',0))}  偏离意图 · 反复犯错")
    if counts.get("?", 0):
        print(f"  ● ?       {counts.get('?',0):3d}  {drift_pct(counts.get('?',0))}  无 drift 字段 (老格式)")


def print_timeline(rows: list[dict]):
    if not rows:
        return
    by_day: dict[str, list[str]] = {}
    for r in rows:
        d = datetime.fromtimestamp(r["mtime"]).strftime("%m-%d")
        by_day.setdefault(d, []).append(r["drift"])
    print("\n📅 Daily timeline (· green · ! yellow · X red · ? unknown)\n")
    for d in sorted(by_day):
        glyphs = "".join(f"{COLOR.get(x,'')}{GLYPH.get(x,'?')}{RESET}" for x in by_day[d])
        print(f"  {d}  {glyphs}  ({len(by_day[d])})")


def print_red_details(rows: list[dict], top: int = 5):
    reds = [r for r in rows if r["drift"] == "red"]
    if not reds:
        print(f"\n✅ No RED sessions · 漂移可控")
        return
    reds.sort(key=lambda r: r["mtime"], reverse=True)
    print(f"\n🚨 {len(reds)} RED sessions (showing top {min(top, len(reds))} most recent):\n")
    for r in reds[:top]:
        ts = datetime.fromtimestamp(r["mtime"]).strftime("%m-%d %H:%M")
        print(f"  {COLOR['red']}● {ts}{RESET}  [{r['project']}]  {r['name']}")
        for sig in r.get("drift_signals", []):
            if sig:
                print(f"      · {sig}")
        print(f"      → {r['path'].name}\n")


def print_yellow_signals_summary(rows: list[dict], top_signals: int = 5):
    yellows = [r for r in rows if r["drift"] == "yellow"]
    if not yellows:
        return
    sigs = []
    for r in yellows:
        sigs.extend(s for s in r.get("drift_signals", []) if s)
    if not sigs:
        return
    print(f"\n⚠️ Top yellow signals (n={len(yellows)} sessions · {len(sigs)} signals)\n")
    for sig, count in Counter(sigs).most_common(top_signals):
        print(f"  {count}× · {sig}")


def main():
    days = 30
    project_filter = None
    top = 5
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i].startswith("--project"):
            i += 1
            project_filter = args[i] if i < len(args) else None
        elif args[i].startswith("--top"):
            i += 1
            top = int(args[i]) if i < len(args) else top
        elif args[i].isdigit():
            days = int(args[i])
        i += 1

    rows = collect_sessions(days, project_filter)
    print_summary(rows, days)
    print_timeline(rows)
    print_yellow_signals_summary(rows)
    print_red_details(rows, top)
    print()


if __name__ == "__main__":
    main()
