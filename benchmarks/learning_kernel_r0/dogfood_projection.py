"""Read-only fail-closed projection of pre-verdict Compass dogfood."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from benchmarks.poi_gate2.canonical import canonical_json_bytes, hash_json
from benchmarks.poi_gate2.dogfood_evidence import artifact_from_mapping


ROOT = Path(__file__).parents[2]
DEFAULT_SOURCE = ROOT / "docs" / "evidence" / "s4_live_agent_dogfood_candidates_v1.json"


def build_projection(source: Path = DEFAULT_SOURCE) -> dict[str, Any]:
    raw = json.loads(Path(source).read_text(encoding="utf-8"))
    artifact = artifact_from_mapping(raw)
    candidates = tuple(
        {
            "episode_id": candidate.packet.episode_id,
            "record_hash": candidate.record_hash,
            "verification_state": candidate.verification_state,
            "reason_code": "blocked_missing_independent_verdict",
        }
        for candidate in artifact.bundle.candidates
    )
    if any(
        candidate.candidate_state != "blocked_missing_independent_verdict"
        for candidate in artifact.bundle.candidates
    ):
        raise ValueError("source dogfood contains a candidate with unexpected authority")
    preimage = {
        "schema_version": "compass.learning_kernel.dogfood_preflight.v1",
        "source_artifact_hash": artifact.artifact_hash,
        "source_bundle_hash": artifact.bundle.bundle_hash,
        "candidate_count": len(candidates),
        "candidates": list(candidates),
        "stage_a_admitted_count": 0,
        "stage_a_state": "blocked_missing_independent_verdict",
        "synthesized_authority": {
            "reward": False,
            "impact": False,
            "capsule": False,
            "selector": False,
            "utility": False,
        },
        "development_recommendation": "flat",
        "runtime_recommendation": "flat",
        "improvement_claim": False,
    }
    return {**preimage, "projection_hash": hash_json(preimage)}


def write_projection(source: Path, output: Path) -> Path:
    output = Path(output)
    content = canonical_json_bytes(build_projection(source)) + b"\n"
    if output.exists():
        if output.read_bytes() != content:
            raise ValueError("projection output already contains conflicting evidence")
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(content)
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--write", required=True)
    args = parser.parse_args(argv)
    path = write_projection(Path(args.source), Path(args.write))
    print(canonical_json_bytes({"written": str(path), "status": "blocked"}).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_projection", "main", "write_projection"]
