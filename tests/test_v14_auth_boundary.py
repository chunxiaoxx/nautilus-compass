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
        and node.name in {
            "_v14_allowed_projects",
            "_v14_require_project",
            "_v14_union_projects",
        }
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


def test_project_mapping_rejects_path_escape_even_if_misconfigured(monkeypatch):
    ns = _boundary_namespace()
    monkeypatch.setenv(
        "COMPASS_V14_PROJECT_MAP",
        json.dumps({"u_owner": ["../outside", "/tmp/outside", "safe/project", ".", ".."]}),
    )

    for unsafe in ("../outside", "/tmp/outside", "safe/project", ".", ".."):
        with pytest.raises(_HTTPException) as exc:
            ns["_v14_require_project"]("u_owner", unsafe)
        assert exc.value.status_code == 403


def _recall_namespace(monkeypatch):
    source = (ROOT / "compass_http_v09.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in {
            "_v14_allowed_projects",
            "_v14_require_project",
            "_v14_union_projects",
            "v14_recall",
        }
    }
    calls = []
    scores = {"project-a": 0.2, "project-b": 0.9}

    def call_daemon(req, timeout):
        calls.append(dict(req))
        project = req["project"]
        return {
            "ok": True,
            "scope": "project",
            "recall": [{"path": project, "project": project, "score": scores[project]}],
            "projects_scanned": [project],
            "fresh_extra": [],
        }

    class _App:
        def get(self, *args, **kwargs):
            return lambda function: function

    ns = {
        "_v14_os": os,
        "_v14_json": json,
        "Optional": Optional,
        "HTTPException": _HTTPException,
        "Header": lambda *args, **kwargs: None,
        "Depends": lambda *args, **kwargs: None,
        "auth_user": object(),
        "app": _App(),
        "_call_v14_daemon": call_daemon,
        "_v14_focus_throttled": lambda *args: False,
        "_v14_poi_boost": lambda hits: hits,
        "_v14_emit_poi_candidate": lambda *args: 0,
    }
    monkeypatch.setenv(
        "COMPASS_V14_PROJECT_MAP",
        '{"u_owner": ["project-a", "project-b"], "u_other": ["project-other"]}',
    )
    monkeypatch.setenv("COMPASS_NO_POI_CANDIDATE", "1")
    monkeypatch.delenv("COMPASS_V14_UNION_PROJECT_MAP", raising=False)
    exec(compile(ast.Module(body=list(wanted.values()), type_ignores=[]), str(ROOT / "compass_http_v09.py"), "exec"), ns)
    return ns, calls


def test_v14_user_scope_unions_only_mapped_projects(monkeypatch):
    ns, calls = _recall_namespace(monkeypatch)

    result = ns["v14_recall"](
        "hello", top_k=1, scope="user", project="../outside", user_id="u_owner"
    )

    assert [call["project"] for call in calls] == ["project-a", "project-b"]
    assert all(call["scope"] == "project" for call in calls)
    assert result["ok"] is True
    assert result["scope"] == "user"
    assert result["projects_scanned_count"] == 2
    assert [hit["path"] for hit in result["hits"]] == ["project-b"]


def test_v14_user_scope_uses_only_configured_healthy_subset(monkeypatch):
    ns, calls = _recall_namespace(monkeypatch)
    monkeypatch.setenv(
        "COMPASS_V14_UNION_PROJECT_MAP",
        '{"u_owner": ["project-b", "project-other"]}',
    )

    result = ns["v14_recall"]("hello", scope="user", user_id="u_owner")

    assert [call["project"] for call in calls] == ["project-b"]
    assert result["ok"] is True
    assert result["projects_scanned"] == ["project-b"]


def test_v14_user_scope_rejects_malformed_union_configuration(monkeypatch):
    ns, calls = _recall_namespace(monkeypatch)
    monkeypatch.setenv("COMPASS_V14_UNION_PROJECT_MAP", "{not-json")

    with pytest.raises(_HTTPException) as exc:
        ns["v14_recall"]("hello", scope="user", user_id="u_owner")
    assert exc.value.status_code == 403
    assert calls == []


def test_v14_user_scope_never_forwards_unsafe_mapped_names(monkeypatch):
    ns, calls = _recall_namespace(monkeypatch)
    monkeypatch.setenv(
        "COMPASS_V14_PROJECT_MAP",
        '{"u_owner": ["project-a", "../outside", "safe/project"]}',
    )

    result = ns["v14_recall"]("hello", scope="user", user_id="u_owner")

    assert [call["project"] for call in calls] == ["project-a"]
    assert result["projects_scanned"] == ["project-a"]


def test_v14_user_scope_fails_closed_without_mapping(monkeypatch):
    ns, calls = _recall_namespace(monkeypatch)

    with pytest.raises(_HTTPException) as exc:
        ns["v14_recall"]("hello", scope="user", user_id="u_missing")
    assert exc.value.status_code == 403
    assert calls == []


def test_v14_ingest_uses_the_same_authenticated_project_boundary():
    source = (ROOT / "compass_http_v09.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    ingest = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "v14_ingest_obs"
    )
    args = ingest.args.args
    defaults = [None] * (len(args) - len(ingest.args.defaults)) + list(ingest.args.defaults)
    dependencies = {
        arg.arg: ast.unparse(default)
        for arg, default in zip(args, defaults)
        if default is not None
    }

    assert dependencies.get("user_id") == "Depends(auth_user)"
    assert "authorization" not in dependencies
    ingest_source = ast.get_source_segment(source, ingest)
    assert "_v14_require_project(user_id" in ingest_source
    assert "jwt.decode" not in ingest_source
