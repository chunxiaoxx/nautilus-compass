"""TDD tests for RepoMap cycle 2 · stdlib-only ast scanning + lexical rank."""
from pathlib import Path

import pytest

from engine.repo_map import RepoMap, Symbol, FileSymbols


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Create a small fake repo with 3 py files + 1 excluded."""
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("")
    (tmp_path / "pkg" / "auth.py").write_text(
        '"""Auth module."""\n'
        "import os\n"
        "from typing import Optional\n\n"
        "class AuthService:\n"
        '    """Handles login."""\n'
        "    def __init__(self, db):\n"
        "        self.db = db\n\n"
        "def verify_token(token: str) -> bool:\n"
        '    """Verify a JWT."""\n'
        "    return True\n\n"
        "async def login(user: str, pwd: str) -> Optional[dict]:\n"
        "    return None\n"
    )
    (tmp_path / "pkg" / "billing.py").write_text(
        "class Invoice:\n    pass\n\n"
        "def compute_total(items: list) -> float:\n"
        "    return 0.0\n"
    )
    # Excluded dir
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "cache.py").write_text("# should be excluded\n")
    # Syntax-error file (should be skipped silently)
    (tmp_path / "broken.py").write_text("def (\n")
    return tmp_path


def test_repo_map_scans_py_files(repo: Path):
    rm = RepoMap(str(repo))
    files = rm.scan()
    rels = set(files.keys())
    assert "pkg/auth.py" in rels
    assert "pkg/billing.py" in rels
    assert "pkg/__init__.py" in rels
    # Excluded
    assert not any("__pycache__" in r for r in rels)


def test_parse_file_extracts_class(repo: Path):
    rm = RepoMap(str(repo))
    fs = rm.parse_file(repo / "pkg" / "auth.py")
    assert any(s.name == "AuthService" and s.kind == "class" for s in fs.classes)


def test_parse_file_extracts_function_signature(repo: Path):
    rm = RepoMap(str(repo))
    fs = rm.parse_file(repo / "pkg" / "auth.py")
    verify = next((s for s in fs.functions if s.name == "verify_token"), None)
    assert verify is not None
    assert "def verify_token" in verify.signature
    assert "token: str" in verify.signature
    assert "-> bool" in verify.signature


def test_parse_file_extracts_async_function(repo: Path):
    rm = RepoMap(str(repo))
    fs = rm.parse_file(repo / "pkg" / "auth.py")
    login = next((s for s in fs.functions if s.name == "login"), None)
    assert login is not None
    assert login.signature.startswith("async def login")


def test_parse_file_extracts_imports(repo: Path):
    rm = RepoMap(str(repo))
    fs = rm.parse_file(repo / "pkg" / "auth.py")
    assert "os" in fs.imports
    assert any("typing" in imp for imp in fs.imports)


def test_parse_file_handles_syntax_error(repo: Path):
    rm = RepoMap(str(repo))
    # Should not raise · returns empty FileSymbols
    fs = rm.parse_file(repo / "broken.py")
    assert fs.classes == []
    assert fs.functions == []


def test_rank_files_by_task_terms(repo: Path):
    rm = RepoMap(str(repo))
    rm.scan()
    ranked = rm.rank_files("implement auth login")
    # auth.py should rank higher than billing.py for this task
    auth_score = next((s for s, fs in ranked if "auth" in fs.rel_path), None)
    billing_score = next((s for s, fs in ranked if "billing" in fs.rel_path), None)
    assert auth_score is not None
    assert billing_score is None or auth_score > billing_score


def test_rank_files_returns_empty_for_no_terms(repo: Path):
    rm = RepoMap(str(repo))
    rm.scan()
    ranked = rm.rank_files("")
    assert ranked == []


def test_render_respects_token_budget(repo: Path):
    rm = RepoMap(str(repo))
    rm.scan()
    rendered = rm.render("auth login token", token_budget=50)
    # 50 tokens * 4 chars ≈ 200 chars cap
    assert len(rendered) <= 250  # small margin for last-line overrun


def test_render_includes_top_file(repo: Path):
    rm = RepoMap(str(repo))
    rm.scan()
    rendered = rm.render("verify auth token", token_budget=2000)
    assert "auth.py" in rendered
    assert "verify_token" in rendered or "AuthService" in rendered


def test_render_with_no_matches_returns_empty(repo: Path):
    rm = RepoMap(str(repo))
    rm.scan()
    rendered = rm.render("zzz_no_match_keyword_xyz", token_budget=1000)
    assert rendered == ""


def test_exclude_ignores_root_path_parts(tmp_path: Path):
    """Regression · root dir name colliding with DEFAULT_EXCLUDE (e.g. .claude)
    must not blanket-exclude files BELOW root."""
    nested = tmp_path / ".claude" / "worktrees" / "engine-mvp"
    nested.mkdir(parents=True)
    (nested / "real.py").write_text("def real(): pass\n")

    rm = RepoMap(str(nested))
    files = rm.scan()
    assert "real.py" in files


def test_excludes_dirs_via_custom_exclude(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("def foo(): pass\n")
    (tmp_path / "_ignore").mkdir()
    (tmp_path / "_ignore" / "b.py").write_text("def bar(): pass\n")

    rm = RepoMap(str(tmp_path), exclude_dirs={"_ignore"})
    files = rm.scan()
    assert any("a.py" in r for r in files)
    assert not any("_ignore" in r for r in files)
