"""目标模式心跳执法 · 每小时跑一次(ops/compass_goalmode.bat 循环调度)。

做三件事,结果写 memory obs(红灯额外醒目标记):
1. recall 探活:对本地 daemon 9876 发真实语义查询,失败/超时 = 引擎红灯
   (治 2026-08-23 发现的"torch 坏死数月无人知")。
2. 合约扫描:memory 目录 session-contract-* 里 due 已过且无 CONSUMED 的 = 悬账红灯。
3. 状态摘要追加到 .cache/goalmode_heartbeat.log(本地仪表)。
"""
from __future__ import annotations

import json
import re
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gep.live_coding_adapter import _structured_content  # noqa: E402,F401

ROOT = Path(__file__).resolve().parents[1]
MEM = Path.home() / ".claude" / "projects" / "C--Users-chunx-Projects-nautilus-compass" / "memory"
LOG = Path.home() / ".claude" / ".cache" / "goalmode_heartbeat.log"
PROBE_QUERY = "loop state 当前唯一下一动作"
CST = timezone(timedelta(hours=8))


def probe_recall() -> tuple[bool, float, str]:
    t0 = time.time()
    try:
        s = socket.create_connection(("127.0.0.1", 9876), timeout=120)
        req = {"action": "recall", "query": PROBE_QUERY, "top_k": 1,
               "scope": "project", "project": "C--Users-chunx-Projects-nautilus-compass"}
        s.sendall((json.dumps(req) + "\n").encode("utf-8"))
        buf = b""
        while not buf.endswith(b"\n"):
            c = s.recv(65536)
            if not c:
                break
            buf += c
        s.close()
        r = json.loads(buf.decode("utf-8"))
        ok = bool(r.get("ok")) and len(r.get("recall", [])) > 0
        return ok, time.time() - t0, "" if ok else str(r.get("error"))[:120]
    except Exception as e:
        return False, time.time() - t0, f"{type(e).__name__}: {e}"[:120]


def scan_contracts() -> list[str]:
    overdue = []
    now = datetime.now(CST)
    for f in MEM.glob("session-contract-*.md"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        if "CONSUMED" in text.split("\n")[2] if len(text.split("\n")) > 2 else False:
            continue
        head = text[:1500]
        if "CONSUMED" in head:
            continue
        m = re.search(r"due:\s*(\d{4}-\d{2}-\d{2})T", head)
        if not m:
            continue
        try:
            due = datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=CST)
        except ValueError:
            continue
        if due < now:
            overdue.append(f"{f.stem} (due {m.group(1)})")
    return overdue


def ingest_obs(name: str, body: str) -> None:
    stdin = "\n".join([
        '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"goalmode"}}}',
        '{"jsonrpc":"2.0","method":"notifications/initialized"}',
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
            "name": "ingest_obs",
            "arguments": {"name": name, "body": body,
                          "project": "C--Users-chunx-Projects-nautilus-compass",
                          "drift": "red" if ("🔴" in body or "FAIL" in body) else "green"}}}),
    ]) + "\n"
    env = dict(__import__("os").environ,
               NAUTILUS_COMPASS_PROJECT="C--Users-chunx-Projects-nautilus-compass",
               PYTHONIOENCODING="utf-8")
    try:
        subprocess.run(
            ["python", r"C:\Users\chunx\.claude\plugins\nautilus-compass\mcp_server.py"],
            input=stdin, capture_output=True, text=True, env=env, timeout=300)
    except Exception:
        pass


def main() -> None:
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M")
    ok, secs, err = probe_recall()
    overdue = scan_contracts()
    status = "OK" if ok else "🔴FAIL"
    line = f"[{now}] recall={status} {secs:.1f}s" + (f" err={err}" if err else "")
    if overdue:
        line += " | overdue_contracts=" + ";".join(overdue)
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    if not ok or overdue:
        ingest_obs(
            "goalmode-heartbeat-alert",
            f"[目标模式心跳红灯 {now}] recall={'FAIL' if not ok else 'ok'} ({err or f'{secs:.1f}s'}); "
            f"过期未核销合约: {overdue or '无'}。来源 tools/compass_goal_heartbeat.py 自动执法。",
        )
        print(line)
        sys.exit(1)
    print(line)


if __name__ == "__main__":
    main()
