"""Plugin manifest + slash-command surface · Task #62.

Locks in:
- .claude-plugin/plugin.json schema and version sync
- commands/ slash-command files exist and are well-formed
- compass_verify.py survives piped stdout on Windows GBK consoles
  (regression for the 2026-05-07 UnicodeEncodeError on ✓ glyphs)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
COMMANDS_DIR = ROOT / "commands"

EXPECTED_COMMANDS = {
    "compass-verify",
    "compass-drift",
    "compass-recall",
    "compass-search",
    "compass-status",
}

EXPECTED_SKILLS = {
    "compass-integrity",
}


def _read_pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    assert m, "pyproject.toml has no top-level version"
    return m.group(1)


def test_plugin_manifest_exists_and_parses():
    assert PLUGIN_MANIFEST.is_file(), f"missing {PLUGIN_MANIFEST}"
    data = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    for key in ("name", "version", "description", "license"):
        assert key in data, f"plugin.json missing required key {key!r}"
    assert data["name"] == "nautilus-compass"


def test_plugin_manifest_version_matches_pyproject():
    data = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    assert data["version"] == _read_pyproject_version(), (
        "plugin.json version drift vs pyproject.toml — "
        "update both when bumping"
    )


def test_all_expected_commands_present():
    assert COMMANDS_DIR.is_dir(), f"missing {COMMANDS_DIR}"
    found = {p.stem for p in COMMANDS_DIR.glob("*.md")}
    missing = EXPECTED_COMMANDS - found
    assert not missing, f"commands/ missing: {sorted(missing)}"


def test_each_command_has_h1_and_description():
    for name in EXPECTED_COMMANDS:
        path = COMMANDS_DIR / f"{name}.md"
        text = path.read_text(encoding="utf-8")
        first_line = text.splitlines()[0] if text else ""
        assert first_line.startswith("# "), (
            f"{path.name} must start with H1 (got {first_line!r})"
        )
        # Body should mention the underlying script so users can debug.
        assert ".py" in text, f"{path.name} should reference its backing script"


def test_all_expected_skills_present_with_frontmatter():
    skills_dir = ROOT / "skills"
    assert skills_dir.is_dir(), f"missing {skills_dir}"
    for name in EXPECTED_SKILLS:
        skill_md = skills_dir / name / "SKILL.md"
        assert skill_md.is_file(), f"missing {skill_md}"
        text = skill_md.read_text(encoding="utf-8")
        # YAML frontmatter must lead, with name + description + closing fence
        assert text.startswith("---\n"), (
            f"{skill_md.name} must lead with --- frontmatter"
        )
        head, _, _ = text[4:].partition("\n---\n")
        assert f"name: {name}" in head, (
            f"{skill_md.name} frontmatter missing 'name: {name}'"
        )
        assert "description:" in head, (
            f"{skill_md.name} frontmatter missing description"
        )


def test_compass_verify_handles_piped_stdout():
    """Regression: ✓ glyph crashed on Windows GBK when stdout was piped.

    Forcing PYTHONIOENCODING off + capturing output (which makes stdout
    a pipe, not a tty) used to raise UnicodeEncodeError. The reconfigure
    in compass_verify.py should keep it green now.
    """
    result = subprocess.run(
        [sys.executable, str(ROOT / "compass_verify.py"), "--all"],
        capture_output=True,
        text=False,  # bytes — we don't care about decoding here
        timeout=30,
    )
    # Exit code is 0 (all OK) or 1 (some chain skipped/missing) but never
    # 2 (arg conflict) and never a crash code.
    assert result.returncode in (0, 1), (
        f"compass_verify --all returncode={result.returncode}\n"
        f"stderr: {result.stderr.decode('utf-8', 'replace')[:500]}"
    )
    # If it crashed on encoding, the trace would land in stderr.
    err = result.stderr.decode("utf-8", "replace")
    assert "UnicodeEncodeError" not in err, err
