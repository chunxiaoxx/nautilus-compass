"""v1.7.1 · S6 module 1 · L2 dream-layer distillation (nightly batch).

Reads L1 overview files and produces L2 distilled summaries that compress
across multiple L1 groups for the same project.

OPTIONALLY uses local Ollama LLM (e.g. Qwen 2.5 7B · $0 marginal cost ·
runs offline nightly · NOT on ingest path). If Ollama unavailable, falls
back to deterministic extractive summary (concat + dedup + truncate).

Critical constraint (per anchor): L2 distillation is OFFLINE nightly only ·
NEVER on ingest path · preserves "no LLM at ingest" core diff.

Reference: paper/SPEC_LAYER2_L1_REWRITE.md section 2 (L2 mentioned · this
spec extends into Ollama-optional implementation per COMPASS_V2_SPEC_DRAFT
Layer 2 row 3).
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from .l1_grouper import parse_session_frontmatter  # noqa: F401
except (ImportError, ValueError):
    pass  # type: ignore

OLLAMA_URL = os.environ.get("COMPASS_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("COMPASS_OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_TIMEOUT_S = float(os.environ.get("COMPASS_OLLAMA_TIMEOUT_S", "60"))

L2_DIR_NAME = "_l2"
MAX_L1_INPUT_CHARS = 8000  # cap input to Ollama for predictable latency


def ollama_available(url: str = OLLAMA_URL, timeout: float = 3.0) -> bool:
    """Check if Ollama HTTP API responds. Returns False on any failure."""
    try:
        req = urllib.request.Request(f"{url.rstrip('/')}/api/tags")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError):
        return False


def ollama_generate(prompt: str, model: str = OLLAMA_MODEL,
                    url: str = OLLAMA_URL,
                    timeout: float = OLLAMA_TIMEOUT_S) -> Optional[str]:
    """Call Ollama /api/generate · returns response text or None on failure."""
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 800},
    }
    try:
        req = urllib.request.Request(
            f"{url.rstrip('/')}/api/generate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError,
            json.JSONDecodeError, TimeoutError):
        return None


def extractive_fallback(l1_contents: list, max_chars: int = 1200) -> str:
    """Deterministic fallback when Ollama unavailable · concat + dedup + cap."""
    seen_lines: set = set()
    out_lines: list = []
    for content in l1_contents:
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("---") or line.startswith("#"):
                continue
            if line.startswith("- "):
                key = line[2:]
                if key not in seen_lines:
                    seen_lines.add(key)
                    out_lines.append(line)
    summary = "\n".join(out_lines)
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "\n... [truncated]"
    return summary


def distill_l1_files(l1_paths: list, use_ollama: bool = True) -> str:
    """Produce one L2 distilled markdown body from multiple L1 file contents.

    If use_ollama and ollama_available · calls Ollama for synthesis.
    Otherwise · extractive fallback (deterministic).
    """
    l1_contents = []
    for p in l1_paths:
        path = Path(p) if not isinstance(p, Path) else p
        try:
            l1_contents.append(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    if not l1_contents:
        return "(no L1 input)"

    concat = "\n\n---\n\n".join(l1_contents)[:MAX_L1_INPUT_CHARS]

    if use_ollama and ollama_available():
        prompt = (
            "Distill the following L1 overviews into a concise (~400 word) "
            "L2 summary capturing recurring themes, key decisions, and open "
            "questions. Use markdown bullets. Do not invent facts.\n\n"
            f"{concat}"
        )
        result = ollama_generate(prompt)
        if result:
            return result

    return extractive_fallback(l1_contents)


def render_l2_overview(project_id: str, l1_paths: list,
                       distilled_body: str) -> str:
    """Render full L2 markdown content with frontmatter."""
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [
        "---",
        f"name: l2-{project_id}",
        f"description: L2 dream-layer distillation for project '{project_id}'",
        "type: discovery",
        "concept: pattern",
        "drift: green",
        "tier: semantic",
        "decay_rate: 0.1",
        "promote_after: \"30_access\"",
        "reinforce_count: 0",
        "agent_type: compass-l2-distiller",
        f"l2_project: {project_id}",
        f"l2_l1_count: {len(l1_paths)}",
        f"l2_generated_at: {ts}",
        "l2_l1_sources:",
    ]
    for p in l1_paths:
        lines.append(f"  - {Path(p).name}")
    lines.append("---")
    lines.append("")
    lines.append(f"# L2 Distillation · {project_id}")
    lines.append("")
    lines.append(f"_Synthesized from {len(l1_paths)} L1 overview files_")
    lines.append("")
    lines.append(distilled_body)
    lines.append("")
    return "\n".join(lines) + "\n"


def build_l2(project_root: Path, project_id: Optional[str] = None,
             use_ollama: bool = True) -> dict:
    """Build L2 file from all L1 files in project_root/_l1/.

    Returns:
        {"l2_path": str, "l1_count": int, "ollama_used": bool}
    """
    if not isinstance(project_root, Path):
        project_root = Path(project_root)
    l1_dir = project_root / "_l1"
    if not l1_dir.exists():
        return {"l2_path": "", "l1_count": 0, "ollama_used": False,
                "skipped": "no _l1/ directory"}

    l1_files = [f for f in l1_dir.glob("*.md") if not f.name.startswith("_")]
    if not l1_files:
        return {"l2_path": "", "l1_count": 0, "ollama_used": False,
                "skipped": "no L1 files"}

    pid = project_id or project_root.name
    used_ollama = use_ollama and ollama_available()
    distilled = distill_l1_files(l1_files, use_ollama=use_ollama)
    content = render_l2_overview(pid, l1_files, distilled)

    l2_dir = project_root / L2_DIR_NAME
    l2_dir.mkdir(parents=True, exist_ok=True)
    l2_path = l2_dir / f"{pid}.md"
    l2_path.write_text(content, encoding="utf-8")

    return {"l2_path": str(l2_path), "l1_count": len(l1_files),
            "ollama_used": used_ollama}
