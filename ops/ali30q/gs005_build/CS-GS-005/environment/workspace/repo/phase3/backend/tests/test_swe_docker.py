"""TDD — services.swe_docker 的纯解析(官方 SWE-bench harness report.json → 离散 reward）。

官方 harness 输出二元 resolved·但 report.json 的 tests_status.FAIL_TO_PASS.success/failure
给逐项结果 → reward = len(FAIL_TO_PASS.success)(path B 离散梯度·替本地 pytest）。
Docker run 本身是 integration(需 Docker·不在纯单测）·此处只测 report 解析。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importlib  # noqa: E402
from services.swe_docker import (  # noqa: E402
    parse_harness_report, remote_cleanup_cmd, DEFAULT_SWE_EVAL_TIMEOUT)


_REPORT = {
    "astropy__astropy-6938": {
        "patch_is_None": False,
        "patch_exists": True,
        "patch_successfully_applied": True,
        "resolved": False,
        "tests_status": {
            "FAIL_TO_PASS": {"success": ["test_a"], "failure": ["test_b"]},
            "PASS_TO_PASS": {"success": ["p1", "p2", "p3"], "failure": []},
            "FAIL_TO_FAIL": {"success": [], "failure": []},
            "PASS_TO_FAIL": {"success": [], "failure": []},
        },
    }
}


def _write(tmp_path, obj):
    p = tmp_path / "report.json"
    p.write_text(json.dumps(obj), encoding="utf-8")
    return str(p)


def test_parse_report_extracts_f2p_passed(tmp_path):
    r = parse_harness_report(_write(tmp_path, _REPORT), "astropy__astropy-6938")
    assert r["f2p_total"] == 2
    assert r["f2p_passed"] == 1                 # 离散 reward = 过 1/2
    assert r["f2p_fail_tests"] == ["test_b"]
    assert r["p2p_passed"] == 3 and r["p2p_total"] == 3
    assert r["applied"] is True
    assert r["resolved"] is False
    assert r["parsed"] is True


def test_parse_report_resolved_all_f2p(tmp_path):
    obj = json.loads(json.dumps(_REPORT))
    obj["astropy__astropy-6938"]["tests_status"]["FAIL_TO_PASS"] = {
        "success": ["test_a", "test_b"], "failure": []}
    obj["astropy__astropy-6938"]["resolved"] = True
    r = parse_harness_report(_write(tmp_path, obj), "astropy__astropy-6938")
    assert r["f2p_passed"] == 2 and r["f2p_total"] == 2 and r["resolved"] is True


def test_parse_report_patch_not_applied(tmp_path):
    obj = json.loads(json.dumps(_REPORT))
    obj["astropy__astropy-6938"]["patch_successfully_applied"] = False
    obj["astropy__astropy-6938"]["tests_status"] = {
        "FAIL_TO_PASS": {"success": [], "failure": ["test_a", "test_b"]},
        "PASS_TO_PASS": {"success": [], "failure": []}}
    r = parse_harness_report(_write(tmp_path, obj), "astropy__astropy-6938")
    assert r["applied"] is False
    # apply 失败 → reward None(诚实·不混入梯度·同 local 路径口径）
    assert r["f2p_passed"] is None


def test_parse_report_missing_instance(tmp_path):
    r = parse_harness_report(_write(tmp_path, {}), "astropy__astropy-6938")
    assert r["parsed"] is False and r["f2p_passed"] is None


# ── eval timeout hardening (2026-06-21 · 防单题 hang 冻结整个 verify 队列 + 远端孤儿泄漏) ──

def test_default_eval_timeout_is_bounded():
    """默认超时应远小于旧 2400s(40min)·封顶 hang 冻结队列时长。"""
    assert DEFAULT_SWE_EVAL_TIMEOUT <= 1200


def test_eval_timeout_env_override(monkeypatch):
    monkeypatch.setenv("FDE_SWE_EVAL_TIMEOUT", "300")
    import services.swe_docker as sd
    importlib.reload(sd)
    try:
        assert sd.DEFAULT_SWE_EVAL_TIMEOUT == 300
    finally:
        monkeypatch.delenv("FDE_SWE_EVAL_TIMEOUT", raising=False)
        importlib.reload(sd)


def test_remote_cleanup_cmd_targets_container_and_proc():
    """超时清理命令须含:停该 instance+run 的容器 + 杀 run_evaluation 进程(治孤儿)。"""
    cmd = remote_cleanup_cmd("psf__requests-2317", "verify_b7e1ea0a")
    assert "sweb.eval.psf__requests-2317.verify_b7e1ea0a" in cmd
    assert "docker stop" in cmd or "docker rm" in cmd
    assert "psf__requests-2317" in cmd and "run_evaluation" in cmd
    # 必须 best-effort 不报错(2>/dev/null / true 兜底)
    assert "2>/dev/null" in cmd or "|| true" in cmd or "; true" in cmd
