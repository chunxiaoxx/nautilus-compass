# -*- coding: utf-8 -*-
"""LOOP 探针层:四源+定时件,静默检查,有事件才输出。
用法:python runtime/loop/probe.py   (exit 0=无事;exit 1=有事件,看 stdout)
"""
import json
import subprocess
import sys
import urllib.request
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
                      ("gtaras7/typesafe-jev", 2)):
        try:
            out = subprocess.run(
                ["gh", "issue", "view", str(num), "--repo", repo, "--json", "comments"],
                capture_output=True, text=True, timeout=20)
            n = len(json.loads(out.stdout).get("comments", [])) if out.returncode == 0 else -1
            k = f"{repo}#{num}"
            prev = base.get(k)
            if n > 0 and prev is not None and n > prev:
                EVENTS.append(f"GitHub {k} 新增 {n - prev} 条评论(总 {n})——外联回应!")
            base[k] = max(n, prev or 0)
        except Exception:
            pass
    base_f.write_text(json.dumps(base), encoding="utf-8")
    # 通知流兜底(漏监教训 10/1:typesafe-jev Issue#2 回应漏看半天)
    try:
        out = subprocess.run(
            ["gh", "api", "notifications", "--jq",
             ".[] | select(.unread==true) | .subject.title"],
            capture_output=True, text=True, timeout=20)
        for line in (out.stdout or "").splitlines():
            if line.strip():
                EVENTS.append(f"GitHub 通知未读: {line.strip()[:70]}")
    except Exception:
        pass


def probe_a100():
    try:
        import paramiko
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect("223.109.239.30", port=23236, username="root",
                  password="iefe4Eey", timeout=10)
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


def main():
    import datetime
    print(f"[ts {datetime.datetime.now():%m-%d %H:%M}]")  # 时间戳头:防轮账时间漂移(10/2 第三次复发教训)
    probe_mailbox()
    probe_github()
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
