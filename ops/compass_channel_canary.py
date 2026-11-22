#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compass 通道金丝雀——外部模型通道死亡时大声报警,不再静默。

背景(2026-11-22 用户拍板建):11/19-11/22 Token Plan 429 断供 3 天,
rounds.log 只留一行小字,降级巡检看到了也只能写给自己看,无人被拍肩膀。

机制:
  · 每 30 分钟(LaunchAgent)用 loop 同款通道发一发 1-token 探活请求
  · 连续 2 次失败 → 报警三件:
      ① 落 runtime/loop/CHANNEL_DOWN 标记(loop 轮次与任意对话框可见)
      ② 发平台函一行 [kind:alert](经 scripts/platform_mail.py,走平台HTTP,与LLM通道无关)
      ③ 追加 runtime/loop/canary.log
  · 恢复 → 撤标记,记 recovery
  · 报警节流:同一场断供最多每 6h 一函
  · 永不抛异常退出(LaunchAgent 不刷屏),一切失败写日志

通道读法:与 claude CLI 同源——~/.claude/settings.json 的 env 段
(ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN / ANTHROPIC_MODEL),
不硬编码端点,换通道本探针自动跟随。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "runtime" / "loop" / "channel_canary_state.json"
DOWN_MARKER = ROOT / "runtime" / "loop" / "CHANNEL_DOWN"
LOG = ROOT / "runtime" / "loop" / "canary.log"
SETTINGS = Path.home() / ".claude" / "settings.json"
ALERT_COOLDOWN_S = 6 * 3600
FAIL_THRESHOLD = 2


def _env() -> dict:
    d = json.loads(SETTINGS.read_text(encoding="utf-8")).get("env", {})
    return {k: v for k, v in d.items() if isinstance(v, str)}


def _log(line: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")


def _probe(env: dict) -> tuple[bool, str]:
    base = env.get("ANTHROPIC_BASE_URL", "https://open.bigmodel.cn/api/anthropic").rstrip("/")
    token = env.get("ANTHROPIC_AUTH_TOKEN", "")
    model = env.get("ANTHROPIC_MODEL") or env.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "")
    body = json.dumps({"model": model, "max_tokens": 1,
                       "messages": [{"role": "user", "content": "ok"}]}).encode()
    req = urllib.request.Request(
        base + "/v1/messages", data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {token}",
                 "x-api-key": token,
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status == 200, f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        snippet = ""
        try:
            snippet = e.read(200).decode(errors="replace")
        except Exception:
            pass
        return False, f"HTTP {e.code} {snippet}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _send_platform_letter(reason: str) -> None:
    """平台函走平台 HTTP,与 LLM 通道无关——通道死也能发出去。失败只记日志。"""
    subject = "[kind:alert] compass 通道金丝雀:外部模型通道死亡"
    body = (f"金丝雀连续 {FAIL_THRESHOLD} 次探活失败,值守轮将静默零产出。\n"
            f"失败原因: {reason}\n"
            f"标记文件: runtime/loop/CHANNEL_DOWN(恢复后自动撤除)\n"
            f"—— ops/compass_channel_canary.py 自动执法")
    bf = ROOT / "runtime" / "loop" / ".canary_alert_body.txt"
    bf.write_text(body, encoding="utf-8")
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "platform_mail.py"),
             "send", "compass", f"channel-canary-{time.strftime('%Y%m%d-%H%M')}",
             subject, str(bf)],
            capture_output=True, text=True, timeout=60)
        _log(f"alert letter rc={r.returncode} out={ (r.stdout or '')[:120] }")
    except Exception as e:
        _log(f"alert letter FAILED: {type(e).__name__}: {e}")


def main() -> int:
    now = int(time.time())
    st = {"streak": 0, "last_ok": 0, "last_alert": 0}
    try:
        st.update(json.loads(STATE.read_text(encoding="utf-8")))
    except Exception:
        pass
    ok, reason = _probe(_env())
    if ok:
        if st["streak"] >= FAIL_THRESHOLD or DOWN_MARKER.exists():
            _log(f"RECOVERED (was down streak={st['streak']})")
        st.update(streak=0, last_ok=now)
        DOWN_MARKER.unlink(missing_ok=True)
    else:
        st["streak"] = int(st.get("streak", 0)) + 1
        _log(f"FAIL streak={st['streak']} · {reason}")
        if st["streak"] >= FAIL_THRESHOLD:
            DOWN_MARKER.parent.mkdir(parents=True, exist_ok=True)
            DOWN_MARKER.write_text(f"{now} {reason}\n", encoding="utf-8")
            if now - int(st.get("last_alert") or 0) > ALERT_COOLDOWN_S:
                st["last_alert"] = now
                _send_platform_letter(reason)
    try:
        STATE.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
