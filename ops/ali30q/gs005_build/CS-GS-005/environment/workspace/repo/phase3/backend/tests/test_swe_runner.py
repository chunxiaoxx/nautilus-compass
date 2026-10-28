"""集成测 — services.swe_runner(合成 git repo·端到端 effect + swe_verify 链）。

自包含:临时建 git repo + buggy module + test → 验 apply+pytest+parse 链。无网络。
"""
import os, sys, subprocess, tempfile, shutil
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.swe_runner import run_candidate, apply_patch  # noqa: E402
from services.swe_verify import parse_pytest_summary, swe_reward  # noqa: E402

_BUGGY = "def add(a, b):\n    return a - b\n"          # bug: 应 +
_TEST = "from calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n"
# 把 a - b 修成 a + b 的 unified diff
_GOOD_PATCH = (
    "--- a/calc.py\n+++ b/calc.py\n@@ -1,2 +1,2 @@\n"
    " def add(a, b):\n-    return a - b\n+    return a + b\n")
_BAD_PATCH = (
    "--- a/calc.py\n+++ b/calc.py\n@@ -1,2 +1,2 @@\n"
    " def add(a, b):\n-    return a * b\n+    return a + b\n")  # 上下文不匹配=apply 失败


def _git(d, *args):
    subprocess.run(["git", "-C", d, *args], capture_output=True, text=True, check=True)


@pytest.fixture
def repo():
    d = tempfile.mkdtemp(prefix="swe_base_")
    open(os.path.join(d, "calc.py"), "w").write(_BUGGY)
    open(os.path.join(d, "test_calc.py"), "w").write(_TEST)
    try:
        _git(d, "init", "-q")
        _git(d, "config", "user.email", "t@t")
        _git(d, "config", "user.name", "t")
        _git(d, "add", "-A")
        _git(d, "commit", "-qm", "base")
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_base_fails_without_patch(repo):
    # 空 patch(no-op diff 不存在）→ 直接跑 base 测试应失败。用 run_candidate 加恒真 patch。
    from services.swe_runner import run_pytest
    out = run_pytest(repo, "test_calc.py")
    s = parse_pytest_summary(out)
    assert s["parsed"] and s["passed"] == 0 and s["failed"] == 1


def test_good_patch_makes_test_pass(repo):
    out = run_candidate(repo, _GOOD_PATCH, "test_calc.py")
    s = parse_pytest_summary(out)
    assert s["parsed"] and s["passed"] == 1
    assert swe_reward(s) == 1


def test_base_repo_untouched_after_candidate(repo):
    # run_candidate 在副本做·base 的 calc.py 仍是 buggy
    run_candidate(repo, _GOOD_PATCH, "test_calc.py")
    assert "a - b" in open(os.path.join(repo, "calc.py")).read()


def test_bad_patch_apply_fails(repo):
    out = run_candidate(repo, _BAD_PATCH, "test_calc.py")
    assert "patch_apply_failed" in out
    assert swe_reward(parse_pytest_summary(out)) is None   # 未 parse → 不混入梯度


# --- 真 SWE instance 隔离支持(2026-06-19·节点4 接 producer 前补）---
# 纯 Python repo(如 sympy）的隔离:venv 只装依赖·把打 patch 的副本放 PYTHONPATH 首位·
# 用 venv python 跑 pytest。需 run_candidate 接 python_exe + env_extra。

_ENV_TEST = (
    "import os\n\n\n"
    "def test_env_mark():\n    assert os.environ.get('SWE_MARK') == 'ok'\n")
_NOOP_PATCH = (  # 恒真 no-op:给 calc.py 加一行注释(上下文匹配）
    "--- a/calc.py\n+++ b/calc.py\n@@ -1,2 +1,2 @@\n"
    " def add(a, b):\n-    return a - b\n+    return a + b\n")


def test_run_candidate_accepts_python_exe(repo):
    # 显式传 python_exe=sys.executable 应与默认行为一致(向后兼容）
    out = run_candidate(repo, _GOOD_PATCH, "test_calc.py", python_exe=sys.executable)
    s = parse_pytest_summary(out)
    assert s["parsed"] and s["passed"] == 1


def test_run_pytest_accepts_list_target(repo):
    # 真 SWE 的 FAIL_TO_PASS 是多个 node id → test_target 须支持 list
    from services.swe_runner import run_pytest
    out = run_pytest(repo, ["test_calc.py::test_add"])
    s = parse_pytest_summary(out)
    assert s["parsed"]  # 选到了该 node(此时 buggy → failed==1）
    assert s["failed"] == 1


def test_run_candidate_env_extra_plumbed(repo):
    # env_extra 注入的环境变量须传到 pytest 子进程(PYTHONPATH 同理走此路）
    open(os.path.join(repo, "test_env.py"), "w").write(_ENV_TEST)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "add env test")
    out = run_candidate(repo, _NOOP_PATCH, "test_env.py", env_extra={"SWE_MARK": "ok"})
    s = parse_pytest_summary(out)
    assert s["parsed"] and s["passed"] == 1
    # 不注入 → 失败(证明确实靠 env_extra 而非默认）
    out2 = run_candidate(repo, _NOOP_PATCH, "test_env.py")
    assert parse_pytest_summary(out2)["failed"] == 1
