"""Phase 2.I.2 (2026-05-30) · tier promotion driver · daily cron.

Reads all session_*.md frontmatter across project memory dirs · computes
new tier via proof.tier_promotion.calculate_new_tier from the
cumulative_impact field · mutates `tier:` field in-place if changed ·
appends one log record per mutation to a jsonl sidecar.

Idempotent: subsequent runs with the same cumulative_impact + correct tier
take no action (no log entry, no file rewrite).

CLI entry: `py -3 scripts/tier_promotion_driver.py`. Cron once daily.

Frontmatter parse-mutate-write mirrors the pattern in
`proof/poi_emitter.py:update_frontmatter_cumulative` (cumulative_impact /
impact_event_count / last_impact_at) · this module adds the same pattern
for the `tier:` field. Future refactor could extract a shared
frontmatter helper.

Finding G (2026-05-30) align: canonical tier set is
working/episodic/semantic/procedural (from agentmemory naming · see
proof/tier_promotion.TIERS). Invalid tier values in frontmatter
(e.g. "L2" from plan-doc misnomer) fall back to DEFAULT_TIER ("episodic")
rather than raise.

Reference: docs/plans/.../implementation-plan.md §I.2
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Make repo root importable when invoked as a script
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from proof.tier_promotion import calculate_new_tier, TIERS  # noqa: E402

DEFAULT_TIER: str = "episodic"
DEFAULT_LOG: Path = (
    Path.home()
    / ".claude"
    / "plugins"
    / "nautilus-compass"
    / ".cache"
    / "tier_promotion_log.jsonl"
)

# Field stamping the cumulative_impact value at the last tier change · used
# to compute a per-run delta so re-runs with unchanged cumulative_impact
# don't cascade tiers (e.g. episodic→semantic on day 1 wouldn't trip again
# to procedural on day 2 with the same 1.5 cumulative · only when impact
# grows past last_changed_at + PROMOTE_THRESHOLD).
_LAST_AT_FIELD: str = "tier_last_changed_at_impact"


def _find_session_memory_dirs() -> list[Path]:
    """Find ~/.claude/projects/<encoded>/memory/ dirs across all projects."""
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return []
    return [
        proj / "memory"
        for proj in projects_dir.iterdir()
        if (proj / "memory").exists()
    ]


def _parse_frontmatter_fields(text: str) -> Optional[dict[str, str]]:
    """Extract simple key:value pairs from YAML-ish frontmatter.

    Returns None if no frontmatter delimiters present. Doesn't handle nested
    mappings or list values (we only need flat scalars for tier_promotion).
    """
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    front_block = text[4:end]
    fields: dict[str, str] = {}
    for line in front_block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            continue  # list item · skip
        if ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        fields[key.strip()] = val.strip()
    return fields


def _safe_float(raw: str) -> float:
    """Coerce frontmatter scalar to float · 0.0 on missing / unparseable."""
    raw = (raw or "").strip()
    try:
        return float(raw) if raw else 0.0
    except (TypeError, ValueError):
        return 0.0


def _read_tier_state(fields: dict[str, str]) -> tuple[str, float, float]:
    """Pull tier (with fallback), cumulative_impact, and last_changed_at_impact.

    Returns (tier, cumulative_impact, delta) where delta = cumulative_impact -
    last_changed_at_impact. Driver feeds delta to calculate_new_tier · so a
    second run with unchanged cumulative_impact sees delta=0 → no tier change.
    """
    tier = fields.get("tier", "").strip() or DEFAULT_TIER
    if tier not in TIERS:
        tier = DEFAULT_TIER  # Finding G · invalid frontmatter tier falls back
    cur_impact = _safe_float(fields.get("cumulative_impact", ""))
    last_at = _safe_float(fields.get(_LAST_AT_FIELD, ""))
    delta = cur_impact - last_at
    return tier, cur_impact, delta


def _rewrite_tier_in_frontmatter(
    text: str, new_tier: str, last_changed_at_impact: float
) -> Optional[str]:
    """Return new text with `tier:` set to new_tier AND `tier_last_changed_at_impact:`
    stamped with the cumulative_impact value at change time. Both fields added
    if missing.

    Returns None if text has no frontmatter delimiters (caller treats as skip).
    """
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    front_block = text[4:end]
    body = text[end:]
    lines = front_block.splitlines()
    new_lines: list[str] = []
    seen_tier = False
    seen_last_at = False
    stamp = round(last_changed_at_impact, 4)
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("tier:"):
            new_lines.append(f"tier: {new_tier}")
            seen_tier = True
        elif stripped.startswith(f"{_LAST_AT_FIELD}:"):
            new_lines.append(f"{_LAST_AT_FIELD}: {stamp}")
            seen_last_at = True
        else:
            new_lines.append(line)
    if not seen_tier:
        new_lines.append(f"tier: {new_tier}")
    if not seen_last_at:
        new_lines.append(f"{_LAST_AT_FIELD}: {stamp}")
    return "---\n" + "\n".join(new_lines) + body


def process_session_file(path: Path) -> Optional[dict]:
    """Read · compute new tier · rewrite if changed · return mutation record.

    Returns None on: file unreadable · no frontmatter · tier unchanged ·
    write failure. Returns dict with file/old_tier/new_tier/cumulative_impact
    on successful mutation.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    fields = _parse_frontmatter_fields(text)
    if fields is None:
        return None
    cur_tier, cur_impact, delta = _read_tier_state(fields)
    new_tier = calculate_new_tier(cur_tier, delta)
    if new_tier == cur_tier:
        return None
    rewritten = _rewrite_tier_in_frontmatter(text, new_tier, cur_impact)
    if rewritten is None:
        return None
    try:
        path.write_text(rewritten, encoding="utf-8")
    except OSError:
        return None
    return {
        "file": str(path),
        "old_tier": cur_tier,
        "new_tier": new_tier,
        "cumulative_impact": cur_impact,
        "delta": round(delta, 4),
    }


