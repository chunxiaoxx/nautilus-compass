"""Append-only progress and atomic pair checkpoints for long C2 runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from benchmarks.poi_gate2.canonical import hash_json


CHECKPOINT_SCHEMA = "compass.live_agent_c2.pair_checkpoint.v1"
PROGRESS_SCHEMA = "compass.live_agent_c2.progress.v1"
TERMINAL_STATUSES = frozenset({"complete", "incomplete", "interrupted"})


class CheckpointStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.directory = self.root / "checkpoints"
        self.progress_path = self.root / "progress.jsonl"

    def initialize(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        if not self.progress_path.exists():
            self.progress_path.write_text("", encoding="utf-8")

    def terminal_pair_ids(self) -> frozenset[str]:
        return frozenset(path.stem for path in self.directory.glob("c2_pair_*.json"))

    def started_pair_ids(self) -> frozenset[str]:
        return frozenset(
            item["pair_id"]
            for item in self._progress_events()
            if item["status"] == "started"
        )

    def mark_started(self, pair_id: str) -> None:
        if pair_id in self.terminal_pair_ids() or pair_id in self.started_pair_ids():
            raise ValueError("pair already has durable progress")
        self._append_progress(pair_id, "started")

    def mark_interrupted(self, pair_id: str) -> None:
        self.write_checkpoint(
            pair_id=pair_id,
            status="interrupted",
            bundles=(),
            outcome=None,
            invalid_attempt_count=1,
            retry_count=0,
            failure_codes=("executor_interrupted",),
        )

    def write_checkpoint(
        self,
        *,
        pair_id: str,
        status: str,
        bundles: Sequence[Mapping[str, Any]],
        outcome: Mapping[str, Any] | None,
        invalid_attempt_count: int,
        retry_count: int,
        failure_codes: Sequence[str],
    ) -> None:
        if status not in TERMINAL_STATUSES:
            raise ValueError("checkpoint status is unsupported")
        values = {
            "schema_version": CHECKPOINT_SCHEMA,
            "pair_id": pair_id,
            "status": status,
            "bundles": list(bundles),
            "outcome": outcome,
            "invalid_attempt_count": invalid_attempt_count,
            "retry_count": retry_count,
            "failure_codes": list(failure_codes),
        }
        payload = {**values, "checkpoint_hash": hash_json(values)}
        destination = self.directory / f"{pair_id}.json"
        if destination.exists():
            if self._read_checkpoint(destination) != payload:
                raise ValueError("pair checkpoint conflicts with existing evidence")
            return
        temporary = destination.with_suffix(".json.tmp")
        _write_json(temporary, payload)
        temporary.replace(destination)
        self._append_progress(pair_id, status)

    def prepare_resume(self) -> None:
        orphaned = self.started_pair_ids() - self.terminal_pair_ids()
        for pair_id in sorted(orphaned):
            self.mark_interrupted(pair_id)

    def checkpoints(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            self._read_checkpoint(path)
            for path in sorted(self.directory.glob("c2_pair_*.json"))
        )

    def _append_progress(self, pair_id: str, status: str) -> None:
        values = {
            "schema_version": PROGRESS_SCHEMA,
            "pair_id": pair_id,
            "status": status,
        }
        event = {**values, "progress_hash": hash_json(values)}
        with self.progress_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event, separators=(",", ":"), sort_keys=True) + "\n")

    def _progress_events(self) -> tuple[dict[str, Any], ...]:
        events = []
        for line in self.progress_path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            supplied_hash = item.pop("progress_hash")
            if item.get("schema_version") != PROGRESS_SCHEMA:
                raise ValueError("progress schema mismatch")
            if hash_json(item) != supplied_hash:
                raise ValueError("progress hash mismatch")
            events.append({**item, "progress_hash": supplied_hash})
        return tuple(events)

    @staticmethod
    def _read_checkpoint(path: Path) -> dict[str, Any]:
        item = json.loads(path.read_text(encoding="utf-8"))
        supplied_hash = item.pop("checkpoint_hash")
        if item.get("schema_version") != CHECKPOINT_SCHEMA:
            raise ValueError("checkpoint schema mismatch")
        if item.get("status") not in TERMINAL_STATUSES:
            raise ValueError("checkpoint status mismatch")
        if hash_json(item) != supplied_hash:
            raise ValueError("checkpoint hash mismatch")
        return {**item, "checkpoint_hash": supplied_hash}


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


__all__ = ["CHECKPOINT_SCHEMA", "PROGRESS_SCHEMA", "CheckpointStore"]
