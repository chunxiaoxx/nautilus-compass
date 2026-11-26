"""默认项目判定的 60 秒缓存 · 2026-11-27。

现象(云上实测):不传 project 的每次 recall,resolve_project 都遍历 12,167 个目录、
stat 61,518 个记忆文件,耗时 2.76 秒——MCP 召回"3 秒左右"的主因。

改法:兜底扫描结果缓存 60 秒;缓存键带项目根目录路径(换根目录不串台);
显式 project 与环境变量优先级不变。本文件把这三条钉住,并带一个阴性对照
(TTL 过期后必须重新扫描并反映新布局)。
"""
import importlib.util
import os
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load():
    spec = importlib.util.spec_from_file_location("mcp_server_default_cache", ROOT / "mcp_server.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _project(projects: Path, name: str, mtime: float) -> None:
    mem = projects / name / "memory"
    mem.mkdir(parents=True)
    for i in range(3):
        path = mem / f"session_{i:03d}.md"
        path.write_text("y", encoding="utf-8")
        os.utime(path, (mtime, mtime))


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("NAUTILUS_COMPASS_PROJECT", raising=False)
    projects = tmp_path / ".claude" / "projects"
    _project(projects, "older-proj", mtime=1_000_000_000)
    _project(projects, "newer-proj", mtime=2_000_000_000)
    mod = _load()
    monkeypatch.setattr(mod, "PROJECTS_DIR", projects)
    scans = {"n": 0}
    real_glob = Path.glob

    def counting_glob(self, pattern):
        scans["n"] += 1
        return real_glob(self, pattern)

    monkeypatch.setattr(Path, "glob", counting_glob)
    return mod, projects, scans


def test_second_call_within_ttl_does_not_rescan(env):
    mod, _, scans = env
    assert mod.resolve_project(None) == "newer-proj"
    first = scans["n"]
    assert first >= 2  # 阳性对照:第一次确实扫了
    assert mod.resolve_project(None) == "newer-proj"
    assert scans["n"] == first  # 第二次零扫描


def test_negative_control_after_ttl_expiry_rescans_new_layout(env, monkeypatch):
    mod, projects, scans = env
    assert mod.resolve_project(None) == "newer-proj"
    _project(projects, "brand-new-proj", mtime=3_000_000_000)
    assert mod.resolve_project(None) == "newer-proj"  # TTL 内仍给旧结果
    monkeypatch.setattr(mod, "_DEFAULT_PROJECT_CACHE", ("", 0.0, None))  # 等价于缓存过期
    assert mod.resolve_project(None) == "brand-new-proj"  # 过期后必须反映新布局


def test_cache_is_keyed_by_root_so_roots_do_not_leak(env, monkeypatch, tmp_path):
    mod, _, _ = env
    assert mod.resolve_project(None) == "newer-proj"
    other = tmp_path / "other-root" / "projects"
    _project(other, "only-proj-here", mtime=1_000_000_000)
    monkeypatch.setattr(mod, "PROJECTS_DIR", other)
    assert mod.resolve_project(None) == "only-proj-here"


def test_explicit_and_env_still_win_over_cache(env, monkeypatch):
    mod, _, scans = env
    assert mod.resolve_project("explicit-proj") == "explicit-proj"
    assert scans["n"] == 0
    monkeypatch.setenv("NAUTILUS_COMPASS_PROJECT", "env-proj")
    assert mod.resolve_project(None) == "env-proj"
    assert scans["n"] == 0


def test_ttl_is_sixty_seconds_and_uses_wall_clock(env):
    mod, projects, _ = env
    assert mod._DEFAULT_PROJECT_TTL_S == 60.0
    now = time.time()
    mod._default_project_remember(now, projects, "x")
    assert mod._default_project_cached(now + 59.0, projects) == "x"
    assert mod._default_project_cached(now + 61.0, projects) is None
