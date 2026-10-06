# -*- coding: utf-8 -*-
"""LOOP 探针层:四源+定时件,静默检查,有事件才输出。
用法:python runtime/loop/probe.py   (exit 0=无事;exit 1=有事件,看 stdout)
"""
import json
import subprocess
import sys
from pathlib import Path

EVENTS = []


def probe_mailbox():
    # 本机常挂 socks 代理会劫持 urllib,curl 走系统栈更稳
    try:
        out = subprocess.run(
            ["curl", "-s", "--max-time", "15",
             "https://nautilus.social/api/platform/org/mailbox?to=compass&unread=1"],
            capture_output=True, text=True, timeout=20)
        data = json.loads(out.stdout).get("data") or []
        for m in data:
            EVENTS.append(f"信箱未读 #{m.get('id')} {m.get('from_agent')}: {(m.get('title') or '')[:50]}")
    except Exception as e:
        EVENTS.append(f"探针故障-信箱: {type(e).__name__}")


def probe_github():
    base_f = Path(__file__).parent / ".gh_baseline.json"
    base = {}
    try:
        base = json.loads(base_f.read_text(encoding="utf-8"))
    except Exception:
        pass
    for repo, num in (("MemTensor/MemOS", 2440), ("mem0ai/mem0", 7514),
                      ("gtaras7/typesafe-jev", 2),
                      # 10/3 夜 LOOP 增:报名帖+送测+已采纳协议线(增量报,首跑只建基线)
                      ("Nautilus-agent/compass", 1), ("Nautilus-agent/compass", 2),
                      ("Srt-tian/PhysicalRSI", 1), ("EmbodiedSWE/EmbodiedSWE", 134),
                      ("sunghunkwag/rsi-bench", 1), ("getzep/graphiti", 1948)):
        try:
            out = subprocess.run(
                ["gh", "issue", "view", str(num), "--repo", repo, "--json", "comments"],
                capture_output=True, text=True, timeout=20)
            comments = json.loads(out.stdout).get("comments", []) if out.returncode == 0 else None
            if comments is None:
                continue
            # 只数外部评论:自家出站件不计增量(R51/R55 两次自家回评误报同型);
            # 基线直写不取 max(对方删评时 max 会冻结高位漏报,R40 有先例)
            n = sum(1 for c in comments
                    if (c.get("author") or {}).get("login") != "chunxiaoxx")
            k = f"{repo}#{num}"
            prev = base.get(k)
            if prev is not None and n > prev:
                EVENTS.append(f"GitHub {k} 新增 {n - prev} 条外部评论(外部总 {n})——外联回应!")
            base[k] = n
        except Exception:
            pass
    base_f.write_text(json.dumps(base), encoding="utf-8")
    # 通知流兜底(漏监教训 10/1:typesafe-jev Issue#2 回应漏看半天)
    # 分级过滤(R70:CI/Deploy 常规红每轮刷 20-40 行稀释真事件信号)——
    # workflow 失败类折叠计数不逐条列;issue/PR 类=外联回应信号,逐条列
    try:
        out = subprocess.run(
            ["gh", "api", "notifications", "--jq",
             ".[] | select(.unread==true) | .subject.title"],
            capture_output=True, text=True, timeout=20)
        ci_n = 0
        for line in (out.stdout or "").splitlines():
            t = line.strip()
            if not t:
                continue
            if "workflow run failed" in t or "workflow run succeeded" in t:
                ci_n += 1
                continue
            EVENTS.append(f"GitHub 通知未读: {t[:70]}")
        if ci_n:
            EVENTS.append(f"GitHub CI/Deploy 通知 ×{ci_n}(组织他仓常规红,折叠不处置)")
    except Exception:
        pass


def probe_a100():
    try:
        import paramiko
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect("223.109.239.30", port=23236, username="root",
                  password="REDACTED_A100_PW", timeout=10)
        # GPU 空闲判定=无计算进程(瞬时利用率会误报:迭代间隙利用率 0 但进程在)
        _, out, _ = c.exec_command(
            "nvidia-smi --query-compute-apps=pid --format=csv,noheader | wc -l; "
            "nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader",
            timeout=20)
        lines = out.read().decode().strip().splitlines()
        n_proc = int(lines[0].strip() or 0)
        if n_proc == 0:
            EVENTS.append(f"A100 真空闲(无计算进程): {lines[1] if len(lines) > 1 else '?'}")
        c.close()
    except Exception as e:
        EVENTS.append(f"探针故障-A100: {type(e).__name__}")


