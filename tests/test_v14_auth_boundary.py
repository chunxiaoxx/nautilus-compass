"""Negative tests for the v14 authenticated user→project boundary."""

import ast
import json
import os
from pathlib import Path
from typing import Optional

import pytest

ROOT = Path(__file__).resolve().parents[1]


class _HTTPException(Exception):
    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code = status_code


def _boundary_namespace():
    source = (ROOT / "compass_http_v09.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in {"_v14_allowed_projects", "_v14_require_project"}
    }
    ns = {
        "_v14_os": os,
        "_v14_json": json,
        "Optional": Optional,
        "HTTPException": _HTTPException,
    }
    exec(compile(ast.Module(body=list(wanted.values()), type_ignores=[]), str(ROOT / "compass_http_v09.py"), "exec"), ns)
    return ns


def test_project_mapping_is_fail_closed_without_configuration(monkeypatch):
    ns = _boundary_namespace()
    monkeypatch.delenv("COMPASS_V14_PROJECT_MAP", raising=False)

    assert ns["_v14_allowed_projects"]("u_test") == set()
    with pytest.raises(_HTTPException) as exc:
        ns["_v14_require_project"]("u_test", "C--Users-chunx")
    assert exc.value.status_code == 403


def test_project_mapping_rejects_other_users_and_projects(monkeypatch):
    ns = _boundary_namespace()
    monkeypatch.setenv(
        "COMPASS_V14_PROJECT_MAP",
        '{"u_owner": ["project-owner"], "u_other": ["project-other"]}',
    )

    assert ns["_v14_require_project"]("u_owner", "project-owner") == "project-owner"
    with pytest.raises(_HTTPException) as exc:
        ns["_v14_require_project"]("u_owner", "project-other")
    assert exc.value.status_code == 403


def test_v14_recall_signature_depends_on_auth_user():
    source = (ROOT / "compass_http_v09.py").read_text(encoding="utf-8")

    assert "user_id: str = Depends(auth_user)" in source
    assert "scope=user disabled until mapped-project filtering is enabled" in source
    assert "effective_agent_id = user_id" in source
