"""compass × Nautilus stake module · #4 fusion · drift event consumer.

Pretend we are the Nautilus stake module · poll compass for drift events ·
apply stake_penalty / stake_bonus to agents based on AI self-audit.

Background: see paper/STAKE_DRIFT_COUPLING.md for the spec.

Real implementation:
  - Nautilus stake module on cloud server (43.160.239.61) imports this
  - Polls ~/.compass/stake_events/*.json every 60s
  - For each event:
      drift=red    → burn 1% of agent's locked stake (drift signal evidence required)
      drift=green  → reward 0.1% of locked stake
      drift=yellow → no action
  - Marks event as processed (rename to .processed.json)
  - Logs to chain (USDC ledger) for audit

Anti-cheat: see paper/STAKE_DRIFT_COUPLING.md §"反作弊设计".
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

EVENTS_DIR = Path.home() / ".compass" / "stake_events"
PROCESSED_DIR = EVENTS_DIR / "processed"

# Anti-cheat thresholds
DRIFT_RED_PENALTY_PCT = 1.0     # 1% of locked stake
DRIFT_GREEN_BONUS_PCT = 0.1     # 0.1%
MIN_DRIFT_SIGNALS_FOR_RED = 1   # red drift 必须有 ≥1 个 signal · 防虚报


class FakeStakeModule:
    """A simulator · in production this is a real Nautilus stake service with USDC ledger."""

    def __init__(self):
        self.balances = {}      # agent_id → locked_usdc

    def get_locked(self, agent_id: str) -> float:
        return self.balances.get(agent_id, 100.0)  # default 100 USDC for demo

    def apply_penalty(self, agent_id: str, amount: float, reason: str) -> dict:
        bal = self.get_locked(agent_id)
        burned = min(amount, bal)
        self.balances[agent_id] = bal - burned
        print(f"  ⛔ stake_penalty: {agent_id} burned {burned:.4f} USDC ({reason})")
        return {"ok": True, "burned": burned, "reason": reason}

    def apply_bonus(self, agent_id: str, amount: float, reason: str) -> dict:
        bal = self.get_locked(agent_id)
        self.balances[agent_id] = bal + amount
        print(f"  💚 stake_bonus: {agent_id} +{amount:.4f} USDC ({reason})")
        return {"ok": True, "rewarded": amount, "reason": reason}


def consume_event(event: dict, stake: FakeStakeModule) -> dict:
    """Process one drift event · return action result."""
    drift = event.get("drift") or event.get("type")
    agent_id = event.get("agent_id")
    user_id = event.get("user_id")
    signals = event.get("signals") or event.get("drift_signals") or []

    if not agent_id:
        return {"skip": True, "reason": "no agent_id"}

    locked = stake.get_locked(agent_id)
    print(f"  · agent={agent_id} · locked={locked:.2f} USDC · drift={drift} · signals={len(signals)}")

    # Anti-cheat: red drift 必须有 signals
    if drift == "drift_red" or drift == "red":
        if len(signals) < MIN_DRIFT_SIGNALS_FOR_RED:
            print(f"  ⚠️ drift=red but no signals · downgrading to yellow (anti-cheat)")
            drift = "yellow"

    if drift == "drift_red" or drift == "red":
        return stake.apply_penalty(
            agent_id=agent_id,
            amount=locked * DRIFT_RED_PENALTY_PCT / 100,
            reason=f"red_drift · {signals[0] if signals else '?'}",
        )

    if drift == "drift_green" or drift == "green":
        return stake.apply_bonus(
            agent_id=agent_id,
            amount=locked * DRIFT_GREEN_BONUS_PCT / 100,
            reason="green_drift",
        )

    return {"skip": True, "reason": f"yellow or unknown drift={drift}"}


def poll_loop(stake: FakeStakeModule, run_once: bool = False, interval: int = 60):
    """Main loop · poll EVENTS_DIR · process · move to processed."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        if not EVENTS_DIR.exists():
            print(f"[stake] events dir {EVENTS_DIR} not exists · waiting")
            if run_once:
                return
            time.sleep(interval)
            continue

        events = sorted(EVENTS_DIR.glob("*.json"))
        if not events:
            print(f"[stake] no pending events at {EVENTS_DIR}")
            if run_once:
                return
            time.sleep(interval)
            continue

        print(f"[stake] processing {len(events)} pending events:")
        for ev_path in events:
            try:
                ev = json.loads(ev_path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"  · {ev_path.name}: bad JSON {e} · move to processed/")
                ev_path.rename(PROCESSED_DIR / ev_path.name)
                continue
            result = consume_event(ev, stake)
            if not result.get("skip"):
                # Mark as processed
                ev_path.rename(PROCESSED_DIR / ev_path.name)

        if run_once:
            return
        time.sleep(interval)


def demo():
    """Generate fake events + consume."""
    print("=" * 60)
    print("stake×drift event consumer demo · #4 fusion")
    print("=" * 60)

    EVENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate 3 fake events
    fake_events = [
        {
            "ts": "2026-05-05T10:00:00Z", "type": "drift_red",
            "agent_id": "ag_hermes_loop_main", "user_id": "u_demo",
            "signals": ["3 次重派同一 issue", "未分析失败原因"],
            "suggested_penalty_pct": 1.0,
        },
        {
            "ts": "2026-05-05T10:01:00Z", "type": "drift_green",
            "agent_id": "ag_openclaw_strategy", "user_id": "u_demo",
            "signals": [],
        },
        {
            "ts": "2026-05-05T10:02:00Z", "type": "drift_red",
            "agent_id": "ag_fake_red_no_signal", "user_id": "u_demo",
            "signals": [],   # no signals · should downgrade to yellow (anti-cheat)
        },
    ]
    for i, ev in enumerate(fake_events):
        ts = int(time.time() * 1000) + i
        path = EVENTS_DIR / f"demo_{ts}.json"
        path.write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[demo] wrote fake event: {path.name}")

    print()
    print("[stake] starting consumer (run_once=True)...")
    stake = FakeStakeModule()
    poll_loop(stake, run_once=True, interval=0)
    print()
    print(f"[stake] final balances: {stake.balances}")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        print("Usage:")
        print("  python stake_drift_event_consumer.py --demo")
        print("  # Or in production: import poll_loop · pass real Nautilus stake module")
