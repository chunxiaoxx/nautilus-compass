# -*- coding: utf-8 -*-
"""框常驻 worker v0.1 — 对话框降级为驾驶舱(2026-09-18 用户定调,方案函 403-406)。

落点:各框仓所在机器(飞轮=本地 Windows schtasks,同 g2b1 executor 配方)。
每轮:经 mailbox HTTP API(带 X-API-Key)拉本框未读函 → 裁决类转呈哨兵
→ 其余逐封 claude headless 在本框仓执行 → 回函/审计。
compass 408 两边界已采纳:裁决白名单显式化+对裁判也记账。

用法:python ops/frame_worker.py <frame>
环境:FRAME_WORKER_<FRAME>_DIR / FRAME_API_BASE / FRAME_API_KEY
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta

import requests

# 裁决类白名单(只转呈不代拍)
DECIDE_PAT = ("判据注册", "判据修订", "开考", "重考", "判卷", "成绩单签发",
              "对外承诺", "批准", "裁决", "拍板")

BASE = os.environ.get("FRAME_API_BASE", "https://www.nautilus.social")
KEY = os.environ.get("FRAME_API_KEY", "")


def _call(prefix: str, path: str, payload: dict | None = None) -> dict:
    """HTTP 层走 requests(9/20 实测:本地网络中间层干扰 Python urllib TLS 指纹,
    curl/requests(urllib3)通而 urllib 稳定 SSL EOF——worker 全量换 requests)。"""
    r = requests.request("POST" if payload is not None else "GET", BASE + prefix + path,
                         json=payload, headers={"X-API-Key": KEY}, timeout=60)
    if r.status_code >= 400:
        # 统一 409 语义在 _post_mail;此处抛带码异常
        class _HttpErr(Exception):
            pass
        e = _HttpErr(f"HTTP {r.status_code}: {r.text[:200]}")
        e.status_code = r.status_code
        raise e
    return r.json()


def _api(path: str, payload: dict | None = None) -> dict:
    return _call("/api/platform/org", path, payload)


def _fde(path: str, payload: dict | None = None) -> dict:
    return _call("/api/platform/fde", path, payload)


def _post_mail(from_a: str, to_a: str, trace: str, title: str, body: str) -> dict:
    """投函;409=同 trace 已存在(幂等成功),其余异常向上抛。"""
    try:
        return _api("/mailbox", {
            "from_agent": from_a, "to_agent": to_a, "trace_id": trace,
            "title": title[:200], "body": body, "task_meta": None, "meta": None,
            "deadline": (datetime.now() + timedelta(hours=2)).isoformat(),
        })
    except Exception as e:  # noqa: BLE001
        if getattr(e, "status_code", None) == 409:
            return {"idempotent": True}
        raise


def _ack(mid: int, note: str) -> None:
    try:
        _api(f"/mailbox/{mid}/ack", {"note": note})
    except Exception:  # noqa: BLE001 — ack 失败不阻断,下轮会重拉(幂等审计 trace 挡重函)
        pass


def _headless(prompt: str, repo: str | None, max_turns: int = 12, timeout: int = 1500) -> str:
    """claude headless 执行(prompt 走 stdin——v0.2 命令行截断教训),返回 stdout 尾部。"""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
        tf.write(prompt)
        prompt_path = tf.name
    try:
        cmd = ("claude -p --max-turns %d "
               '--allowedTools "Read" "Write" "Edit" "Bash" "Grep" "Glob" < %s'
               % (max_turns, prompt_path))
        # 9/20 实测:本地 socks5h:// 代理 env 使 claude CLI 报 UnsupportedProxyProtocol
        # 假交卷(prime 三题全 API Error)——子进程剥离 socks 系代理,http 代理保留。
        import copy
        env = dict(os.environ)
        for k in ("https_proxy", "http_proxy", "all_proxy",
                  "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY"):
            v = env.get(k, "")
            if v.startswith("socks"):
                env.pop(k, None)
        proc = subprocess.run(cmd, cwd=repo or None, capture_output=True,
                              text=True, timeout=timeout,
                              shell=True, env=env)  # 20261022 Mac 适配:整串命令需 sh 解析(win32 原 shell=platform 判定)
        return proc.stdout or ""  # 全量返回:5000 截尾曾致交付物丢头(9/20 三臂实证,report 侧自有上限)
    finally:
        try:
            os.unlink(prompt_path)
        except OSError:
            pass


def run_dispatch_tasks(frame: str, repo: str | None) -> int:
    """P2 任务源(RSI 蓝图 worker v1.0 目标源的 v0 接线):

    拉 dispatch 里 reserved_for=本框的 open 任务 → claim → headless 执行
    → report。三臂 prime/v7 接入用(9/20 用户拍板,复用现成 worker 件);
    同引擎对照=框级 harness 对照(组织六框本同引擎,差异在流程/上下文)。
    409(已claim)/403(非本框)→ 跳过;report 成功即一轮产出。
    """
    try:
        tasks = _fde("/tasks").get("data", {}).get("tasks") or []
    except Exception as e:  # noqa: BLE001 — 观测源故障不阻塞信箱主职责
        print(f"dispatch source unavailable: {e}")
        return 0
    mine = [t for t in tasks if t.get("status") == "open" and t.get("reserved_for") == frame]
    for t in mine:
        uid = t["task_uid"]
        desc = t.get("description") or ""
        try:
            d = json.loads(desc)
            desc = d.get("_original_description") or desc  # 置回结构解包
        except Exception:
            pass
        try:
            _fde("/claim", {"task_uid": uid, "agent_id": frame})
        except Exception as e:  # noqa: BLE001 — 409/403/网络失败 → 跳过本轮该任务
            print(f"claim {uid} -> {getattr(e, 'status_code', e)}, skip")
            continue
        print(f"CLAIMED {uid}")
        prompt = (f"你是 nautilus 组织 {frame} 框的值守 worker,领到平台任务 {uid}。\n"
                  f"=== 任务全文 ===\n{desc}\n=== 任务结束 ===\n\n"
                  f"要求:只用文件工具(Read/Write/Edit/Bash/Grep/Glob)在工作目录({repo})干活,"
                  f"不要使用任何 MCP 工具(headless 环境未授权)。"
                  f"按任务要求产出交付物(修复后完整文件或 unified diff),在本地留档;"
                  f"**交付文件名必须与任务里 starter 文件路径同名**(663 判材对齐要求);"
                  f"最终输出打印交付物全文(代码用代码围栏包裹)+ 一段三行内说明。"
                  f"不修改判据、不对外承诺、不动 git remote、禁查任何历史答案。")
        try:
            out = _headless(prompt, repo, max_turns=16, timeout=2400)
        except Exception as e:  # noqa: BLE001 — 执行失败留 claimed,下轮 reap 走回收
            print(f"EXEC FAIL {uid}: {e}")
            continue
        # 防假绿(9/20 prime 三题 API Error 假交卷实证):错误文本不上报,
        # 留 claimed 由 reap 回收重试
        if not out.strip() or "API Error" in out[:200] or len(out.strip()) < 80:
            print(f"BAD OUTPUT {uid} (len={len(out)}), not reported")
            continue
        _fde("/report", {"task_uid": uid, "agent_id": frame,
                         "output": {"text": out[:40000], "worker": "frame_worker v0.4"}})
        print(f"REPORTED {uid} ({len(out)} chars)")
    return 0


def run(frame: str) -> int:
    if not KEY:
        print("no FRAME_API_KEY")
        return 2
    env_frame = "".join(c if c.isalnum() else "_" for c in frame.upper())
    repo = os.environ.get(f"FRAME_WORKER_{env_frame}_DIR")
    run_dispatch_tasks(frame, repo)  # P2 任务源(信箱之外的第二源)
    rows = _api(f"/mailbox?to={frame}&unread=1").get("data") or []
    todo = [r for r in rows
            if not (r.get("trace_id") or "").startswith(("worker-audit", "platform-urge"))]
    if not todo:
        print("idle: no pending letters")
        return 0
    for r in todo:
        rid, title, body = r["id"], r.get("title") or "", r.get("body") or ""
        trace = r.get("trace_id") or f"id{rid}"
        if any(p in title for p in DECIDE_PAT):
            _post_mail(frame, "platform", f"{trace}-escalated",
                       f"[worker转呈] 裁决类待人工 id{rid}", f"「{title[:60]}」worker 不代拍,哨兵已推用户。")
            _ack(rid, "worker: escalated to human")
            print(f"ESCALATE id{rid}: {title[:40]}")
            continue
        # v0.2:prompt 走 stdin(命令行传参被截断,id442 实证);只文件工具禁 MCP
        # (headless 无交互授权);"没取到函"不 ack 留待重试(v0.1 假清零教训)。
        import tempfile
        prompt = (f"你是 nautilus 组织 {frame} 框的值守 worker。函件全文如下:\n"
                  f"=== 函件开始 ===\n[id {rid}] {title}\n{body}\n=== 函件结束 ===\n\n"
                  f"要求:只用文件工具(Read/Write/Edit/Bash/Grep/Glob)在本仓({repo})干活,"
                  f"不要使用任何 MCP 工具(headless 环境未授权)。"
                  f"能执行则执行并在仓内留痕;不能执行或需人拍板,如实说明。"
                  f"完成后把给平台的回函全文(首行 VERDICT: ...)作为最终输出打印。"
                  f"不修改判据、不对外承诺、不动 git remote。")
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
            tf.write(prompt)
            prompt_path = tf.name
        cmd = ("claude -p --max-turns 12 "
               '--allowedTools "Read" "Write" "Edit" "Bash" "Grep" "Glob" < ' + prompt_path)
        # v0.3 失败熔断(484):同函已 fail>=2 次 → ack 放弃,防无限空转重试
        try:
            fails = _api(f"/mailbox?to={frame}&unread=1").get("data") or []
        except Exception:
            fails = []
        # (轻量:靠下述 except 路径里审计 trace 不可查,改用本地状态文件计数)
        st_path = os.path.join(os.environ.get("TEMP", "/tmp"), f"fw_{frame}_fails.json")
        try:
            fails_map = json.loads(open(st_path).read())
        except Exception:
            fails_map = {}
        if fails_map.get(str(rid), 0) >= 2:
            _ack(rid, f"worker: abandoned after {fails_map[str(rid)]} fails")
            print(f"ABANDON id{rid} (fuse)")
            os.unlink(prompt_path)
            continue
        try:
            proc = subprocess.run(cmd, cwd=repo or None, capture_output=True,
                                  text=True, timeout=1500, shell=True)  # 20261022 Mac 适配:整串命令需 sh 解析
            out = (proc.stdout or "")[-500:]
            _post_mail(frame, "platform", f"{trace}-workered",
                       f"[worker审计] id{rid} 执行记录",
                       f"rc={proc.returncode}\n{out}")
            print(f"EXEC id{rid}: rc={proc.returncode}")
        except Exception as e:  # noqa: BLE001
            fails_map[str(rid)] = fails_map.get(str(rid), 0) + 1
            try:
                open(st_path, "w").write(json.dumps(fails_map))
            except Exception:
                pass
            print(f"FAIL id{rid} ({fails_map[str(rid)]}/3): {e}")   # 3 次熔断
        finally:
            os.unlink(prompt_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1] if len(sys.argv) > 1 else "flywheel"))
