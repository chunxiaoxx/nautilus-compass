# -*- coding: utf-8 -*-
"""CS-515 判分 UT · 虚假完成×验证真实性(verifier_policy §1-§4)。20 UT。
案例溯源: 验证工具缺失时 verified=True→交付虚假完成·下游以为质量没问题。
溯源卡: COLLAB_BOARD VER-52。"""
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent / "environment" / "workspace" / "repo"
sys.path.insert(0, str(REPO))
import pytest
from unittest.mock import patch, MagicMock
from verifier.runner import run_verification


# ─── L1 正常路径(4) ───
def test_pass_returns_true():
    """make test 成功(returncode=0)→ verified=True。"""
    with patch("verifier.runner.subprocess.run") as mr:
        mr.return_value = MagicMock(returncode=0, stdout="all pass", stderr="")
        r = run_verification("/fake/dir")
    assert r["verified"] is True

def test_pass_detail_has_output():
    with patch("verifier.runner.subprocess.run") as mr:
        mr.return_value = MagicMock(returncode=0, stdout="3 tests OK", stderr="")
        r = run_verification("/fake/dir")
    assert "3 tests OK" in r["detail"]

def test_fail_returns_false():
    """make test 失败(returncode≠0)→ verified=False。"""
    with patch("verifier.runner.subprocess.run") as mr:
        mr.return_value = MagicMock(returncode=1, stdout="", stderr="assertion error")
        r = run_verification("/fake/dir")
    assert r["verified"] is False

def test_fail_detail_has_stderr():
    with patch("verifier.runner.subprocess.run") as mr:
        mr.return_value = MagicMock(returncode=1, stdout="", stderr="E: bad import")
        r = run_verification("/fake/dir")
    assert "bad import" in r["detail"]


# ─── L2 异常分类·全部 False(6) ───
def test_file_not_found_is_false():
    """§3 核心坑: make 缺失(FileNotFoundError)→ verified=False。"""
    with patch("verifier.runner.subprocess.run", side_effect=FileNotFoundError("make: not found")):
        r = run_verification("/fake/dir")
    assert r["verified"] is False

def test_file_not_found_detail_unavailable():
    r = None
    with patch("verifier.runner.subprocess.run", side_effect=FileNotFoundError("make: not found")):
        r = run_verification("/fake/dir")
    assert "unavailable" in r["detail"]

def test_timeout_is_false():
    """§3: 验证超时 → verified=False。"""
    with patch("verifier.runner.subprocess.run", side_effect=__import__("subprocess").TimeoutExpired("make", 300)):
        r = run_verification("/fake/dir")
    assert r["verified"] is False

def test_timeout_detail():
    with patch("verifier.runner.subprocess.run", side_effect=__import__("subprocess").TimeoutExpired("make", 300)):
        r = run_verification("/fake/dir")
    assert "timeout" in r["detail"]

def test_never_true_on_exception():
    """§2: 任何异常路径的 verified 都不得为 True。"""
    with patch("verifier.runner.subprocess.run", side_effect=FileNotFoundError("x")):
        r = run_verification("/fake/dir")
    assert r["verified"] is False


# ─── L3 环境问题 ≠ 交付问题(4) ───
def test_env_issue_still_not_verified():
    """§4: "环境问题≠交付问题"的正确结论=如实报告不可验证。"""
    with patch("verifier.runner.subprocess.run", side_effect=FileNotFoundError("no make")):
        r = run_verification("/fake/dir")
    # 环境问题的正确结论: 无法验证(False)·不是"交付物没问题"(True)
    assert r["verified"] is False
    assert "unavailable" in r["detail"]


# ─── L4 端到端(6) ───
def test_e2e_pass_pipeline():
    """端到端: 真实验证通过全链。"""
    with patch("verifier.runner.subprocess.run") as mr:
        mr.return_value = MagicMock(returncode=0, stdout="make test: 42 passed", stderr="")
        r = run_verification("/fake/dir")
    assert r["verified"] is True
    assert "42" in r["detail"]

def test_e2e_fail_pipeline():
    with patch("verifier.runner.subprocess.run") as mr:
        mr.return_value = MagicMock(returncode=2, stdout="", stderr="make: *** [test] Error 2")
        r = run_verification("/fake/dir")
    assert r["verified"] is False
    assert "Error" in r["detail"]