def _append_log(records: list[dict], log_path: Path) -> None:
    """Append mutation records to log_path (jsonl · one per line · stamped ts)."""
    if not records:
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(log_path, "a", encoding="utf-8") as f:
        for r in records:
            payload = {"ts": ts, **r}
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def run_driver(
    memory_dirs: Optional[list[Path]] = None,
    log_path: Optional[Path] = None,
) -> dict:
    """Run promotion driver across memory_dirs · return summary stats.

    Args:
        memory_dirs: list of dirs to scan for session_*.md · defaults to
                     ~/.claude/projects/*/memory/ when None.
        log_path:    where to append mutation records · defaults to
                     ~/.claude/plugins/nautilus-compass/.cache/tier_promotion_log.jsonl

    Returns:
        {"files_scanned": int, "mutations": int, "promoted": int, "demoted": int}
    """
    dirs = memory_dirs if memory_dirs is not None else _find_session_memory_dirs()
    log = log_path if log_path is not None else DEFAULT_LOG
    files_scanned = 0
    mutations: list[dict] = []
    for d in dirs:
        if not d.exists():
            continue
        for f in d.glob("session_*.md"):
            files_scanned += 1
            rec = process_session_file(f)
            if rec is not None:
                mutations.append(rec)
    _append_log(mutations, log)
    promoted = sum(
        1
        for m in mutations
        if TIERS.index(m["new_tier"]) > TIERS.index(m["old_tier"])
    )
    demoted = sum(
        1
        for m in mutations
        if TIERS.index(m["new_tier"]) < TIERS.index(m["old_tier"])
    )
    return {
        "files_scanned": files_scanned,
        "mutations": len(mutations),
        "promoted": promoted,
        "demoted": demoted,
    }


def main() -> int:
    summary = run_driver()
    print(
        f"[tier_promotion_driver] scanned={summary['files_scanned']} "
        f"mutations={summary['mutations']} "
        f"promoted={summary['promoted']} demoted={summary['demoted']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
