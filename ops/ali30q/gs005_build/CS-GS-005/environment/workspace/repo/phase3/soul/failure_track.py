"""Circuit breaker · N consecutive failures → engage pause + alert.

Persists a consecutive-failure counter; when it reaches MAX_CONSECUTIVE_FAILURES
it engages the pause file (halting autonomous cycles) and files a GitHub issue.
A success resets the counter.
"""
from __future__ import annotations
import json
import subprocess

from soul import pause_check
from soul.config import FAILURE_STATE, MAX_CONSECUTIVE_FAILURES, GITHUB_REPO


def _read() -> int:
    if not FAILURE_STATE.exists():
        return 0
    try:
        return int(json.loads(FAILURE_STATE.read_text()).get("consecutive", 0))
    except Exception:
        return 0


def _write(n: int) -> None:
    FAILURE_STATE.parent.mkdir(parents=True, exist_ok=True)
    FAILURE_STATE.write_text(json.dumps({"consecutive": n}), encoding="utf-8")


def _alert(msg: str) -> None:
    subprocess.run(
        ["gh", "issue", "create", "--repo", GITHUB_REPO,
         "--title", "Soul circuit breaker engaged", "--body", msg],
        capture_output=True, text=True,
    )


def _distress_letter(msg: str) -> None:
    """呼救通道(9/25 熔断分层):熔断瞬间投函 org_mailbox → platform。

    GitHub issue 无人盯(9/25 实证:02:08 熔断,17h 后用户追问才发现);
    org_mailbox 是值守轮每轮必扫通道,呼救函落账=组织必见。
    任何失败静默(不阻塞熔断本身;lazy import 同 daemon 配方)。"""
    try:
        from datetime import datetime as _dt, timedelta as _td
        import models.agent_survival  # noqa: F401 — mapper dependency
        from models.org_mailbox import OrgMailbox
        from utils.database import SessionLocal
        s = SessionLocal()
        try:
            trace = f"soul-distress-{_dt.now():%Y%m%d%H%M}"
            if not s.query(OrgMailbox).filter_by(trace_id=trace,
                                                 to_agent="platform").first():
                s.add(OrgMailbox(
                    from_agent="soul", to_agent="platform", trace_id=trace,
                    title="[呼救·熔断] soul breaker engaged — ship 路径已断,回函通道保活",
                    body=("熔断分层(9/25 用户批)生效:本函经保活通道发出。\n\n" + msg[:1800]),
                    deadline=_dt.now() + _td(hours=2), created_at=_dt.now()))
                s.commit()
        finally:
            s.close()
    except Exception:  # noqa: BLE001 — 呼救失败不阻塞熔断
        pass


def record_failure(cycle_id: str) -> int:
    """Increment consecutive failures. At the cap, engage pause + alert. Returns count."""
    n = _read() + 1
    _write(n)
    if n == MAX_CONSECUTIVE_FAILURES:
        pause_check.engage_pause(
            f"circuit breaker · {n} consecutive failures · last={cycle_id}"
        )
        _alert(f"Soul paused after {n} consecutive failures (last cycle {cycle_id}).")
        _distress_letter(
            f"{n} consecutive failures · last cycle {cycle_id} · "
            "ship/selfimprove 已断;回函通道保活中;解除=人工删 .soul-pause(人监门)。")
    return n


def record_success() -> None:
    _write(0)