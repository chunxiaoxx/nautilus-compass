"""Fail-closed secret scanning for Compass release surfaces and wheels."""

from __future__ import annotations

import ast
import re
import warnings
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import List, Tuple


_SENSITIVE_NAME = re.compile(
    r"(?:password|passwd|pwd|secret|token|api_?key|credential)", re.IGNORECASE
)
_NON_SECRET_NAME_SUFFIXES = (
    "_count",
    "_endpoint",
    "_hash",
    "_id",
    "_limit",
    "_port",
    "_ttl",
    "_type",
    "_url",
)
_PRIVATE_KEY_MARKER = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
_DATABASE_CREDENTIAL_URL = re.compile(
    r"(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis)://"
    r"[^\s/:@]+:[^\s/@]+@",
    re.IGNORECASE,
)
_SERVICE_ENVIRONMENT = re.compile(
    r"^\s*Environment=(?:\"?)([A-Za-z_][A-Za-z0-9_]*)=([^\s\"]+)"
)
_TEXT_SUFFIXES = frozenset(
    {".py", ".service", ".sh", ".ps1", ".txt", ".json", ".toml", ".yml", ".yaml"}
)
_RELEASE_DIRS = (
    "gep",
    "sdk",
    "middleware",
    "storage",
    "proof",
    "drift",
    "recall_pkg",
    "skills_pkg",
    "judges",
    "ops",
    "scripts",
)
_EXCLUDED_PARTS = frozenset(
    {
        ".git",
        ".codex",
        ".claude",
        "__pycache__",
        "_archive",
        "tests",
        "examples",
        "docs",
    }
)


