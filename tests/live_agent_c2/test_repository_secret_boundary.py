from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SENSITIVE_EXPORT = re.compile(
    r"^\s*export\s+(?P<name>[A-Z0-9_]*(?:API_KEY|TOKEN|SECRET))=(?P<value>.*)$",
    re.MULTILINE,
)


def test_legacy_behavior_runner_does_not_embed_provider_credentials() -> None:
    script = (REPO_ROOT / "tests" / "run_behavior_ab_all.sh").read_text(encoding="utf-8")

    literal_exports = []
    for match in SENSITIVE_EXPORT.finditer(script):
        value = match.group("value").strip().strip('"').strip("'")
        if value and not value.startswith(("$", "<")):
            literal_exports.append(match.group("name"))

    assert literal_exports == []
    assert "${ARK_API_KEY:?" in script
