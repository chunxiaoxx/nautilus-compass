"""Daily cost ceiling gate · reads/writes JSONL cost ledger."""
from __future__ import annotations
import json
from datetime import datetime, timezone

from soul.config import COST_LEDGER, DAILY_COST_CAP_USD


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def today_cost() -> float:
    if not COST_LEDGER.exists():
        return 0.0
    total = 0.0
    today = _today()
    with open(COST_LEDGER, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("date") == today:
                try:
                    total += float(row.get("cost_usd", 0.0))
                except (ValueError, TypeError):
                    continue
    return total


def under_cap() -> bool:
    return today_cost() < DAILY_COST_CAP_USD


def record_cost(cost_usd: float, cycle_id: str) -> None:
    COST_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "date": _today(),
        "ts": datetime.now(timezone.utc).isoformat(),
        "cost_usd": float(cost_usd),
        "cycle_id": cycle_id,
    }
    with COST_LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")