class ReleaseSecurityError(ValueError):
    """Bounded scanner failure with a stable reason code."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


@dataclass(frozen=True, order=True)
class SecurityFinding:
    """Redacted finding. Matched source values are intentionally absent."""

    path: str
    line: int
    rule_code: str


def _target_names(target: ast.AST) -> Tuple[str, ...]:
    if isinstance(target, ast.Name):
        return (target.id,)
    if isinstance(target, ast.Attribute):
        return (target.attr,)
    if isinstance(target, ast.Subscript):
        key = target.slice
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            return (key.value,)
    if isinstance(target, (ast.Tuple, ast.List)):
        return tuple(name for item in target.elts for name in _target_names(item))
    return ()


def _assigned_names(node: ast.AST) -> Tuple[str, ...]:
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, ast.AnnAssign):
        targets = (node.target,)
    else:
        return ()
    return tuple(name for target in targets for name in _target_names(target))


def _is_literal_secret(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    lowered = stripped.casefold()
    return not (
        stripped.startswith("$")
        or stripped.startswith("${")
        or stripped.startswith("%")
        or lowered.startswith("<redacted")
        or lowered.startswith("change_me")
        or lowered.startswith("your_")
        or lowered in {"example", "placeholder", "dummy"}
    )


def _is_secret_name(value: str) -> bool:
    lowered = value.casefold()
    return _SENSITIVE_NAME.search(value) is not None and not lowered.endswith(
        _NON_SECRET_NAME_SUFFIXES
    )


def _scan_text(display_path: str, text: str, is_python: bool) -> Tuple[SecurityFinding, ...]:
    findings = set()
    lines = text.splitlines()
    for index, line in enumerate(lines, start=1):
        if _PRIVATE_KEY_MARKER.search(line):
            findings.add(SecurityFinding(display_path, index, "private_key_marker"))
        if _DATABASE_CREDENTIAL_URL.search(line):
            findings.add(SecurityFinding(display_path, index, "credential_db_url"))
        service_match = _SERVICE_ENVIRONMENT.match(line)
        if service_match and _SENSITIVE_NAME.search(service_match.group(1)):
            if _is_literal_secret(service_match.group(2)):
                findings.add(
                    SecurityFinding(
                        display_path,
                        index,
                        "plaintext_service_environment",
                    )
                )
        if Path(display_path).name.startswith(".env") and "=" in line:
            name, value = line.split("=", 1)
            if _is_secret_name(name) and _is_literal_secret(value):
                findings.add(
                    SecurityFinding(display_path, index, "plaintext_env_assignment")
                )

    if not is_python:
        return tuple(sorted(findings))

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            warnings.simplefilter("ignore", DeprecationWarning)
            tree = ast.parse(text, filename=display_path)
    except SyntaxError:
        findings.add(SecurityFinding(display_path, 0, "invalid_python_source"))
        return tuple(sorted(findings))

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            names = _assigned_names(node)
            if (
                isinstance(value, ast.Constant)
                and isinstance(value.value, str)
                and _is_literal_secret(value.value)
                and any(_is_secret_name(name) for name in names)
            ):
                findings.add(
                    SecurityFinding(
                        display_path,
                        node.lineno,
                        "plaintext_sensitive_assignment",
                    )
                )
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and _is_secret_name(key.value)
                    and isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                    and _is_literal_secret(value.value)
                ):
                    findings.add(
                        SecurityFinding(
                            display_path,
                            value.lineno,
                            "plaintext_sensitive_mapping_value",
                        )
                    )
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                value = keyword.value
                if (
                    keyword.arg
                    and _is_secret_name(keyword.arg)
                    and isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                    and _is_literal_secret(value.value)
                ):
                    findings.add(
                        SecurityFinding(
                            display_path,
                            value.lineno,
                            "plaintext_sensitive_call_argument",
                        )
                    )
    return tuple(sorted(findings))


def scan_source_file(path: Path, max_bytes: int = 2 * 1024 * 1024) -> Tuple[SecurityFinding, ...]:
    candidate = Path(path)
    try:
        size = candidate.stat().st_size
    except OSError as exc:
        raise ReleaseSecurityError("source_unreadable") from exc
    if size > max_bytes:
        return (SecurityFinding(candidate.as_posix(), 0, "source_size_limit"),)
    try:
        text = candidate.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ReleaseSecurityError("source_unreadable") from exc
    return _scan_text(candidate.as_posix(), text, candidate.suffix.lower() == ".py")


def _is_release_file(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if any(part in _EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.name == ".env.example":
        return True
    return path.suffix.lower() in _TEXT_SUFFIXES


def release_surface_paths(root: Path) -> Tuple[Path, ...]:
    base = Path(root)
    selected = set()
    for path in base.iterdir():
        if path.is_file() and _is_release_file(path, base):
            selected.add(path)
    for directory_name in _RELEASE_DIRS:
        directory = base / directory_name
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and _is_release_file(path, base):
                selected.add(path)
    return tuple(sorted(selected))


def scan_release_surfaces(root: Path) -> Tuple[SecurityFinding, ...]:
    findings: List[SecurityFinding] = []
    for path in release_surface_paths(root):
        findings.extend(scan_source_file(path))
    return tuple(sorted(findings))


def _unsafe_member_path(name: str) -> bool:
    normalized = PurePosixPath(name.replace("\\", "/"))
    return normalized.is_absolute() or ".." in normalized.parts


def scan_wheel(
    wheel_path: Path,
    max_members: int = 10000,
    max_member_bytes: int = 2 * 1024 * 1024,
) -> Tuple[SecurityFinding, ...]:
    path = Path(wheel_path)
    findings: List[SecurityFinding] = []
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > max_members:
                raise ReleaseSecurityError("wheel_member_limit")
            for member in members:
                display_path = member.filename
                if _unsafe_member_path(display_path):
                    findings.append(
                        SecurityFinding(display_path, 0, "wheel_path_traversal")
                    )
                    continue
                if member.is_dir() or Path(display_path).suffix.lower() not in _TEXT_SUFFIXES:
                    continue
                if member.file_size > max_member_bytes:
                    findings.append(
                        SecurityFinding(display_path, 0, "wheel_member_size_limit")
                    )
                    continue
                try:
                    text = archive.read(member).decode("utf-8")
                except (KeyError, OSError, UnicodeDecodeError, RuntimeError):
                    findings.append(
                        SecurityFinding(display_path, 0, "wheel_member_unreadable")
                    )
                    continue
                findings.extend(
                    _scan_text(
                        display_path,
                        text,
                        Path(display_path).suffix.lower() == ".py",
                    )
                )
    except (OSError, zipfile.BadZipFile) as exc:
        raise ReleaseSecurityError("invalid_wheel") from exc
    return tuple(sorted(set(findings)))


__all__ = [
    "ReleaseSecurityError",
    "SecurityFinding",
    "release_surface_paths",
    "scan_release_surfaces",
    "scan_source_file",
    "scan_wheel",
]
