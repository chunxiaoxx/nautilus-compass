#!/usr/bin/env python3
"""Path B effect 层(Docker 官方 harness 版·2026-06-19)。

本地 pytest 路(swe_runner）只能跑新版可装 instance(老题依赖 cgi/collections.Mapping·
Py3.13 装不上）。官方 SWE-bench harness 用 per-instance Docker 镜像(正确老 Python）→
解装环境地狱·解锁全 Lite 池。本模块薄封装:写 prediction → run_evaluation(Docker）→
解析 report.json 抽 FAIL_TO_PASS 逐项 → 离散 reward(= n_passed·复用 swe_verify 口径）。

self-given:用官方公共 Docker 镜像·不消费 compass cloud GPU(守单一 owner）。
纯解析 parse_harness_report 单测在 tests/test_swe_docker.py。Docker run 是 integration。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys


# GPU box(SWE swebench harness·非 T4·重 Docker 隔离·铁律不上 cloud 生产 box)
_SWE_GPU_HOST = os.environ.get("SWE_GPU_HOST", "ubuntu@43.166.8.20")
_SWE_GPU_PEM = os.environ.get("SWE_GPU_PEM", "/tmp/gpu.pem")
_SWE_REMOTE_PY = os.environ.get("SWE_REMOTE_PY", "/mnt/datadisk0/swe-rsi/venv/bin/python")
_SWE_REMOTE_SCRIPT = os.environ.get(
    "SWE_REMOTE_SCRIPT", "/mnt/datadisk0/swe-rsi/backend/scripts/swe_eval_one.py")
_SWE_REMOTE_WORKDIR = os.environ.get("SWE_REMOTE_WORKDIR", "/mnt/datadisk0/swe-rsi/harness")
_SWE_REMOTE_HF = os.environ.get("SWE_REMOTE_HF", "/mnt/datadisk0/swe-rsi/hf")

# A single hung instance eval used to freeze the whole fde-bench verify queue for the
# old 40min default (2026-06-21 · requests-2317 container test hung ~20min). Bound it
# (covers cold env builds ~≤20min, cached after first) · env-overridable.
DEFAULT_SWE_EVAL_TIMEOUT = int(os.environ.get("FDE_SWE_EVAL_TIMEOUT", "1200"))


def remote_cleanup_cmd(instance_id: str, run_id: str) -> str:
    """Shell cmd to clean up an orphaned remote eval after a timeout (best-effort).

    swebench launches a docker container `sweb.eval.<instance_id>.<run_id>` + a
    `run_evaluation` python proc on the GPU box. On a cloud-side timeout the local ssh
    is killed but those keep running (orphan leak · had to be docker-stopped by hand).
    This stops the container + kills the proc so the next verify cycle starts clean.
    All best-effort (2>/dev/null) — cleanup must never raise.
    """
    container = "sweb.eval.%s.%s" % (instance_id, run_id)
    return (
        "docker stop %s 2>/dev/null; docker rm -f %s 2>/dev/null; "
        "pkill -f 'run_evaluation.*%s' 2>/dev/null; true"
        % (container, container, instance_id)
    )


def remote_swe_eval(instance_id: str, patch: str, run_id: str = "verify",
                    timeout: int = DEFAULT_SWE_EVAL_TIMEOUT) -> dict:
    """cloud-side: scp patch → GPU box → swe_eval_one.py(swebench harness)→ report dict。

    镜像 fde_sdiagnose_run.gpu_eval_candidate 的 ssh 模式(SWE 版)。GPU box 跑重 Docker·
    cloud 只编排。ssh/scp/harness 任一失败 → {"parsed": False, "error": ...}(cloud verify
    侧判 ok=False·不写 verdict·retry)。
    """
    import tempfile
    ssh_base = ["ssh", "-i", _SWE_GPU_PEM, "-o", "ConnectTimeout=20",
                "-o", "StrictHostKeyChecking=no", _SWE_GPU_HOST]
    remote_patch = "/tmp/swe_patch_%s.diff" % run_id
    with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False, encoding="utf-8") as f:
        f.write(patch)
        local = f.name
    try:
        scp = subprocess.run(
            ["scp", "-i", _SWE_GPU_PEM, "-o", "ConnectTimeout=20",
             "-o", "StrictHostKeyChecking=no", local,
             "%s:%s" % (_SWE_GPU_HOST, remote_patch)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if scp.returncode != 0:
            return {"parsed": False, "error": "scp_fail: %s" % scp.stderr[-200:]}
        cmd = ("HF_HOME=%s %s %s %s --patch-file %s --run-id %s --workdir %s"
               % (_SWE_REMOTE_HF, _SWE_REMOTE_PY, _SWE_REMOTE_SCRIPT, instance_id,
                  remote_patch, run_id, _SWE_REMOTE_WORKDIR))
        r = subprocess.run(ssh_base + [cmd], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        # swe_eval_one 打印 "SWE_REPORT_JSON {...}"(末行)·抓出
        for line in reversed((r.stdout or "").splitlines()):
            if line.startswith("SWE_REPORT_JSON "):
                try:
                    return json.loads(line[len("SWE_REPORT_JSON "):])
                except json.JSONDecodeError as ex:
                    return {"parsed": False, "error": "json_decode: %s" % ex}
        return {"parsed": False, "error": "no report line (rc=%d %s)" % (
            r.returncode, (r.stderr or "")[-200:])}
    except subprocess.TimeoutExpired:
        # cloud-side timed out → the remote container + run_evaluation proc are orphaned.
        # Best-effort clean them so the next verify cycle (+ GPU box) starts clean.
        try:
            subprocess.run(ssh_base + [remote_cleanup_cmd(instance_id, run_id)],
                           capture_output=True, text=True, timeout=60)
        except Exception:  # noqa: BLE001 — cleanup is best-effort, never raise
            pass
        return {"parsed": False, "error": "swe_eval_timeout"}
    finally:
        try:
            os.unlink(local)
        except OSError:
            pass


def parse_harness_report(report_path: str, instance_id: str) -> dict:
    """官方 harness report.json → 离散结果。reward = len(FAIL_TO_PASS.success)。

    apply 失败 → f2p_passed=None(诚实·不混梯度·同 local swe_reward 口径）。
    """
    out = {"parsed": False, "f2p_total": 0, "f2p_passed": None, "f2p_fail_tests": [],
           "p2p_total": 0, "p2p_passed": 0, "applied": False, "resolved": False}
    try:
        with open(report_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:  # noqa: BLE001
        return out
    rec = data.get(instance_id)
    if not isinstance(rec, dict):
        return out
    out["parsed"] = True
    out["applied"] = bool(rec.get("patch_successfully_applied"))
    out["resolved"] = bool(rec.get("resolved"))
    ts = rec.get("tests_status", {})
    f2p = ts.get("FAIL_TO_PASS", {})
    p2p = ts.get("PASS_TO_PASS", {})
    f_succ = f2p.get("success", []) or []
    f_fail = f2p.get("failure", []) or []
    out["f2p_total"] = len(f_succ) + len(f_fail)
    out["f2p_fail_tests"] = list(f_fail)
    out["p2p_passed"] = len(p2p.get("success", []) or [])
    out["p2p_total"] = len(p2p.get("success", []) or []) + len(p2p.get("failure", []) or [])
    # apply 失败 → reward None(不混梯度）;否则 = 过的 F2P 数(离散）
    out["f2p_passed"] = len(f_succ) if out["applied"] else None
    return out


# ───────────────────────── Docker effect(integration）─────────────────────────

def write_predictions(path: str, instance_id: str, patch: str, model: str = "soul-rsi") -> str:
    """写官方 harness 要的 predictions JSONL(单条）。"""
    rec = {"instance_id": instance_id, "model_name_or_path": model, "model_patch": patch}
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return path


def run_evaluation(predictions_path: str, instance_id: str, run_id: str,
                   dataset: str = "princeton-nlp/SWE-bench_Lite",
                   timeout: int = 2400, cwd: str | None = None) -> tuple:
    """跑官方 harness(Docker·单 instance）。回 (returncode, stdout_tail)。

    🔴 cwd = harness 落 logs/ 的根·必须与 find_report 用同一 workdir(否则 report 找不到）。
    """
    # 🔴 --namespace none:强制本地构建·不从 swebench/ Docker Hub namespace 拉预构镜像
    # (2026-06-23 实证:多数 instance 的 swebench/sweb.eval.* 未发布 → 拉 404 → 报错不本地构建)。
    harness_args = ["--dataset_name", dataset, "--predictions_path", predictions_path,
                    "--max_workers", "1", "--run_id", run_id,
                    "--instance_ids", instance_id, "--cache_level", "env",
                    "--namespace", "none"]
    if sys.platform == "win32":
        # Windows: 经 launcher 注入 resource stub(harness 顶层 import Unix-only resource）
        # ⚠️ 已知 Windows 写 CRLF 文件破 Linux 容器内执行 → 真跑须在 Linux(cloud）。
        launcher = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "scripts", "_swe_harness_win.py")
        cmd = [sys.executable, launcher] + harness_args
    else:
        cmd = [sys.executable, "-m", "swebench.harness.run_evaluation"] + harness_args
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd or os.getcwd())
    return r.returncode, ((r.stdout or "")[-2000:] + "\n" + (r.stderr or "")[-1000:])


def find_report(run_id: str, instance_id: str, model: str = "soul-rsi",
                cwd: str | None = None) -> str | None:
    """定位 report.json。harness 落 logs/run_evaluation/<run_id>/<model>/<instance>/report.json。"""
    base = os.path.join(cwd or os.getcwd(), "logs", "run_evaluation", run_id, model, instance_id)
    rp = os.path.join(base, "report.json")
    if os.path.exists(rp):
        return rp
    # fallback:扫 run_id 目录
    root = os.path.join(cwd or os.getcwd(), "logs", "run_evaluation", run_id)
    for dirpath, _dirs, files in os.walk(root):
        if "report.json" in files and instance_id in dirpath:
            return os.path.join(dirpath, "report.json")
    return None


def read_test_output(run_id: str, instance_id: str, model: str = "soul-rsi",
                     cwd: str | None = None, max_chars: int = 6000) -> str:
    """读该 instance 的 test_output.txt(harness 落的真实测试输出·喂 turn-2 记忆 traceback）。"""
    base = os.path.join(cwd or os.getcwd(), "logs", "run_evaluation", run_id, model, instance_id)
    for name in ("test_output.txt", "test_output.log"):
        p = os.path.join(base, name)
        if os.path.exists(p):
            with open(p, encoding="utf-8", errors="replace") as f:
                t = f.read()
            return t[-max_chars:]
    return ""


def run_candidate_docker(instance_id: str, patch: str, run_id: str,
                         dataset: str = "princeton-nlp/SWE-bench_Lite",
                         model: str = "soul-rsi", workdir: str | None = None,
                         timeout: int = 2400) -> dict:
    """完整 effect:写 prediction → run_evaluation(Docker）→ parse report + 读 test output。

    回 {report:dict(parse_harness_report）, test_output:str, rc:int, stdout_tail:str}。
    workdir = harness cwd(logs 落这里）·默认临时。patch 为空/未应用 → report.applied=False。
    """
    wd = workdir or os.getcwd()
    os.makedirs(wd, exist_ok=True)
    pred = os.path.join(wd, "preds_%s.jsonl" % run_id)
    write_predictions(pred, instance_id, patch, model)
    rc, tail = run_evaluation(pred, instance_id, run_id, dataset, timeout, cwd=wd)
    rep_path = find_report(run_id, instance_id, model, cwd=wd)
    report = parse_harness_report(rep_path, instance_id) if rep_path else {
        "parsed": False, "f2p_passed": None, "f2p_total": 0, "f2p_fail_tests": [],
        "applied": False, "resolved": False, "p2p_passed": 0, "p2p_total": 0}
    test_out = read_test_output(run_id, instance_id, model, cwd=wd)
    return {"report": report, "test_output": test_out, "rc": rc, "stdout_tail": tail,
            "report_path": rep_path}
