import json
from datetime import datetime, timezone

from soul import budget_gate


def test_under_cap_allows(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ledger.write_text(json.dumps({"date": today, "cost_usd": 5.0}) + "\n")
    monkeypatch.setattr(budget_gate, "COST_LEDGER", ledger)
    monkeypatch.setattr(budget_gate, "DAILY_COST_CAP_USD", 20.0)
    assert budget_gate.under_cap() is True


def test_over_cap_blocks(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ledger.write_text(json.dumps({"date": today, "cost_usd": 25.0}) + "\n")
    monkeypatch.setattr(budget_gate, "COST_LEDGER", ledger)
    monkeypatch.setattr(budget_gate, "DAILY_COST_CAP_USD", 20.0)
    assert budget_gate.under_cap() is False


def test_record_appends(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(budget_gate, "COST_LEDGER", ledger)
    budget_gate.record_cost(0.003, "cycle_abc")
    lines = ledger.read_text().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["cost_usd"] == 0.003


def test_yesterday_cost_ignored(tmp_path, monkeypatch):
    """Cost cap is per-day: a prior day's spend must not block today."""
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps({"date": "2000-01-01", "cost_usd": 999.0}) + "\n")
    monkeypatch.setattr(budget_gate, "COST_LEDGER", ledger)
    monkeypatch.setattr(budget_gate, "DAILY_COST_CAP_USD", 20.0)
    assert budget_gate.today_cost() == 0.0
    assert budget_gate.under_cap() is True
