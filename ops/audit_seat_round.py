#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""审计席例行体检(2026-11-22 用户拍板"审计常态化")——只读探针,跨 Mac/cloud/GitHub。

背景:11/17-11/22 一次人工审计抓出五台"坏了没人知道"的仪器(loop 断供 3 天/判官假红
10 天/记忆服务无效数周/治理欠账 18 天/CI 盲区第 4 次)——审计不该靠人想起来。

纪律:
  · 只读:不发函、不 ack、不写 memory、不开轮、不改远端任何文件(10/24 单写定谳兼容)。
  · 每探针独立 try/except,单点失败记 UNREACHABLE 不拖垮整轮;永不抛异常退出。
  · 产出:runtime/audit/seat_rounds/<ts>.md 报告 + seat_log.md 一行汇总;RED 弹 Windows 气泡;
    报告 git commit(不 push)。
  · 调度:Windows 计划任务 compass-audit-seat 每日 09:30(ops/audit_seat_round.ps1 包装)。

判定口径(红=需人马上看;黄=知悉;绿=正常):
  loop 轮龄>3h 红 / CHANNEL_DOWN 标记 红 / 判官全同色 红
  API Error 尾部>0 黄 / 仓 ahead>0 黄 / 治理 M1 未落写 黄 / soul 连败≥3 或熔断 黄
  判官轮龄>4h 黄 / 信箱未读>0 黄 / 草稿 PR≥15 黄 / 机器不可达 黄
