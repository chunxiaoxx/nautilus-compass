from __future__ import annotations

import json

import pytest

from benchmarks.live_agent_c2.checkpoints import CheckpointStore


def test_orphaned_started_pair_becomes_terminal_interrupted_on_resume(tmp_path):
    store = CheckpointStore(tmp_path)
    store.initialize()
    store.mark_started("c2_pair_aaaaaaaa")

    store.prepare_resume()

    checkpoint = store.checkpoints()[0]
    assert checkpoint["pair_id"] == "c2_pair_aaaaaaaa"
    assert checkpoint["status"] == "interrupted"
    assert checkpoint["failure_codes"] == ["executor_interrupted"]
    assert checkpoint["invalid_attempt_count"] == 1


def test_checkpoint_hash_tampering_fails_closed(tmp_path):
    store = CheckpointStore(tmp_path)
    store.initialize()
    store.mark_started("c2_pair_bbbbbbbb")
    store.write_checkpoint(
        pair_id="c2_pair_bbbbbbbb",
        status="incomplete",
        bundles=(),
        outcome=None,
        invalid_attempt_count=2,
        retry_count=1,
        failure_codes=("provider_timeout",),
    )
    path = next(store.directory.glob("*.json"))
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["retry_count"] = 0
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="checkpoint hash mismatch"):
        store.checkpoints()
