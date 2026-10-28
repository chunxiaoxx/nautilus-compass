"""Manual pause + circuit-breaker pause check.

A sentinel file (PAUSE_FILE) toggles autonomous Soul off at runtime with no
restart: create it to pause, delete it to resume. The circuit breaker
(failure_track) also writes it to halt after repeated failures.

熔断分层(2026-09-25 用户批,#1011 承诺):pause 分两层——
- 人工 pause(文件内容非 BREAKER_PREFIX 前缀)= 人监门至上,全停(含回函);
- breaker 自动熔断 = 只断 ship 高危路径(selfimprove/patch-ship),
  回函/呼救通道保活。病根:9/25 02:08 二次熔断后 breaker 全停,
  回函通道同死 → 组织失明 17h 无人知(GitHub issue 无人盯)。
"""
from __future__ import annotations

from soul.config import PAUSE_FILE

# failure_track 熔断写入的 pause 文件前缀(判层依据,改此处须同步 failure_track)。
BREAKER_PREFIX = "circuit breaker"


def is_paused() -> bool:
    return PAUSE_FILE.exists()


def pause_origin() -> "str | None":
    """None = 未 pause;'breaker' = 熔断自动暂停;'manual' = 人工暂停。

    文件存在但读不出 → 按 manual 处理(fail-safe 向人工侧,人监门至上)。"""
    if not PAUSE_FILE.exists():
        return None
    try:
        content = PAUSE_FILE.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return "manual"
    return "breaker" if content.startswith(BREAKER_PREFIX) else "manual"


def ship_blocked() -> bool:
    """ship 高危路径(selfimprove/patch-ship)任一 pause 层都断。"""
    return is_paused()


def letters_blocked() -> bool:
    """回函/呼救通道只有人工 pause 才断;breaker 自动熔断保活。"""
    return pause_origin() == "manual"


def engage_pause(reason: str) -> None:
    PAUSE_FILE.write_text(reason, encoding="utf-8")


def lift_pause() -> None:
    PAUSE_FILE.unlink(missing_ok=True)