"""
from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT_DIR = ROOT / "runtime" / "audit"
ROUNDS = AUDIT_DIR / "seat_rounds"
LOG = AUDIT_DIR / "seat_log.md"
KEY = Path.home() / ".ssh" / "id_ed25519"
MAC = "chunxiao.wang@192.168.5.120"
SSH = ["ssh", "-i", str(KEY), "-o", "ConnectTimeout=10", "-o", "BatchMode=yes"]


def _b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def mac(script: str, timeout: int = 90) -> str:
    r = subprocess.run(SSH + [MAC, f"echo {_b64(script)} | base64 -d | bash"],
                       capture_output=True, text=True, timeout=timeout,
                       encoding="utf-8", errors="replace")
    return (r.stdout or "") + (("\n[err]" + r.stderr[-200:]) if r.returncode else "")


def cloud(script: str, timeout: int = 120) -> str:
    inner = f"echo {_b64(script)} | base64 -d | bash"
    return mac(f'ssh -o ConnectTimeout=8 -o BatchMode=yes cloud "{inner}"', timeout)


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str, str]] = []  # (probe, level, reading, note)

    def add(self, name: str, level: str, reading: str, note: str = "") -> None:
        self.rows.append((name, level, reading, note))
        print(f"[{level:5}] {name}: {reading} {note}")

    def worst(self) -> str:
        for lv in ("RED", "AMBER", "UNREACH", "GREEN"):
            if any(r[1] == lv for r in self.rows):
                return lv
        return "GREEN"


def probe_loop(rep: Report) -> None:
    name = "Mac 值守 loop"
    try:
        out = mac(
            "cd ~/Projects/nautilus-compass && python3 -c \"import json,datetime as d;"
            "s=json.load(open('runtime/loop/state.json'));"
            "t=d.datetime.strptime(s['last_round_ts'],'%Y-%m-%d %H:%M')-d.timedelta(hours=8);"
            "print(s['round'], round((d.datetime.utcnow()-t).total_seconds()/3600,1))\"; "
            "grep -c 'API Error' <(tail -40 runtime/loop/rounds.log); ls runtime/loop/CHANNEL_DOWN 2>/dev/null | wc -l")
        lines = [l.strip() for l in out.splitlines() if l.strip() and not l.startswith("[err]")]
        rnd, age = lines[0].split()
        api_err, down = int(lines[1]), int(lines[2])
        age_f = float(age)
        if age_f < -0.5:  # 时间戳口径漂移(state.json 为北京时间)——不能静默判绿
            level, note = "AMBER", "轮龄为负=时间戳口径异常"
        elif age_f > 3 or down:
            level, note = "RED", ""
        else:
            level, note = ("AMBER" if (age_f > 2.5 or api_err) else "GREEN"), ""
        rep.add(name, level, f"R{rnd} 轮龄{age}h", f"{note} 近轮API Error={api_err} CHANNEL_DOWN={down}".strip())
    except Exception as e:  # noqa: BLE001
        rep.add(name, "UNREACH", "-", str(e)[:80])


def probe_canary(rep: Report) -> None:
    name = "通道金丝雀"
    try:
        out = mac("cat ~/Projects/nautilus-compass/runtime/loop/channel_canary_state.json 2>/dev/null; "
                  "echo; tail -1 ~/Projects/nautilus-compass/runtime/loop/canary.log 2>/dev/null")
        lines = [l for l in out.splitlines() if l.strip()]
        st = json.loads(lines[0])
        ok_age = round((time.time() - float(st.get("last_ok") or 0)) / 3600, 1)
        level = "RED" if int(st.get("streak") or 0) >= 2 else ("AMBER" if int(st.get("streak") or 0) >= 1 or ok_age > 1.5 else "GREEN")
        rep.add(name, level, f"streak={st.get('streak')} 上次OK={ok_age}h前")
    except Exception as e:  # noqa: BLE001
        rep.add(name, "UNREACH", "-", str(e)[:80])


def probe_repo(rep: Report) -> None:
    name = "仓 CI 盲区(ahead)"
    try:
        out = mac("cd ~/Projects/nautilus-compass && git fetch -q origin 2>/dev/null; git rev-list --count origin/main..HEAD; "
                  "git status --porcelain | wc -l")
        ahead, dirty = [int(x) for x in out.split()[:2]]
        rep.add(name, "AMBER" if ahead else "GREEN", f"ahead={ahead}", f"dirty={dirty}")
    except Exception as e:  # noqa: BLE001
        rep.add(name, "UNREACH", "-", str(e)[:80])


def probe_governance(rep: Report) -> None:
    name = "治理欠账 M1-M3"
    try:
        out = mac("grep -c '终态坐标' ~/infra/baseline/INFRA_BASELINE.md 2>/dev/null; grep -c '终态坐标' ~/.claude/ORG_BRIEF.md 2>/dev/null")
        a, b = [int(x) for x in out.split()[:2]]
        rep.add(name, "GREEN" if (a and b) else "AMBER", f"INFRA_BASELINE命中={a} ORG_BRIEF命中={b}",
                "" if (a and b) else "COORD_1104 开出至今未落写")
    except Exception as e:  # noqa: BLE001
        rep.add(name, "UNREACH", "-", str(e)[:80])


def probe_soul(rep: Report) -> None:
    name = "soul 自改(cloud)"
    try:
        out = cloud("cat ~/nautilus-soul-workspace/.soul-failure-state.json; echo; ls ~/nautilus-soul-workspace/.soul-pause 2>/dev/null | wc -l")
        lines = [l for l in out.splitlines() if l.strip()]
        st = json.loads(lines[0])
        paused = int(lines[1])
        c = int(st.get("consecutive") or 0)
        level = "AMBER" if (paused or c >= 3) else "GREEN"
        rep.add(name, level, f"连败={c}/5 pause={paused}")
    except Exception as e:  # noqa: BLE001
        rep.add(name, "UNREACH", "-", str(e)[:80])


def probe_judge(rep: Report) -> None:
    name = "PR 机审器(cloud)"
    try:
        out = cloud("journalctl -u nautilus-pr-review --since '6 hours ago' --no-pager 2>/dev/null | grep -a 'pr_review {' | tail -1")
        m = re.search(r"\{.*\} at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", out)
        if not m:
            rep.add(name, "AMBER", "6h 无运行记录")
            return
        summ = eval(m.group(0)[: m.group(0).rfind("} at") + 1])  # noqa: S307 - journal 自家格式
        # journal 时间戳=cloud 本地时(UTC+8),本机亦 UTC+8,按本地时解析即对;勿再减 timezone
        ts = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
        age = round((time.time() - ts) / 3600, 1)
        level = "RED" if summ.get("monotone_alert") else ("AMBER" if age > 4 else "GREEN")
        rep.add(name, level, f"审{summ.get('reviewed')} 绿{summ.get('green')} 红{summ.get('red')} 灰{summ.get('grey')} 轮龄{age}h",
                "全同色警报!" if summ.get("monotone_alert") else "")
    except Exception as e:  # noqa: BLE001
        rep.add(name, "UNREACH", "-", str(e)[:80])


def probe_mailbox(rep: Report) -> None:
    name = "平台信箱未读"
    try:
        out = mac("cd ~/Projects/nautilus-compass && .venv/bin/python scripts/platform_mail.py check --to compass 2>/dev/null | tail -1")
        m = re.search(r"total:\s*(\d+)", out)
        n = int(m.group(1)) if m else -1
        rep.add(name, "AMBER" if n != 0 else "GREEN", f"unread={n}")
    except Exception as e:  # noqa: BLE001
        rep.add(name, "UNREACH", "-", str(e)[:80])


def probe_github(rep: Report) -> None:
    name = "GitHub 草稿 PR 积压"
    try:
        cred = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                              capture_output=True, text=True, timeout=30, cwd=ROOT).stdout
        tok = dict(l.split("=", 1) for l in cred.splitlines() if "=" in l).get("password", "")
        req = urllib.request.Request("https://api.github.com/repos/chunxiaoxx/nautilus-core/pulls?state=open&per_page=100",
                                     headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            prs = json.load(r)
        drafts = [p for p in prs if p.get("draft")]
        rep.add(name, "AMBER" if len(drafts) >= 15 else "GREEN", f"开放={len(prs)} 草稿={len(drafts)}")
    except Exception as e:  # noqa: BLE001
        rep.add(name, "UNREACH", "-", str(e)[:80])


def notify(level: str, summary: str) -> None:
    if level != "RED":
        return
    ps = ("Add-Type -AssemblyName System.Windows.Forms;"
          "$n=New-Object System.Windows.Forms.NotifyIcon;$n.Icon=[System.Drawing.SystemIcons]::Warning;"
          "$n.Visible=$true;$n.ShowBalloonTip(15000,'compass 审计席 RED',\"" + summary.replace('"', "'") + "\",[System.Windows.Forms.ToolTipIcon]::Warning);Start-Sleep 12;$n.Dispose()")
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", "Add-Type -AssemblyName System.Drawing;" + ps],
                       capture_output=True, timeout=40)
    except Exception:  # noqa: BLE001
        pass


def main() -> int:
    ROUNDS.mkdir(parents=True, exist_ok=True)
    rep = Report()
    for p in (probe_loop, probe_canary, probe_repo, probe_governance, probe_soul, probe_judge, probe_mailbox, probe_github):
        try:
            p(rep)
        except Exception as e:  # noqa: BLE001
            rep.add(p.__name__, "UNREACH", "-", str(e)[:80])
    worst = rep.worst()
    ts = time.strftime("%Y%m%d-%H%M%S")  # 秒级:同分钟多跑不互相覆盖
    lines = [f"# 审计席例行体检 · {ts} · 总判 {worst}", "",
             "| 探针 | 判 | 读数 | 备注 |", "|---|---|---|---|"]
    lines += [f"| {n} | {lv} | {rd} | {note} |" for n, lv, rd, note in rep.rows]
    lines += ["", f"[实测] 全部读数为本席只读探针当场取得;UNREACHABLE=机器不在网段/超时,非故障。",
              "", "判级口径见 ops/audit_seat_round.py 文件头。"]
    (ROUNDS / f"{ts}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"- {ts} · **{worst}** · " + "; ".join(f"{n}={lv}" for n, lv, _, _ in rep.rows) + "\n")
    reds = [f"{n}:{rd}" for n, lv, rd, _ in rep.rows if lv == "RED"]
    if reds:
        notify(worst, " | ".join(reds)[:200])
    try:
        subprocess.run(["git", "add", "runtime/audit"], cwd=ROOT, capture_output=True, timeout=30)
        subprocess.run(["git", "commit", "-q", "-m", f"chore(audit): 审计席例行体检 {ts} 总判{worst}"],
                       cwd=ROOT, capture_output=True, timeout=30)
    except Exception:  # noqa: BLE001
        pass
    print(f"\n总判: {worst} · 报告: runtime/audit/seat_rounds/{ts}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
