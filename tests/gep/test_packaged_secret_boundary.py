from __future__ import annotations

import ast
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIRS = (
    "gep",
    "sdk",
    "middleware",
    "storage",
    "proof",
    "drift",
    "recall_pkg",
    "skills_pkg",
    "judges",
    "mcp_durable",
)
SENSITIVE_NAME = re.compile(
    r"(?:password|passwd|pwd|secret|token|api_?key|credential)",
    re.IGNORECASE,
)
PRIVATE_KEY_MARKER = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
DATABASE_CREDENTIAL_URL = re.compile(
    r"(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis)://"
    r"[^\s/:@]+:[^\s/@]+@",
    re.IGNORECASE,
)


def packaged_python_files() -> tuple[Path, ...]:
    paths = set(REPO_ROOT.glob("*.py"))
    for directory in PACKAGE_DIRS:
        paths.update((REPO_ROOT / directory).rglob("*.py"))
    return tuple(sorted(paths))


def _assigned_names(node: ast.Assign | ast.AnnAssign) -> tuple[str, ...]:
    targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
    return tuple(target.id for target in targets if isinstance(target, ast.Name))


def test_packaged_python_has_no_plaintext_secret_literals() -> None:
    findings: list[str] = []
    for path in packaged_python_files():
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        relative = path.relative_to(REPO_ROOT).as_posix()

        if PRIVATE_KEY_MARKER.search(source):
            findings.append(f"{relative}: private-key marker")
        if DATABASE_CREDENTIAL_URL.search(source):
            findings.append(f"{relative}: credential-bearing database URL")

        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                names = _assigned_names(node)
                if (
                    isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                    and value.value
                    and any(SENSITIVE_NAME.search(name) for name in names)
                ):
                    findings.append(
                        f"{relative}:{node.lineno}: plaintext sensitive assignment"
                    )
            elif isinstance(node, ast.Call):
                for keyword in node.keywords:
                    value = keyword.value
                    if (
                        keyword.arg
                        and SENSITIVE_NAME.search(keyword.arg)
                        and isinstance(value, ast.Constant)
                        and isinstance(value.value, str)
                        and value.value
                    ):
                        findings.append(
                            f"{relative}:{value.lineno}: plaintext sensitive call argument"
                        )

    assert findings == []


def test_compass_health_database_connection_is_environment_backed() -> None:
    path = REPO_ROOT / "compass_http_v09.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    health = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "compass_health"
    )
    connect_calls = [
        node
        for node in ast.walk(health)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "connect"
    ]

    assert len(connect_calls) == 2  # daemon socket + PostgreSQL
    postgres_call = next(
        call
        for call in connect_calls
        if any(keyword.arg == "connect_timeout" for keyword in call.keywords)
    )
    assert postgres_call.args
    assert not isinstance(postgres_call.args[0], ast.Constant)
    assert not {
        keyword.arg for keyword in postgres_call.keywords
    }.intersection({"host", "user", "password", "dbname"})
    assert any(
        isinstance(node, ast.Constant) and node.value == "COMPASS_PG_DSN"
        for node in ast.walk(health)
    )