def probe_cloud_daemon():
    """第六源(2026-10-06 灯下黑教训):云端 compass daemon 健康——19.5万次过载拒连 19h 无人察觉。"""
    try:
        import subprocess
        r = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=12", "cloud",
             "grep -c 'overload' ~/.claude/plugins/nautilus-compass/.cache/daemon.log 2>/dev/null; "
             "tail -1 ~/.claude/plugins/nautilus-compass/.cache/daemon.log 2>/dev/null"],
            capture_output=True, text=True, timeout=40)
        lines = [x for x in r.stdout.splitlines() if x.strip()]
        cnt = int(lines[0]) if lines and lines[0].isdigit() else -1
        last = lines[1][:60] if len(lines) > 1 else "?"
        if cnt < 0:
            EVENTS.append("探针故障-cloudd: 无读数")
        else:
            base = _cloud_baseline(cnt)
            delta = cnt - base
            if delta > 50:
                EVENTS.append(f"🔴 cloud-daemon 过载新增 {delta}(累计 {cnt})尾行: {last}")
            elif delta > 0:
                EVENTS.append(f"cloud-daemon 过载小幅 +{delta}(累计 {cnt})观察")
            else:
                EVENTS.append(f"cloud-daemon 过载零新增(累计 {cnt})")
    except Exception as e:
        EVENTS.append(f"探针故障-cloudd: {type(e).__name__}: {str(e)[:50]}")


_CLOUD_BASELINE_FILE = Path(__file__).parent / ".cloud_overload_last.txt"
def _cloud_baseline(cur: int) -> int:
    """滚动基线:读上次计数(无文件则用修复时刻 195013 并落盘),比较后回写。"""
    try:
        last = int(_CLOUD_BASELINE_FILE.read_text().strip())
    except Exception:
        last = 195013
    Path(_CLOUD_BASELINE_FILE).write_text(str(cur))
    return last


def probe_gmail():
    # Gmail 未读探针(10/5 盲区修复:LOOP 指令清单从未含 Gmail,9/10 后零覆盖,
    # 用户拷问"为何没找到 gmail 外部来信"——补第五源;REST 配方=9/10 fallback 档)
    # 只报营销过滤后的真未读增量;基线记见过的 msg id,防同一封轮轮重报
    base_f = Path(__file__).parent / ".gmail_baseline.json"
    try:
        base = set(json.loads(base_f.read_text(encoding="utf-8")))
    except Exception:
        base = set()
    try:
        gdir = Path.home() / ".gmail-mcp"
        creds = json.loads((gdir / "credentials.json").read_text(encoding="utf-8"))
        inst = json.loads((gdir / "client_secret.json").read_text(encoding="utf-8"))["installed"]
        out = subprocess.run(
            ["curl", "-s", "--max-time", "15", "--proxy", "http://127.0.0.1:10808",
             "-X", "POST", "https://oauth2.googleapis.com/token",
             "-d", f"client_id={inst['client_id']}",
             "-d", f"client_secret={inst['client_secret']}",
             "-d", "refresh_token=" + creds["refresh_token"],
             "-d", "grant_type=refresh_token"],
            capture_output=True, text=True, timeout=20)
        tok = json.loads(out.stdout).get("access_token")
        if not tok:
            raise RuntimeError("no access_token")
        q = "is%3Ainbox%20is%3Aunread%20-category%3Apromotions%20-category%3Asocial"
        out = subprocess.run(
            ["curl", "-s", "--max-time", "15", "--proxy", "http://127.0.0.1:10808",
             f"https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=10&q={q}",
             "-H", f"Authorization: Bearer {tok}"],
            capture_output=True, text=True, timeout=20)
        msgs = json.loads(out.stdout).get("messages") or []
        fresh = [m["id"] for m in msgs if m["id"] not in base]
        base.update(m["id"] for m in msgs)
        for i, mid in enumerate(fresh[:5]):
            det = subprocess.run(
                ["curl", "-s", "--max-time", "15", "--proxy", "http://127.0.0.1:10808",
                 f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{mid}?format=metadata&metadataHeaders=Subject&metadataHeaders=From",
                 "-H", f"Authorization: Bearer {tok}"],
                capture_output=True, text=True, timeout=20)
            hdrs = {h["name"]: h["value"] for h in
                    json.loads(det.stdout).get("payload", {}).get("headers", [])}
            EVENTS.append(f"Gmail 未读新件: {(hdrs.get('Subject') or '?')[:60]}"
                          f" <{(hdrs.get('From') or '?')[:40]}>")
        base_f.write_text(json.dumps(sorted(base)[-200:]), encoding="utf-8")
    except Exception as e:
        EVENTS.append(f"探针故障-gmail: {type(e).__name__}: {str(e)[:60]}")


def main():
    import datetime
    print(f"[ts {datetime.datetime.now():%m-%d %H:%M}]")  # 时间戳头:防轮账时间漂移(10/2 第三次复发教训)
    probe_mailbox()
    probe_github()
    probe_gmail()
    probe_cloud_daemon()
    probe_a100()
    if EVENTS:
        print("== LOOP 探针有事件 ==")
        for e in EVENTS:
            print("-", e)
        sys.exit(1)
    print("quiet")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
