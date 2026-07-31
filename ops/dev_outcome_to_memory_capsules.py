#!/usr/bin/env python3
"""Convert verified development outcomes into Compass memory capsules."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_MEMORY_ROOT = Path.home() / ".claude" / "projects" / "C--Users-chunx" / "memory"
MIN_SIGNAL_COUNT = 3


@dataclass(frozen=True)
class Capsule:
    filename: str
    markdown: str


def _slug(value: Any, default: str = "unknown") -> str:
    text = str(value if value is not None else default).strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9_.-]+", "", text)
    return text[:80] or default


def _frontmatter_list(values: list[str]) -> str:
    escaped = [str(v).replace('"', '\\"') for v in values]
    return "[" + ", ".join(f'"{v}"' for v in escaped) + "]"


def _filename(outcome: dict[str, Any]) -> str:
    seed = f"{outcome.get('id', '')}:{outcome.get('commit', '')}:{outcome.get('title', '')}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
    return f"session_dev_outcome_{_slug(outcome.get('id'))}_{digest}.md"


def _impact(outcome: dict[str, Any]) -> float:
    try:
        return float(outcome.get("impact", 1.0))
    except (TypeError, ValueError):
        return 1.0


def _evidence_lines(values: Any) -> list[str]:
    if not isinstance(values, list):
        return ["- no evidence listed"]
    lines = []
    for item in values:
        lines.append(f"- {item}")
    return lines or ["- no evidence listed"]


def build_capsules(
    outcomes: list[dict[str, Any]],
    *,
    generated_at: str | None = None,
) -> list[Capsule]:
    ts = generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    capsules: list[Capsule] = []
    for outcome in outcomes:
        outcome_id = _slug(outcome.get("id"))
        title = str(outcome.get("title") or outcome_id)
        commit = str(outcome.get("commit") or "unknown")
        kind = _slug(outcome.get("kind"), "execution")
        tier = str(outcome.get("tier") or "semantic")
        impact = _impact(outcome)
        result = str(outcome.get("result") or "")
        tags = ["dogfood", "execution-outcome", "compass-c5", f"kind:{kind}", f"commit:{commit}"]
        desc = f"Compass C5 outcome {outcome_id}: {title}; commit={commit}; result={result}"

        fm = [
            "---",
            f"name: session_20260721_compass_dev_outcome_{outcome_id}",
            f"description: {desc}",
            "type: execution_outcome",
            "drift: green",
            "agent_type: compass-dogfood-loop",
            "ingested_via: dev_outcome_to_memory_capsules",
            f"tier: {tier}",
            "promote_after: 20_access",
            "reinforce_count: 0",
            f"cumulative_impact: {impact:.1f}",
            "impact_event_count: 1",
            f"last_impact_at: {ts}",
            f"commit: {commit}",
            f"outcome_kind: {kind}",
            f"tags: {_frontmatter_list(tags)}",
            "---",
            "",
        ]
        body = [
            f"# {title}",
            "",
            "## Result",
            "",
            result,
            "",
            "## Evidence",
            "",
            *_evidence_lines(outcome.get("evidence")),
            "",
            "## Why this matters to Compass",
            "",
            "This is a verified development outcome that feeds the memory flywheel: execution result -> capsule -> recall benchmark -> policy gate.",
            "",
        ]
        capsules.append(Capsule(filename=_filename(outcome), markdown="\n".join(fm + body)))
    return capsules


def signal_support_from_capsules(capsules: list[Capsule]) -> dict[str, Any]:
    n_impact = sum(1 for c in capsules if re.search(r"^cumulative_impact:\s*(?!0(?:\.0)?$)", c.markdown, re.MULTILINE))
    n_tier = sum(1 for c in capsules if re.search(r"^tier:\s*(?!working$)\w+", c.markdown, re.MULTILINE))
    return {
        "n_capsules": len(capsules),
        "n_impact": n_impact,
        "n_tier_nonworking": n_tier,
        "meets_min_signal_count": n_impact >= MIN_SIGNAL_COUNT and n_tier >= MIN_SIGNAL_COUNT,
    }


def write_capsules(capsules: list[Capsule], memory_root: Path) -> list[Path]:
    memory_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for capsule in capsules:
        path = memory_root / capsule.filename
        path.write_text(capsule.markdown, encoding="utf-8")
        written.append(path)
    manifest = {
        "written": [str(p) for p in written],
        "support": signal_support_from_capsules(capsules),
    }
    (memory_root / "_dev_outcome_capsules_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return written


def read_outcomes(path: Path) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
        raise ValueError("outcomes JSON must be a list of objects")
    return data


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outcomes", required=True, help="JSON list of verified development outcomes")
    ap.add_argument("--memory-root")
    ap.add_argument("--write-default-memory", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    capsules = build_capsules(read_outcomes(Path(args.outcomes)))
    if args.dry_run:
        print(json.dumps(signal_support_from_capsules(capsules), ensure_ascii=False, indent=2))
        return 0
    if args.memory_root:
        root = Path(args.memory_root)
    elif args.write_default_memory:
        root = DEFAULT_MEMORY_ROOT
    else:
        raise SystemExit("choose --memory-root, --write-default-memory, or --dry-run")
    written = write_capsules(capsules, root)
    print(json.dumps({"written": [str(p) for p in written], "support": signal_support_from_capsules(capsules)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
