"""默认项目竞选排除自动日志洪水目录 · 平台函 #148685(飞轮→compass,2026-11-23,用户已批改法)。

现象:v5 大脑每 ~43s 往 v5-breath-auto/memory/ 落一个 ingest_*.md(日增约两千);
resolve_project 不传 project 时选"最近修改过 .md 的项目" → 默认项目恒为 v5-breath-auto,
不带项目名的召回前几名全是空壳条目。

改法(两处同改):ingest_*.md 占九成以上且总数过两百的目录不参与默认竞选;
显式传 project 时照常可访问。覆盖 mcp_server.resolve_project 与 compass_http._resolve_project。
"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_project(projects: Path, name: str, ingest_n: int, other_n: int, mtime: float) -> Path:
    mem = projects / name / "memory"
    mem.mkdir(parents=True)
    for i in range(ingest_n):
        (mem / f"ingest_{i:05d}.md").write_text("x", encoding="utf-8")
    for i in range(other_n):
        (mem / f"session_{i:03d}.md").write_text("y", encoding="utf-8")
    for f in mem.glob("*.md"):
        os.utime(f, (mtime, mtime))
    return mem


@pytest.fixture
def layout(tmp_path, monkeypatch):
    """洪水目录修改时间最新;正常项目较旧。未改前默认项目会落到洪水目录。"""
    # compass_http._resolve_project 扫 Path.home()/.claude/projects;home patch 成 tmp_path
    projects = tmp_path / ".claude" / "projects"
    _make_project(projects, "v5-breath-auto", 300, 0, mtime=2_000_000_000)
    _make_project(projects, "-Users-x-real-proj", 0, 2, mtime=1_000_000_000)
    monkeypatch.delenv("NAUTILUS_COMPASS_PROJECT", raising=False)
    monkeypatch.delenv("COMPASS_DEFAULT_PROJECT", raising=False)
    return projects


def _flood_dir(tmp_path, ingest_n, other_n):
    mem = tmp_path / "flood" / "memory"
    mem.mkdir(parents=True)
    for i in range(ingest_n):
        (mem / f"ingest_{i:05d}.md").write_text("x", encoding="utf-8")
    for i in range(other_n):
        (mem / f"session_{i:03d}.md").write_text("y", encoding="utf-8")
    return mem


def test_helper_thresholds(tmp_path):
    mcp_server = _load("mcp_server", "mcp_server.py")
    is_flood = mcp_server._is_auto_journal_flood
    # 过两百且九成以上 → 洪水
    assert is_flood(_flood_dir(tmp_path / "a", 200, 20)) is True
    # 未过两百,即便全是 ingest → 不算(小项目误伤保护)
    assert is_flood(_flood_dir(tmp_path / "b", 150, 0)) is False
    # 过两百但 ingest 不足九成 → 不算
    assert is_flood(_flood_dir(tmp_path / "c", 200, 30)) is False
    # 空目录 / 不存在 → 不算
    assert is_flood(tmp_path / "nope") is False


def test_mcp_server_default_skips_flood_and_explicit_still_works(layout, monkeypatch):
    mcp_server = _load("mcp_server", "mcp_server.py")
    monkeypatch.setattr(mcp_server, "PROJECTS_DIR", layout)
    assert mcp_server.resolve_project(None) == "-Users-x-real-proj"   # 验收①
    assert mcp_server.resolve_project("v5-breath-auto") == "v5-breath-auto"   # 验收②/④
    monkeypatch.setenv("NAUTILUS_COMPASS_PROJECT", "env-proj")
    assert mcp_server.resolve_project(None) == "env-proj"   # 既有优先级(显式 > 环境变量)不变


def _compass_http_funcs():
    """只取 compass_http.py 里这两个函数来测,不导入整个模块(免 fastapi 依赖,CI 不跳过)。"""
    import ast
    src = (ROOT / "compass_http.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    wanted = {"_is_auto_journal_flood", "_resolve_project"}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    assert {n.name for n in nodes} == wanted, "compass_http.py 缺少被测函数"
    ns = {"os": os, "Path": Path}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "compass_http.py", "exec"), ns)
    return ns


def test_compass_http_default_skips_flood_and_explicit_still_works(layout, monkeypatch):
    ns = _compass_http_funcs()
    monkeypatch.setattr(Path, "home", lambda: layout.parents[1])   # = tmp_path,扫描 tmp/.claude/projects
    assert ns["_resolve_project"](None) == "-Users-x-real-proj"
    assert ns["_resolve_project"]("v5-breath-auto") == "v5-breath-auto"
    assert ns["_is_auto_journal_flood"](layout / "v5-breath-auto" / "memory") is True
    monkeypatch.setenv("COMPASS_DEFAULT_PROJECT", "env-proj")
    assert ns["_resolve_project"](None) == "env-proj"
