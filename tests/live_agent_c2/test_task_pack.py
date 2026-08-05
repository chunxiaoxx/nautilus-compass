from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks.live_agent_c2.schema import QUERY_CLASSES
from benchmarks.live_agent_c2.task_pack import (
    DEFAULT_TASK_PACK_PATH,
    pack_from_mapping,
    read_task_pack,
)


def valid_pack_mapping():
    return json.loads(DEFAULT_TASK_PACK_PATH.read_text(encoding="utf-8"))


def test_committed_pack_is_deidentified_complete_and_deterministic():
    pack = read_task_pack()

    assert pack.schema_version == "compass.live_agent_c2.task_pack.v1"
    assert pack.seed == 2486
    assert len(pack.tasks) == 8
    assert {task.query_class for task in pack.tasks} == set(QUERY_CLASSES)
    assert pack.protected_query_classes == ("protected_noop",)
    assert tuple(task.task_id for task in pack.tasks) == tuple(
        sorted(task.task_id for task in pack.tasks)
    )
    assert len(pack.task_hashes) == len(set(pack.task_hashes)) == len(pack.tasks)
    assert pack.pack_hash == read_task_pack().pack_hash
    assert not any(task.memory_text for task in pack.tasks if task.protected)


def test_pack_hash_is_independent_of_json_object_key_order(tmp_path: Path):
    raw = valid_pack_mapping()
    reordered = {key: raw[key] for key in reversed(tuple(raw))}
    path = tmp_path / "reordered.json"
    path.write_text(json.dumps(reordered), encoding="utf-8")

    assert read_task_pack(path).pack_hash == read_task_pack().pack_hash


def test_pack_rejects_duplicate_ids_unsorted_tasks_and_missing_query_class():
    raw = valid_pack_mapping()
    raw["tasks"][1]["task_id"] = raw["tasks"][0]["task_id"]
    with pytest.raises(ValueError, match="duplicate task_id"):
        pack_from_mapping(raw)

    raw = valid_pack_mapping()
    raw["tasks"] = list(reversed(raw["tasks"]))
    with pytest.raises(ValueError, match="sorted"):
        pack_from_mapping(raw)

    raw = valid_pack_mapping()
    raw["tasks"] = [
        item for item in raw["tasks"] if item["query_class"] != "conflict_resolution"
    ]
    with pytest.raises(ValueError, match="every frozen query_class"):
        pack_from_mapping(raw)


def test_pack_rejects_unknown_fields_bad_protected_class_and_duplicate_json_keys(
    tmp_path: Path,
):
    raw = valid_pack_mapping()
    raw["source_url"] = "forbidden"
    with pytest.raises(TypeError, match="unknown C2TaskPack fields"):
        pack_from_mapping(raw)

    raw = valid_pack_mapping()
    raw["protected_query_classes"] = []
    with pytest.raises(ValueError, match="protected_query_classes"):
        pack_from_mapping(raw)

    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(
        '{"schema_version":"compass.live_agent_c2.task_pack.v1",'
        '"schema_version":"duplicate"}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate JSON key"):
        read_task_pack(duplicate)
