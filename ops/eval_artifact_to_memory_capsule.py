#!/usr/bin/env python3
"""Turn Compass eval artifacts into lifecycle-tagged memory capsules."""
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


@dataclass(frozen=True)
class Capsule:
    filename: str
    markdown: str


def read_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected object JSON: {path}")
    return data


def capsule_filename(source_artifact: Path) -> str:
    raw = str(source_artifact).replace("\\", "/")
    h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"session_eval_capsule_{h}_route_a_benchmark.md"


def _frontmatter_list(values: list[str]) -> str:
    escaped = [v.replace('"', '\\"') for v in values]
    return "[" + ", ".join(f'"{v}"' for v in escaped) + "]"


def _slug_value(value: Any, default: str = "unknown") -> str:
    text = str(value if value is not None else default).strip()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^A-Za-z0-9_.-]+", "", text)
    return text[:80] or default


def _summary_value(summary: dict[str, Any], mode: str, key: str) -> Any:
    value = summary.get(mode, {})
    return value.get(key) if isinstance(value, dict) else None


def _first_actions(hint: dict[str, Any], recall: dict[str, Any]) -> list[dict[str, Any]]:
    actions = hint.get("next_actions")
    if isinstance(actions, list) and actions:
        return [x for x in actions if isinstance(x, dict)][:5]
    recs = recall.get("recommendations")
    if isinstance(recs, list):
        return [x for x in recs if isinstance(x, dict)][:5]
    return []


def _impact_seed(recall: dict[str, Any], hint: dict[str, Any]) -> float:
    meta = recall.get("meta", {})
    n_memories = meta.get("n_memories", 0) if isinstance(meta, dict) else 0
    risk = str(hint.get("risk") or "").lower()
    if n_memories and risk not in {"critical", "high"}:
        return 1.0
    if n_memories:
        return 0.5
    return 0.0


def build_capsule(
    recall: dict[str, Any],
    hint: dict[str, Any],
    *,
    source_artifact: Path,
    manifest: dict[str, Any] | None = None,
) -> Capsule:
    manifest = manifest or {}
    meta = recall.get("meta", {}) if isinstance(recall.get("meta"), dict) else {}
    summary = recall.get("result_summary", {}) if isinstance(recall.get("result_summary"), dict) else {}
    actions = _first_actions(hint, recall)

    generated_at = str(recall.get("generated_at") or manifest.get("run_at") or datetime.now(timezone.utc).isoformat(timespec="seconds"))
    flat_mrr = _summary_value(summary, "flat", "mrr")
    flat_p1 = _summary_value(summary, "flat", "p1")
    n_memories = meta.get("n_memories", 0)
    n_impact = meta.get("n_impact", 0)
    n_tier = meta.get("n_tier_nonworking", 0)
    risk = hint.get("risk", "unknown")
    suite = manifest.get("suite", "unknown")
    python_version = manifest.get("python_version", "unknown")
    embedder = meta.get("embedder") or manifest.get("embedder") or "unknown"
    impact = _impact_seed(recall, hint)

    tags = [
        "route-a",
        "benchmark",
        "dogfood",
        "eval-artifact",
        "write-side-seed",
        f"risk:{_slug_value(risk)}",
        f"suite:{_slug_value(suite)}",
    ]
    desc = (
        "Route A benchmark smoke baseline: "
        f"n={n_memories}, flat_mrr={flat_mrr}, risk={risk}; "
        "seed tier/impact signals for the next recall benchmark."
    )
    fm = [
        "---",
        "name: session_20260721_compass_route_a_benchmark_capsule",
        f"description: {desc}",
        "type: benchmark",
        "drift: green",
        "agent_type: compass-eval-loop",
        "ingested_via: eval_artifact_to_memory_capsule",
        "tier: semantic",
        "promote_after: 20_access",
        "reinforce_count: 0",
        f"cumulative_impact: {impact:.1f}",
        "impact_event_count: 1",
        f"last_impact_at: {generated_at}",
        f"tags: {_frontmatter_list(tags)}",
        "---",
        "",
    ]

    action_lines = []
    for item in actions:
        action = item.get("action", "unknown")
        priority = item.get("priority", "unknown")
        reason = item.get("reason", "")
        next_step = item.get("next_step", "")
        action_lines.append(f"- {priority}: {action} - {reason} Next: {next_step}".strip())
    if not action_lines:
        action_lines.append("- none: no tuning action found.")

    body = [
        "# Route A benchmark smoke baseline",
        "",
        "## Evidence",
        "",
        f"- source_artifact: {source_artifact}",
        f"- suite: {suite}",
        f"- python_version: {python_version}",
        f"- embedder: {embedder}",
        f"- n_memories: {n_memories}",
        f"- n_impact: {n_impact}",
        f"- n_tier_nonworking: {n_tier}",
        f"- flat P@1: {flat_p1}",
        f"- flat MRR: {flat_mrr}",
        f"- poi delta MRR: {_summary_value(summary, 'poi', 'delta_mrr_vs_flat')}",
        f"- tier delta MRR: {_summary_value(summary, 'tier', 'delta_mrr_vs_flat')}",
        f"- gemini delta MRR: {_summary_value(summary, 'gemini', 'delta_mrr_vs_flat')}",
        f"- tuning risk: {risk}",
        "",
        "## Interpretation",
        "",
        "The recall foundation is already strong, but the differentiating lifecycle layer has little signal to act on.",
        "This capsule intentionally seeds one non-working tier and one positive impact event so the next benchmark can observe write-side signal presence.",
        "",
        "## Next Actions",
        "",
        *action_lines,
        "",
    ]
    return Capsule(filename=capsule_filename(source_artifact), markdown="\n".join(fm + body))


def write_capsule(capsule: Capsule, memory_root: Path) -> Path:
    memory_root.mkdir(parents=True, exist_ok=True)
    path = memory_root / capsule.filename
    path.write_text(capsule.markdown, encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recall-artifact", required=True)
    ap.add_argument("--tuning-hint")
    ap.add_argument("--manifest")
    ap.add_argument("--memory-root")
    ap.add_argument("--write-default-memory", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    recall_path = Path(args.recall_artifact)
    recall = read_json(recall_path)
    hint = read_json(Path(args.tuning_hint)) if args.tuning_hint else {}
    manifest = read_json(Path(args.manifest)) if args.manifest else {}
    capsule = build_capsule(recall, hint, source_artifact=recall_path, manifest=manifest)

    if args.dry_run:
        print(capsule.markdown)
        return 0

    if args.memory_root:
        root = Path(args.memory_root)
    elif args.write_default_memory:
        root = DEFAULT_MEMORY_ROOT
    else:
        raise SystemExit("choose --memory-root, --write-default-memory, or --dry-run")

    path = write_capsule(capsule, root)
    print(json.dumps({"written": str(path), "filename": capsule.filename}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
