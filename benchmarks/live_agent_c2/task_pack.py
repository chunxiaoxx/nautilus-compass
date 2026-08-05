"""Frozen deidentified task-pack loader for Compass C2."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from benchmarks.poi_gate2.canonical import canonical_json_bytes, hash_json

from .schema import QUERY_CLASSES, LiveTask, task_from_mapping, task_to_mapping


TASK_PACK_SCHEMA = "compass.live_agent_c2.task_pack.v1"
DEFAULT_TASK_PACK_PATH = Path(__file__).parent / "fixtures" / "c2" / "task_pack.json"


class _DuplicateJsonKeyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class C2TaskPack:
    schema_version: str
    pack_id: str
    seed: int
    protected_query_classes: tuple[str, ...]
    tasks: tuple[LiveTask, ...]
    task_hashes: tuple[str, ...] = field(init=False)
    pack_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != TASK_PACK_SCHEMA:
            raise ValueError(f"schema_version must be {TASK_PACK_SCHEMA}")
        if not isinstance(self.pack_id, str) or not self.pack_id.startswith("c2_pack_"):
            raise ValueError("pack_id must be a stable c2_pack_ identifier")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError("seed must be a non-negative integer")
        if self.protected_query_classes != ("protected_noop",):
            raise ValueError("protected_query_classes must contain only protected_noop")
        _validate_tasks(self.tasks)
        task_hashes = tuple(task.task_hash for task in self.tasks)
        object.__setattr__(self, "task_hashes", task_hashes)
        object.__setattr__(self, "pack_hash", hash_json(pack_to_mapping(self)))

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(pack_to_mapping(self)) + b"\n"


def pack_from_mapping(raw: Mapping[str, Any]) -> C2TaskPack:
    expected = {
        "schema_version",
        "pack_id",
        "seed",
        "protected_query_classes",
        "tasks",
    }
    values = _exact_mapping("C2TaskPack", raw, expected)
    protected = _sequence("protected_query_classes", values["protected_query_classes"])
    task_rows = _sequence("tasks", values["tasks"])
    tasks = tuple(task_from_mapping(item) for item in task_rows)
    return C2TaskPack(
        schema_version=values["schema_version"],
        pack_id=values["pack_id"],
        seed=values["seed"],
        protected_query_classes=protected,
        tasks=tasks,
    )


def pack_to_mapping(pack: C2TaskPack) -> dict[str, Any]:
    if not isinstance(pack, C2TaskPack):
        raise TypeError("pack must be a C2TaskPack")
    return {
        "schema_version": pack.schema_version,
        "pack_id": pack.pack_id,
        "seed": pack.seed,
        "protected_query_classes": list(pack.protected_query_classes),
        "tasks": [task_to_mapping(task) for task in pack.tasks],
    }


def read_task_pack(path: Optional[Path] = None) -> C2TaskPack:
    source = DEFAULT_TASK_PACK_PATH if path is None else Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    except _DuplicateJsonKeyError as exc:
        raise ValueError(str(exc)) from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid task pack JSON") from exc
    return pack_from_mapping(raw)


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _exact_mapping(label: str, raw: Mapping[str, Any], expected: set[str]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise TypeError(f"{label} must be a mapping")
    if any(not isinstance(key, str) for key in raw):
        raise TypeError(f"{label} field names must be strings")
    unknown = set(raw) - expected
    missing = expected - set(raw)
    if unknown:
        raise TypeError(f"unknown {label} fields: {', '.join(sorted(unknown))}")
    if missing:
        raise TypeError(f"missing {label} fields: {', '.join(sorted(missing))}")
    return {name: raw[name] for name in expected}


def _sequence(name: str, raw: Any) -> tuple[Any, ...]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise TypeError(f"{name} must be a sequence")
    return tuple(raw)


def _validate_tasks(tasks: tuple[LiveTask, ...]) -> None:
    if not tasks or any(not isinstance(task, LiveTask) for task in tasks):
        raise ValueError("tasks must contain LiveTask values")
    task_ids = tuple(task.task_id for task in tasks)
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("tasks contain duplicate task_id values")
    if task_ids != tuple(sorted(task_ids)):
        raise ValueError("tasks must be sorted by task_id")
    query_classes = {task.query_class for task in tasks}
    if query_classes != set(QUERY_CLASSES):
        raise ValueError("tasks must represent every frozen query_class")
    counts = {query_class: 0 for query_class in QUERY_CLASSES}
    for task in tasks:
        counts[task.query_class] += 1
    if any(count < 2 for count in counts.values()):
        raise ValueError("tasks must contain at least two examples per query_class")
    task_hashes = tuple(task.task_hash for task in tasks)
    if len(task_hashes) != len(set(task_hashes)):
        raise ValueError("tasks must have unique content hashes")


__all__ = [
    "C2TaskPack",
    "DEFAULT_TASK_PACK_PATH",
    "TASK_PACK_SCHEMA",
    "pack_from_mapping",
    "pack_to_mapping",
    "read_task_pack",
]
