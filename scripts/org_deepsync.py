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
import sys
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


def due_enforcer() -> tuple[list[dict], list[str]]:
    """断点 2 接线:due 执法器——机械判逾期,替代人工末催。

    职权边界:只亮牌+汇总,不直接催他框(跨框追办=platform 主责,
    五框分工矩阵);--notify 时向 platform 发逾期汇总表。
    返回 (逾期明细 rows, 亮牌行 lines)。
    """
    from datetime import datetime as _dt
    now = _dt.now()
    rows: list[dict] = []
    lines: list[str] = []
    for name in FRAMES:
        try:
            req = urllib.request.Request(
                f"https://nautilus.social/api/platform/org/bootstrap?agent={name}")
            with urllib.request.urlopen(req, timeout=12) as r:
                d = json.loads(r.read(60000)).get("data", {})
            for m in d.get("mailbox", {}).get("unread", []):
                dl = m.get("deadline")
                if not dl or m.get("ack_at"):
                    continue
                t = _dt.strptime(dl.split(".")[0], "%Y-%m-%d %H:%M:%S")
                if t < now:
                    hours = (now - t).total_seconds() / 3600
                    rows.append({"box": name, "id": m["id"],
                                 "from": m.get("from_agent"),
                                 "title": str(m.get("title", ""))[:60],
                                 "deadline": dl, "overdue_h": round(hours, 1)})
                    lines.append(f"🔴 {name} 欠 id={m['id']}(from={m.get('from_agent')})"
                                 f" 已逾期 {hours:.1f}h · {str(m.get('title', ''))[:50]}")
        except Exception as e:  # noqa: BLE001
            lines.append(f"{name} due-scan ERR({str(e)[:50]})")
    return rows, lines


