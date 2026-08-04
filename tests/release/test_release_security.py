from __future__ import annotations

import ast
import warnings
import zipfile
from pathlib import Path

import pytest

from release_security import (
    ReleaseSecurityError,
    release_surface_paths,
    scan_release_surfaces,
    scan_source_file,
    scan_wheel,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DSN_FILES = (
    REPO_ROOT / "ops" / "arxiv_discovery_cron.py",
    REPO_ROOT / "ops" / "engagement_followup_cron.py",
    REPO_ROOT / "ops" / "gmail_inbound_monitor_cron.py",
    REPO_ROOT / "scripts" / "ingest_anchors.py",
    REPO_ROOT / "scripts" / "v7_monitor_cron.py",
)


def finding_codes(path):
    return {finding.rule_code for finding in scan_source_file(path)}


@pytest.mark.parametrize(
    ("filename", "body", "expected"),
    [
        (
            "database.py",
            'DSN = "postgresql://user:synthetic-password@localhost/db"\n',
            "credential_db_url",
        ),
        (
            "private.py",
            'KEY = "-----BEGIN PRIVATE KEY-----"\n',
            "private_key_marker",
        ),
        (
            "assignment.py",
            'API_TOKEN = "synthetic-token-value"\n',
            "plaintext_sensitive_assignment",
        ),
        (
            "call.py",
            'client(api_key="synthetic-key-value")\n',
            "plaintext_sensitive_call_argument",
        ),
        (
            "attribute.py",
            'settings.API_TOKEN = "synthetic-token-value"\n',
            "plaintext_sensitive_assignment",
        ),
        (
            "subscript.py",
            'settings["api_key"] = "synthetic-key-value"\n',
            "plaintext_sensitive_assignment",
        ),
        (
            "mapping.py",
            'CONFIG = {"api_key": "synthetic-key-value"}\n',
            "plaintext_sensitive_mapping_value",
        ),
        (
            ".env.example",
            "COMPASS_API_TOKEN=synthetic-token-value\n",
            "plaintext_env_assignment",
        ),
        (
            "compass.service",
            "Environment=COMPASS_API_TOKEN=synthetic-token-value\n",
            "plaintext_service_environment",
        ),
    ],
)
def test_scanner_detects_synthetic_release_secrets(tmp_path, filename, body, expected):
    path = tmp_path / filename
    path.write_text(body, encoding="utf-8")

    findings = scan_source_file(path)

    assert expected in {finding.rule_code for finding in findings}
    rendered = repr(findings)
    assert "synthetic-password" not in rendered
    assert "synthetic-token-value" not in rendered
    assert "synthetic-key-value" not in rendered


def test_scanner_allows_environment_backed_values(tmp_path):
    path = tmp_path / "clean.py"
    path.write_text(
        'import os\nDSN = os.environ.get("COMPASS_PG_DSN", "").strip()\n',
        encoding="utf-8",
    )

    assert scan_source_file(path) == ()


def test_scanner_does_not_leak_parser_warnings_from_documentation(tmp_path):
    path = tmp_path / "documentation.py"
    path.write_text('"""Example path: C:\\path\\to\\file."""\n', encoding="utf-8")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        scan_source_file(path)

    assert not [
        item
        for item in caught
        if item.category in (SyntaxWarning, DeprecationWarning)
    ]


def test_release_surface_allowlist_excludes_non_runtime_trees(tmp_path):
    for relative in (
        "runtime.py",
        "ops/worker.py",
        "scripts/tool.py",
        "middleware/auth.py",
        "tests/test_secret.py",
        "examples/example.py",
        "docs/sample.py",
        "scripts/_archive/old.py",
        ".git/hooks/pre-commit.py",
        ".codex/archived_sessions/old.py",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("VALUE = 1\n", encoding="utf-8")

    selected = {path.relative_to(tmp_path).as_posix() for path in release_surface_paths(tmp_path)}

    assert "runtime.py" in selected
    assert "ops/worker.py" in selected
    assert "scripts/tool.py" in selected
    assert "middleware/auth.py" in selected
    assert not selected.intersection(
        {
            "tests/test_secret.py",
            "examples/example.py",
            "docs/sample.py",
            "scripts/_archive/old.py",
            ".git/hooks/pre-commit.py",
            ".codex/archived_sessions/old.py",
        }
    )


def test_wheel_scanner_rejects_secret_and_path_traversal(tmp_path):
    wheel = tmp_path / "artifact.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("package/clean.py", "VALUE = 1\n")
        archive.writestr(
            "package/bad.py",
            'TOKEN = "synthetic-token-value"\n',
        )
        archive.writestr("../escape.py", "VALUE = 1\n")

    findings = scan_wheel(wheel)

    assert {finding.rule_code for finding in findings} == {
        "plaintext_sensitive_assignment",
        "wheel_path_traversal",
    }
    assert "synthetic-token-value" not in repr(findings)


def test_wheel_scanner_bounds_member_count(tmp_path):
    wheel = tmp_path / "too-many.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("a.py", "VALUE = 1\n")
        archive.writestr("b.py", "VALUE = 2\n")

    with pytest.raises(ReleaseSecurityError, match="wheel_member_limit"):
        scan_wheel(wheel, max_members=1)


def test_tracked_release_surfaces_are_secret_clean():
    assert scan_release_surfaces(REPO_ROOT) == ()


def _dsn_environment_default(tree, variable_name):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "get" or len(node.args) < 1:
            continue
        if not isinstance(node.func.value, ast.Attribute):
            continue
        if node.func.value.attr != "environ":
            continue
        if isinstance(node.args[0], ast.Constant) and node.args[0].value == variable_name:
            return node.args[1] if len(node.args) > 1 else None
    raise AssertionError("missing environment lookup for {}".format(variable_name))


@pytest.mark.parametrize(
    ("path", "variable_name"),
    [
        (DSN_FILES[0], "NAUTILUS_DSN"),
        (DSN_FILES[1], "NAUTILUS_DSN"),
        (DSN_FILES[2], "NAUTILUS_DSN"),
        (DSN_FILES[3], "COMPASS_PG_DSN"),
        (DSN_FILES[4], "COMPASS_PG_DSN"),
    ],
)
def test_database_jobs_have_no_connection_string_default(path, variable_name):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    default = _dsn_environment_default(tree, variable_name)

    if default is not None and not (
        isinstance(default, ast.Constant) and default.value == ""
    ):
        pytest.fail("credential_db_default_present")
    assert "_require_dsn(" in path.read_text(encoding="utf-8")