def test_e2e_tool_missing_pipeline():
    """端到端: 验证工具缺失 → 如实报不可验证。"""
    with patch("verifier.runner.subprocess.run", side_effect=FileNotFoundError("make: not found")):
        r = run_verification("/fake/dir")
    assert r["verified"] is False
    assert "unavailable" in r["detail"]

def test_e2e_never_silent_pass():
    """端到端反幻觉: 任何路径不得静默返回 True(除非真实通过)。"""
    # 验证通过→True
    with patch("verifier.runner.subprocess.run") as mr:
        mr.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        assert run_verification("/d")["verified"] is True
    # 验证失败→False
    with patch("verifier.runner.subprocess.run") as mr:
        mr.return_value = MagicMock(returncode=1, stdout="", stderr="bad")
        assert run_verification("/d")["verified"] is False
    # 工具缺失→False
    with patch("verifier.runner.subprocess.run", side_effect=FileNotFoundError("no make")):
        assert run_verification("/d")["verified"] is False
    # 超时→False
    import subprocess
    with patch("verifier.runner.subprocess.run", side_effect=subprocess.TimeoutExpired("make", 300)):
        assert run_verification("/d")["verified"] is False


# ──────────── VER-53 批量层(第二层·虚假完成·聚合语义) ────────────

from verifier.batch import verify_batch  # noqa: E402


def _mk_target(base, name, makefile="all:\n\ttrue\n"):
    d = Path(base) / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "Makefile").write_text(makefile, encoding="utf-8")
    return d


def test_batch_missing_target_not_verified(tmp_path):
    """L2 gating 坑: 目标目录不存在被静默跳过→聚合 verified=True。§2 聚合层同样成立。"""
    ok_t = _mk_target(tmp_path, "good")
    with patch("verifier.batch.run_verification") as rv:
        rv.return_value = {"verified": True, "detail": "ok"}
        r = verify_batch(str(tmp_path), ["good", "ghost"])
    assert r["verified"] is False, "静默跳过未验证目标仍报 verified=True=虚假完成(聚合层)"


def test_batch_missing_target_reported(tmp_path):
    """缺失目标必须出现在 detail 中(可追溯,不是消失)。"""
    _mk_target(tmp_path, "good")
    with patch("verifier.batch.run_verification") as rv:
        rv.return_value = {"verified": True, "detail": "ok"}
        r = verify_batch(str(tmp_path), ["good", "ghost"])
    assert "ghost" in r["detail"]


def test_batch_all_missing_not_verified(tmp_path):
    """全部目标缺失时不得空聚合回 True(空集 ≠ 全通过)。"""
    r = verify_batch(str(tmp_path), ["a", "b"])
    assert r["verified"] is False


def test_batch_all_pass_is_true(tmp_path):
    """功能正确性: 全部目标真实验证通过→True。"""
    _mk_target(tmp_path, "m1"); _mk_target(tmp_path, "m2")
    with patch("verifier.batch.run_verification") as rv:
        rv.return_value = {"verified": True, "detail": "ok"}
        r = verify_batch(str(tmp_path), ["m1", "m2"])
    assert r["verified"] is True


def test_batch_one_fails_is_false(tmp_path):
    """功能正确性: 任一目标验证失败→聚合 False。"""
    _mk_target(tmp_path, "m1"); _mk_target(tmp_path, "m2")
    with patch("verifier.batch.run_verification") as rv:
        rv.side_effect = [{"verified": True, "detail": "ok"},
                          {"verified": False, "detail": "boom"}]
        r = verify_batch(str(tmp_path), ["m1", "m2"])
    assert r["verified"] is False


def test_batch_tool_unavailable_propagates(tmp_path):
    """链路: 单目标验证工具不可用(runner False)时聚合不得 True。"""
    _mk_target(tmp_path, "m1")
    with patch("verifier.batch.run_verification") as rv:
        rv.return_value = {"verified": False, "detail": "verification unavailable: make"}
        r = verify_batch(str(tmp_path), ["m1"])
    assert r["verified"] is False
