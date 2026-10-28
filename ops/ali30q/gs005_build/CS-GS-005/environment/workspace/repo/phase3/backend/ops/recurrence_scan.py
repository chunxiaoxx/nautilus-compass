#!/usr/bin/env python
"""复发扫描器(2026-10-04 · 复发棘轮物理化:教训从"记住"变"每轮跑一下")。

来源=复盘第四节优化件3:immune 登记表的问题模式做成机检。
判据=各教训的实测探针;触发器=LOOP 轮/部署窗;台账=stdout JSON(值守轮记 memory,
部署窗记 runbook 勾)。

用法(在 phase3/backend/ 下):python ops/recurrence_scan.py
退出码:全过=0;任一红=1(值守轮按红灯处置序处理,先证伪探针自身)。
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ssh(cmd: str) -> str:
    r = subprocess.run(["ssh", "-o", "ConnectTimeout=10", "cloud", cmd],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    return r.stdout.strip()


def _local_grep_count(pattern: str, subdir: str) -> int:
    n = 0
    for p in (ROOT / subdir).rglob("*.py"):
        if ".venv" in str(p) or "__pycache__" in str(p):
            continue
        try:
            if re.search(pattern, p.read_text(encoding="utf-8", errors="ignore")):
                n += 1
        except OSError:
            continue
    return n


def scans() -> list[dict]:
    out = []
    # 1. nginx .bak 残留(8/30→10/3 复发)
    out.append({"name": "nginx_bak", "status": "PASS" if _ssh(
        "ls /etc/nginx/sites-enabled/ | grep -c '\\.bak' || true") == "0" else "RED",
        "detail": "sites-enabled .bak 必须 0"})
    # 2. utcnow 回潮(9/22+10/4 两轮病根)——AMBER 分诊件:只有"混写表"(裸SQL+模型
    #    双路径写同表)才致病;纯模型写入表全表同钟自洽,盲改反而人为混列。分诊清单
    #    =org_mailbox(已修);其余待逐表确认写入路径后定。
    n = _local_grep_count(r"datetime\.utcnow", "models")
    out.append({"name": "utcnow_models", "status": "PASS" if n == 0 else "AMBER",
                "detail": f"models/ 下 utcnow 文件数={n}(分诊:混写表必修,纯模型表自洽;org_mailbox 已修)"})
    # 3. 生产工作树 clean(纪律2)
    dirty = _ssh("cd /home/ubuntu/nautilus-mvp && git status --porcelain | head -3")
    out.append({"name": "prod_clean", "status": "PASS" if not dirty else "RED",
                "detail": dirty or "clean"})
    # 4. posts 渲染活性(v5 修复验证,1370 行历史帖)
    posts = _ssh("curl -s -m 8 'http://127.0.0.1:8001/posts' | grep -c 'class=\\\"post\\\"' || true")
    out.append({"name": "posts_render", "status": "PASS" if posts.isdigit() and int(posts) > 0 else "AMBER",
                "detail": f"渲染帖数={posts}(0=渲染层仍未修,v5 修复单 #2763)"})
    # 5. key 信箱时钟(10/4 根修后新函不应 NULL/偏移)
    skew = _ssh("cd /home/ubuntu/nautilus-mvp/phase3/backend && python3 -c \""
                "import psycopg2; url=[l.split('=',1)[1].strip() for l in open('.env') if l.startswith('DATABASE_URL=')][0]; "
                "c=psycopg2.connect(url).cursor(); "
                "c.execute('SELECT coalesce(max(now()-created_at), interval \\\"0\\\") FROM org_mailbox WHERE created_at > now() - interval \\\"6 hours\\\"'); "
                "print(c.fetchone()[0])\"")
    out.append({"name": "mailbox_clock", "status": "PASS", "detail": f"最新函时钟偏差={skew}(信息性)"})
    return out


def main() -> None:
    rows = scans()
    payload = {"ts": datetime.now(timezone.utc).isoformat(), "scans": rows,
               "red": [r["name"] for r in rows if r["status"] == "RED"]}
    log = _append_log(payload)
    payload["halflife"] = _halflife(log)
    print(json.dumps(payload, ensure_ascii=False, indent=1))
    sys.exit(1 if payload["red"] else 0)


LOG_PATH = ROOT / "docs" / "evidence" / "org-os" / "recurrence_log.jsonl"


def _append_log(payload: dict) -> list:
    """台账落盘(gitignore 高频写文件):每跑一行,周报半衰期取数源。"""
    import io
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": payload["ts"],
                                "status": {r["name"]: r["status"] for r in payload["scans"]}},
                               ensure_ascii=False) + "\n")
        with open(LOG_PATH, encoding="utf-8") as f:
            return [json.loads(x) for x in f if x.strip()]
    except OSError:
        return []


def _halflife(log: list) -> dict:
    """错误半衰期(2026-10-04 用户批入周报):同名探针相邻两次 RED 的间隔小时。
    首犯(1 次)标注 first;从未红标注 clean——自我优化能力的真读数。"""
    from datetime import datetime as _dt
    series: dict = {}
    for row in log:
        ts = _dt.fromisoformat(row["ts"])
        for name, st in row.get("status", {}).items():
            if st == "RED":
                series.setdefault(name, []).append(ts)
    out = {}
    for name, ts_list in series.items():
        gaps = [(b - a).total_seconds() / 3600 for a, b in zip(ts_list, ts_list[1:])]
        out[name] = (f"首犯 {ts_list[0]:%m-%d}" if not gaps
                     else f"再现{len(gaps)}次,间隔{[round(g, 1) for g in gaps]}h")
    return out or {"note": "尚无 RED 记录(首期)"}


if __name__ == "__main__":
    main()
