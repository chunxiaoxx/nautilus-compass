"""Tests for the SWE-bench prediction JSONL writer (Phase 4 Task 5).

The official ``swebench`` harness consumes one JSON object per line with exactly
``instance_id`` / ``model_patch`` / ``model_name_or_path``. An empty patch is a
valid (unresolved) prediction and must be preserved, never dropped.
"""
import json

from predictions import write_predictions, KEYS


def test_one_line_per_item_with_exact_keys(tmp_path):
    path = tmp_path / "preds.jsonl"
    write_predictions(
        path, model_name="MiniMax-M3",
        items=[{"instance_id": "a", "model_patch": "diff1"},
               {"instance_id": "b", "model_patch": "diff2"}],
    )
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    rec = json.loads(lines[0])
    assert set(rec.keys()) == KEYS
    assert rec["instance_id"] == "a"
    assert rec["model_patch"] == "diff1"
    assert rec["model_name_or_path"] == "MiniMax-M3"


def test_empty_patch_preserved(tmp_path):
    path = tmp_path / "preds.jsonl"
    write_predictions(path, model_name="m",
                      items=[{"instance_id": "a", "model_patch": ""}])
    rec = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert rec["model_patch"] == ""


def test_per_item_model_name_override(tmp_path):
    path = tmp_path / "preds.jsonl"
    write_predictions(
        path, model_name="default",
        items=[{"instance_id": "a", "model_patch": "d",
                "model_name_or_path": "arm3-decomp"}],
    )
    rec = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert rec["model_name_or_path"] == "arm3-decomp"


def test_returns_count_written(tmp_path):
    path = tmp_path / "preds.jsonl"
    n = write_predictions(path, model_name="m",
                          items=[{"instance_id": "a", "model_patch": "d"}])
    assert n == 1