def due_ledger(rows: list[dict], now_iso: str) -> dict:
    """误报双计数(汇聚2.0 修正层施工 · 2026-09-26):逾期三态账。

    每条逾期 id 状态机:active(本轮在列)→ flare(消失 1 轮=疑似误报或
    已处理,待复轮)→ cleared(消失 ≥2 轮)。计数:persist/flare/cleared
    +历史误报率=flare_total/(flare_total+cleared_total)——执法器自身
    漂移可被复算(自报复发防线)。
    """
    import os
    p = Path(__file__).parent.parent / "runtime/deepsync/due_ledger.json"
    book: dict[str, dict] = {}
    if p.exists():
        try:
            book = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            book = {}
    seen = {f"{r['box']}#{r['id']}" for r in rows}
    for k in seen:  # 本轮在列:active 记 first_seen(新)/last_seen(旧)
        e = book.setdefault(k, {"first_seen": now_iso, "misses": 0,
                                "status": "active"})
        e["last_seen"] = now_iso
        e["misses"] = 0
        e["status"] = "active"
    for k, e in book.items():  # 不在列:misses+1,两轮即清
        if k in seen:
            continue
        e["misses"] = int(e.get("misses", 0)) + 1
        e["status"] = "flare" if e["misses"] == 1 else "cleared"
    hist = {}
    for e in book.values():
        if e["status"] in ("flare", "cleared"):
            hist[e["status"]] = hist.get(e["status"], 0) + 1
    fp, cl = hist.get("flare", 0), hist.get("cleared", 0)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(book, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    err_rate = round(fp / (fp + cl), 3) if (fp + cl) else 0.0
    return {"persist": len(seen), "flare": fp, "cleared": cl,
            "false_alarm_rate": err_rate}


def due_signer():
    """执法器报告自签名(自报复发防线:报告生产者标志必须可验源)。

    密钥:~/.claude/.cache/deepsync_due/due_signer_seed.hex(首次生成,
    永不入仓);pubkey 归档 runtime/deepsync/due_signer.pub。
    """
    import os
    from jev_trust.receipt import KeyPair
    d = Path.home() / ".claude/.cache/deepsync_due"
    d.mkdir(parents=True, exist_ok=True)
    sp = d / "due_signer_seed.hex"
    if sp.exists():
        kp = KeyPair.from_hex(sp.read_text(encoding="utf-8").strip())
    else:
        kp = KeyPair(seed=os.urandom(32))
        sp.write_text(kp.seed.hex(), encoding="utf-8")
    pub = Path(__file__).parent.parent / "runtime/deepsync/due_signer.pub"
    if not pub.exists():
        pub.write_text(kp.pub_hex, encoding="utf-8")  # property,无括号
    return kp


def deep_read() -> list[str]:
    """全框深读(2026-09-25 教训:切片验收通过藏在账本正文,机械快照漏一夜)。

    有本地仓的框 → 读账本「最近进度行」(grep 当日日期标记)+ 最新提交;
    无本地仓的框 → 组织正本 git(nautilus-core soul-distill-deploy)+ bootstrap
    state/goals 段。返回人读行。
    """
    import re
    from datetime import datetime as _dt
    today = _dt.now().strftime("%Y-%m-%d")
    lines: list[str] = []

    # ① flywheel:本地仓,账本进度行(日期标记:2026-09-2x 或 9/2x)
    fw = Path("C:/Users/chunx/Projects/nautilusflywheel")
    if fw.is_dir():
        for doc in ("docs/plans/2026-09-21-B案首包执行方案.md", "docs/plans/LOOP_FW_20260921.md"):
            p = fw / doc
            if not p.is_file():
                continue
            hits = [ln.strip()[:160] for ln in p.read_text(
                encoding="utf-8", errors="replace").splitlines()
                if re.search(rf"{today}|9/2[4-9]", ln)][:3]
            for h in hits:
                lines.append(f"[flywheel·{doc.split('/')[-1][:20]}] {h}")
        log = _git(fw, "log", "-3", "--pretty=%h %ad %s", "--date=format:%d %H:%M")
        for ln in log.splitlines()[:3]:
            lines.append(f"[flywheel·git] {ln[:150]}")

    # ② 组织正本(platform/v5/soul 层真值):nautilus-core soul-distill-deploy
    core = Path("C:/Users/chunx/Projects/nautilus-core")
    if core.is_dir():
        _git(core, "fetch", "origin", "soul-distill-deploy", "--quiet")
        log = _git(core, "log", "-5", "--pretty=%h %ad %s",
                   "--date=format:%d %H:%M", "origin/soul-distill-deploy")
        for ln in log.splitlines()[:5]:
            lines.append(f"[org-ssot·git] {ln[:150]}")

    # ③ 无本地仓框:v5/platform/daily 的 bootstrap state/goals 段截取
    for name in ("v5", "platform", "daily"):
        try:
            req = urllib.request.Request(
                f"https://nautilus.social/api/platform/org/bootstrap?agent={name}")
            with urllib.request.urlopen(req, timeout=12) as r:
                d = json.loads(r.read(60000)).get("data", {})
            seg = {k: d.get(k) for k in ("identity", "state", "goals") if d.get(k)}
            s = json.dumps(seg, ensure_ascii=False)
            lines.append(f"[{name}·bootstrap] {s[:260]}")
        except Exception as e:  # noqa: BLE001
            lines.append(f"[{name}·bootstrap] ERR({str(e)[:40]})")
    return lines


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
    ap.add_argument("--notify", action="store_true",
                    help="新增逾期时写 due_report(发送人工触发)")
    ap.add_argument("--notify-all", action="store_true",
                    help="强制写当前全量逾期报告(首跑/周汇总用)")
    ap.add_argument("--deep", action="store_true",
                    help="全框深读:账本进度行+组织正本 git+bootstrap 正文段")
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

    print("\n== due 执法器(逾期亮牌,职权:只亮牌+汇总,追办权在 platform)==")
    due_rows, due_lines = due_enforcer()
    snap["due_overdue"] = due_rows
    # 误报双计数(三态账):persist/flare/cleared + 历史误报率
    dl = due_ledger(due_rows, ts)
    snap["due_ledger_counts"] = dl
    due_lines.append(f"  双计数:persist={dl['persist']} flare={dl['flare']}"
                     f" cleared={dl['cleared']}"
                     f" 历史误报率={dl['false_alarm_rate']}")
    # 只对新增逾期亮牌(对比上次快照,防每轮重复噪声)
    prev_due = {r["id"] for r in (prev or {}).get("due_overdue", [])}
    new_due = [r for r in due_rows if r["id"] not in prev_due]
    snap["due_new_this_round"] = [r["id"] for r in new_due]
    for ln in due_lines or ["  (无逾期)"]:
        print(f"  {ln}")

    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1),
                    encoding="utf-8", newline="\n")
    for ln in mb_lines or ["  (全部清空)"]:
        print(f"  {ln}")

    notify_all = "--notify-all" in sys.argv
    if (new_due or (notify_all and due_rows)) and (
            "--notify" in sys.argv or notify_all):
        body = ["跨框逾期汇总(深同步轮自动生成,职权边界:只报不催,追办由你方执行)\n"]
        for r in due_rows:
            body.append(f"- {r['box']} 欠 id={r['id']}(from={r['from']}) "
                        f"逾期 {r['overdue_h']}h(deadline {r['deadline']}):"
                        f"{r['title']}")
        body.append(f"\n本轮新增逾期:{', '.join(str(r['id']) for r in new_due)}。"
                    "数据源:各框 bootstrap mailbox(deadline+ack_at 机械判定)。")
        body.append(f"执法器双计数(误报自检):persist={dl['persist']}"
                    f" flare={dl['flare']} cleared={dl['cleared']}"
                    f" 历史误报率={dl['false_alarm_rate']}")
        out = outdir / f"due_report_{ts}.md"
        # 自签名:先写终版(含 pubkey 验证头),一次签;sig 在旁文件
        try:
            kp = due_signer()
            body.append(f"\n验证:jev_trust KeyPair.verify_log(本报告,"
                        f"旁 .sig 文件)+pubkey={kp.pub_hex[:16]}…"
                        "(全量见 runtime/deepsync/due_signer.pub)")
        except Exception as e:  # noqa: BLE001
            print(f"[sign] 密钥 FAIL {str(e)[:80]}(报告不带签名头)")
        out.write_text("\n".join(body), encoding="utf-8", newline="\n")
        try:
            sig = kp.sign_log(out)
            print(f"[sign] {sig.name}")
        except Exception as e:  # noqa: BLE001
            print(f"[sign] FAIL {str(e)[:80]}(报告未签名)")
        print(f"\n[notify] 新增逾期 {len(new_due)} 条,报告已写 {out.name}"
              "(发送用 platform_mail.py,人工触发)")

    if a.deep:
        print("\n== 全框深读(账本正文+组织正本+bootstrap 段)==")
        deep_lines = deep_read()
        snap["deep"] = deep_lines
        path.write_text(json.dumps(snap, ensure_ascii=False, indent=1),
                        encoding="utf-8", newline="\n")
        for ln in deep_lines:
            print(f"  {ln}")

    print("\n== 对比上一快照 ==")
    for n in snap["diff_notes"]:
        print(f"  {n}")


if __name__ == "__main__":
    main()
