# -*- coding: utf-8 -*-
"""组织深同步探查器(Loop 机制 6 第四方:直接探查各框仓,不信自报)。

来源:2026-09-24 用户拷问——compass 凭自身记忆索引断言 flywheel「静默」,
实测当日 7 commit 全速,误判全案。本脚本=防复发资产:深同步轮(每 5 轮)跑。

每框采集:最近 commit / 账本头部 / 仓内函件最新 3 件 / 活跃度标。
只读零写入;输出 JSON 快照 + 与上一快照的 diff。

用法:python scripts/org_deepsync.py [--out runtime/deepsync/]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

FRAMES = {
    "compass": {
        "repo": Path("C:/Users/chunx/Projects/nautilus-compass"),
        "ledger": "docs/plans/LOOP_STATE.md",
        "mail_glob": "*_INBOUND_*|*_OUTBOUND_*|*_REPLY_*",
    },
    "flywheel": {
        "repo": Path("C:/Users/chunx/Projects/nautilusflywheel"),
        "ledger": "GOALS.md",  # 北极星;loop 锚 docs/plans/LOOP_FW_*.md
        "mail_glob": "*_INBOUND_*|*_OUTBOUND_*|*_REPLY_*",
    },
    "v5": {
        # 本地仓 2026-08-27 归档;9 月起现役活动经平台函件+组织正本(无本地活跃仓)
        "repo": Path("C:/Users/chunx/Projects/nautilus-v5.archived-20260827"),
        "note": "archived 2026-08-27;现役通道=平台函件/bootstrap",
        "ledger": "",  # 归档仓,账本仅历史
        "mail_glob": "*_INBOUND_*|*_OUTBOUND_*|*_REPLY_*",
        "bootstrap": "https://nautilus.social/api/platform/org/bootstrap?agent=v5",
    },
    "platform": {
        "repo": Path("C:/Users/chunx/Projects/nautilus-platform-sdk"),
        "ledger": "",
        "mail_glob": "*_INBOUND_*|*_OUTBOUND_*|*_REPLY_*",
        "bootstrap": "https://nautilus.social/api/platform/org/bootstrap?agent=compass",
    },
    "daily": {
        # 本地仓未定位(2026-09-24 盲区);仅走平台 bootstrap 兜底
        "repo": None,
        "ledger": "",
        "mail_glob": "",
        "bootstrap": "https://nautilus.social/api/platform/org/bootstrap?agent=daily",
    },
}


def _git(repo: Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=30)
        return r.stdout.strip() if r.returncode == 0 else f"ERR({r.returncode})"
    except Exception as e:  # noqa: BLE001
        return f"ERR({str(e)[:60]})"


def _find_ledger(repo: Path, hint: str) -> str | None:
    if hint and (repo / hint).is_file():
        return hint
    for pat in ("docs/plans/LOOP*.md", "LOOP_STATE*.md", "GOALS.md"):
        hits = sorted(repo.glob(pat))
        if hits:
            return str(hits[0].relative_to(repo))
    return None


def _latest_mail(repo: Path, n: int = 3) -> list[str]:
    pats = ("*_INBOUND_*", "*_OUTBOUND_*", "*_REPLY_*", "*_BROADCAST_*")
    files = [f for pat in pats for f in repo.glob(pat) if f.is_file()]
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return [f.name for f in files[:n]]


def _activity(last_iso: str) -> str:
    """last_iso 如 2026-09-24T12:34:56+08:00 → 活跃度标。"""
    try:
        t = datetime.fromisoformat(last_iso)
        hours = (datetime.now(timezone.utc) - t).total_seconds() / 3600
        if hours < 0:
            hours = 0.0  # 时区/时钟偏差
        if hours < 48:
            return f"ACTIVE({hours:.0f}h)"
        if hours < 24 * 7:
            return f"WARM({hours/24:.1f}d)"
        return f"STALE({hours/24:.0f}d)"
    except Exception:  # noqa: BLE001
        return "?"


def probe_frame(name: str, cfg: dict) -> dict:
    out: dict = {"frame": name}
    repo = cfg.get("repo")
    if repo is None or not repo.is_dir():
        out["status"] = "REPO_MISSING"
    else:
        out["status"] = "OK"
        log = _git(repo, "log", "-5", "--pretty=%h|%ad|%s", "--date=iso")
        commits = [ln.split("|", 2) for ln in log.splitlines() if "|" in ln]
        out["commits"] = [{"h": c[0], "date": c[1], "s": c[2][:90]} for c in commits]
        out["activity"] = _activity(commits[0][1]) if commits else "NO_COMMITS"
        ledger = _find_ledger(repo, cfg.get("ledger", ""))
        out["ledger"] = ledger
        if ledger:
            head = (repo / ledger).read_text(encoding="utf-8", errors="replace").splitlines()[:8]
            out["ledger_head"] = [ln.strip()[:100] for ln in head if ln.strip()][:5]
        out["mail_latest"] = _latest_mail(repo)
    bs = cfg.get("bootstrap")
    if bs:
        try:
            req = urllib.request.Request(bs, method="GET")
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read(4000).decode("utf-8", "replace")
            out["bootstrap"] = f"HTTP200(len={len(body)})"
        except Exception as e:  # noqa: BLE001
            out["bootstrap"] = f"ERR({str(e)[:60]})"
    return out


def diff_prev(snapshot: dict, prev: dict | None) -> list[str]:
    if not prev:
        return ["(首跑,无对比基线)"]
    notes = []
    for name, cur in snapshot["frames"].items():
        p = prev.get("frames", {}).get(name)
        if not p:
            continue
        cn, pn = len(cur.get("commits", [])), len(p.get("commits", []))
        ch = {c["h"] for c in cur.get("commits", [])} & {c["h"] for c in p.get("commits", [])}
        delta = cn - len(ch)
        notes.append(f"{name}: 自上快照 +{delta} commits,activity={cur.get('activity', '?')}")
    return notes


def mailbox_view() -> list[str]:
    """断点 1 接线:拉各框 bootstrap mailbox 段,自动投影跨框未读/逾期。

    平台已生成 unread/due_12h,此前无框消费——本视图替代手工函件两列。
    """
    lines = []
    for name in FRAMES:
        try:
            req = urllib.request.Request(
                f"https://nautilus.social/api/platform/org/bootstrap?agent={name}")
            with urllib.request.urlopen(req, timeout=12) as r:
                d = json.loads(r.read(20000)).get("data", {})
            mb = d.get("mailbox", {})
            unread = mb.get("unread", [])
            if unread or mb.get("due_12h"):
                for m in unread[:4]:
                    lines.append(f"{name} 未读 id={m.get('id')} "
                                 f"from={m.get('from_agent')} · "
                                 f"{str(m.get('title', ''))[:60]}")
                if mb.get("due_12h"):
                    lines.append(f"{name} ⚠️ due_12h={mb['due_12h']}")
        except Exception as e:  # noqa: BLE001
            lines.append(f"{name} mailbox ERR({str(e)[:50]})")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "runtime" / "deepsync"))
    a = ap.parse_args()
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)

    snap = {"ts": datetime.now().isoformat(timespec="seconds"),
            "frames": {name: probe_frame(name, cfg) for name, cfg in FRAMES.items()}}

    prevs = sorted(outdir.glob("deepsync_snapshot_*.json"))
    prev = None
    if prevs:
        try:
            prev = json.loads(prevs[-1].read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = None
    snap["diff_notes"] = diff_prev(snap, prev)

    ts = snap["ts"].replace(":", "").replace("-", "")[:13]
    path = outdir / f"deepsync_snapshot_{ts}.json"
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1),
                    encoding="utf-8", newline="\n")

    print(f"== 组织深同步快照 {snap['ts']} → {path.name} ==")
    for name, f in snap["frames"].items():
        print(f"\n[{name}] {f.get('status')} · {f.get('activity', f.get('bootstrap', ''))}"
              f" · ledger={f.get('ledger') or '-'}")
        for c in f.get("commits", [])[:3]:
            print(f"  {c['h']} {c['date'][:10]} {c['s']}")
        if f.get("mail_latest"):
            print(f"  mail: {', '.join(f['mail_latest'])}")
        if f.get("bootstrap"):
            print(f"  bootstrap: {f['bootstrap']}")
    print("\n== 跨框 mailbox 全局投影(自动两列替代手工登记)==")
    mb_lines = mailbox_view()
    snap["mailbox"] = mb_lines
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1),
                    encoding="utf-8", newline="\n")
    for ln in mb_lines or ["  (全部清空)"]:
        print(f"  {ln}")

    print("\n== 对比上一快照 ==")
    for n in snap["diff_notes"]:
        print(f"  {n}")


if __name__ == "__main__":
    main()
