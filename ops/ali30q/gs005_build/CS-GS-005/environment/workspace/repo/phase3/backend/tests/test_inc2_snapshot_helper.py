"""Inc 2 Slice 1 · _snapshot_engine_cycle_outcomes helper."""
from unittest.mock import MagicMock

import pytest

from services.inc2_settlement import _snapshot_engine_cycle_outcomes


def test_snapshot_aggregates_basic_metrics():
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = (
        100,   # total_cycles
        85,    # successful_cycles
        0.85,  # success_rate
    )
    result = _snapshot_engine_cycle_outcomes(db)
    assert result == {
        "total_cycles": 100,
        "successful_cycles": 85,
        "success_rate": 0.85,
    }
    assert db.execute.called


def test_snapshot_handles_no_data():
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = (0, 0, None)
    result = _snapshot_engine_cycle_outcomes(db)
    assert result == {
        "total_cycles": 0,
        "successful_cycles": 0,
        "success_rate": None,
    }
