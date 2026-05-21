"""v1.7.1 · S6 module 2 · viking:// URI scheme · tier-agnostic addressing.

OV paradigm clean-room rewrite (NO fork of AGPL-3.0 source).

URI format:
  viking://<project>/<resource>[?tier=L0|L1|L2]
  viking://<project>/<resource>.l1   (suffix form · convenient)
  viking://<project>/<resource>.l2

Resolves to actual filesystem path under
  ~/.claude/projects/<project>/memory/{session_*.md, _l1/*.md, _l2/*.md}

NO LLM. Pure URL parsing + filesystem mapping.
Reference: paper/SPEC_LAYER2_L1_REWRITE.md section 2 (paradigm borrow only).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs

SCHEME = "viking"
TIER_L0 = "L0"
TIER_L1 = "L1"
TIER_L2 = "L2"
VALID_TIERS = (TIER_L0, TIER_L1, TIER_L2)


def parse_uri(uri: str) -> dict:
    """Parse viking:// URI · returns dict or raises ValueError.

    Returns:
      {"scheme": "viking", "project": str, "resource": str, "tier": str}
    """
    if not isinstance(uri, str) or not uri.startswith(f"{SCHEME}://"):
        raise ValueError(f"not a viking:// URI: {uri!r}")
    p = urlparse(uri)
    if p.scheme != SCHEME:
        raise ValueError(f"unexpected scheme: {p.scheme}")
    project = p.netloc
    if not project:
        raise ValueError(f"missing project (netloc) in {uri!r}")
    raw_path = p.path.lstrip("/")
    if not raw_path:
        raise ValueError(f"missing resource (path) in {uri!r}")

    # Tier from query param has priority
    tier = TIER_L0
    qs = parse_qs(p.query) if p.query else {}
    if "tier" in qs and qs["tier"]:
        tier_q = qs["tier"][0].upper()
        if tier_q in VALID_TIERS:
            tier = tier_q

    # Suffix-form override (.l1 / .l2)
    resource = raw_path
    lower = raw_path.lower()
    if lower.endswith(".l1"):
        tier = TIER_L1
        resource = raw_path[:-3]
    elif lower.endswith(".l2"):
        tier = TIER_L2
        resource = raw_path[:-3]

    return {"scheme": SCHEME, "project": project, "resource": resource, "tier": tier}


def make_uri(project: str, resource: str, tier: str = TIER_L0) -> str:
    """Construct a viking:// URI from components."""
    if tier not in VALID_TIERS:
        raise ValueError(f"invalid tier: {tier!r} (must be one of {VALID_TIERS})")
    base = f"{SCHEME}://{project}/{resource}"
    if tier == TIER_L0:
        return base
    return f"{base}.{tier.lower()}"


def resolve_to_path(uri: str, projects_root: Optional[Path] = None) -> Path:
    """Resolve viking:// URI to filesystem Path.

    Args:
        uri: viking:// URI string
        projects_root: defaults to ~/.claude/projects/

    Returns:
        Path · may NOT exist (caller checks)
    """
    info = parse_uri(uri)
    if projects_root is None:
        projects_root = Path.home() / ".claude" / "projects"
    if not isinstance(projects_root, Path):
        projects_root = Path(projects_root)

    project_dir = projects_root / info["project"]
    memory_dir = project_dir / "memory"
    resource = info["resource"]

    if info["tier"] == TIER_L0:
        return memory_dir / resource
    if info["tier"] == TIER_L1:
        return memory_dir / "_l1" / resource
    if info["tier"] == TIER_L2:
        return memory_dir / "_l2" / resource
    return memory_dir / resource  # fallback (shouldn't reach)


def path_to_uri(path: Path, projects_root: Optional[Path] = None) -> str:
    """Reverse · construct viking:// URI from filesystem Path.

    Returns empty string if path not under projects_root memory hierarchy.
    """
    if not isinstance(path, Path):
        path = Path(path)
    if projects_root is None:
        projects_root = Path.home() / ".claude" / "projects"
    if not isinstance(projects_root, Path):
        projects_root = Path(projects_root)

    try:
        rel = path.relative_to(projects_root)
    except ValueError:
        return ""

    parts = rel.parts
    if len(parts) < 3 or parts[1] != "memory":
        return ""

    project = parts[0]
    rest = parts[2:]

    if rest[0] == "_l1" and len(rest) >= 2:
        return make_uri(project, rest[-1], tier=TIER_L1)
    if rest[0] == "_l2" and len(rest) >= 2:
        return make_uri(project, rest[-1], tier=TIER_L2)
    return make_uri(project, rest[-1], tier=TIER_L0)
