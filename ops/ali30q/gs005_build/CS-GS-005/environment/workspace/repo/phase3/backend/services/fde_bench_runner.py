"""第3类确定性 verify · effect runner(把 fde_bench_poll 纯核心接到真 effect).

Wires the pure orchestration core (services.fde_bench_poll) to REAL effects:

    source     = HTTP GET  {base}/api/platform/fde/tasks?status=produced  (仅第3类·未判)
    verify_fn  = 从 task 取 verifier_inline + produced output → 临时文件 → 跑
                 fde_bench_verify.py(compass 确定性 bench_eval)→ reward
    verdict_fn = HTTP POST {base}/api/platform/fde/verdict   (source='compass/bench_eval')

EFFECT code(HTTP + 子进程)——不单测; 纯核心在 tests/test_fde_bench_poll.py 证.
纯 helper(产出代码抽取/verifier 取出)在 tests/test_fde_bench_runner_helpers.py 证.

Run:
    python -m services.fde_bench_runner --base http://localhost:8000 --dry-run
    python -m services.fde_bench_runner --base http://localhost:8000   # writes verdicts
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import urllib.request
from typing import Callable

from services.fde_bench_poll import poll_and_verify, is_t3_bench_task, parse_t3_spec

# fde_bench_verify.py 在 repo 根(compass 交付的统一适配器). 可由 env 覆盖(云上 vendored).
_DEFAULT_BENCH_VERIFY = r"C:\Users\chunx\Projects\nautilus-core\fde_bench_verify.py"

# CPU-route verify timeout(秒). verifier_inline 自 ssh→T4 跑 KernelBench 的任务内层预算
# ≈680s(见 fde_bench_verify._DEFAULT_TIMEOUT 注释)·故默认 720·env 可覆盖. 纯 CPU 题远低于此.
_VERIFY_TIMEOUT = float(os.environ.get("FDE_BENCH_VERIFY_TIMEOUT", "720"))


def _load_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def strip_code_fence(s: str) -> str:
    """去掉 markdown ```python … ``` 围栏, 返回纯代码(模型产出常带围栏)."""
    if "```" not in s:
        return s.strip()
    start = s.find("```")
    # skip the opening fence line (```python / ```py / ```)
    nl = s.find("\n", start)
    if nl == -1:
        return s.strip()
    end = s.find("```", nl)
    body = s[nl + 1:end] if end != -1 else s[nl + 1:]
    return body.strip()


def extract_solution_code(output) -> str:
    """从 produced output(dict 或 str)抽出产出的 .py 源码."""
    if isinstance(output, dict):
        code = output.get("code") or output.get("solution") or output.get("text") or ""
    else:
        code = str(output or "")
    return strip_code_fence(code)


def verifier_source(task: dict) -> str | None:
    """从 task description 的第3类 spec 取内联的 bench_eval.py 源码."""
    spec = parse_t3_spec(task) or {}
    return spec.get("verifier_inline") or spec.get("bench_eval_inline")


def is_kernelbench_task(task: dict) -> bool:
    """KernelBench 燃料(走 GPU verify 经路)= 第3类 bench 任务且 desc 带 kb_problem_id。

    其余第3类(CPU 确定性·verifier_inline 本机跑)走 make_verify_fn。
    """
    if not is_t3_bench_task(task):
        return False
    spec = parse_t3_spec(task) or {}
    return spec.get("kb_problem_id") is not None


def is_swe_task(task: dict) -> bool:
    """SWE 燃料(走 swebench harness verify·非 KernelBench kb_eval·非 CPU verifier_inline)。

    = 第3类 bench 任务且 desc 带 swe_instance_id(P1.3b·2026-06-20)。
    """
    if not is_t3_bench_task(task):
        return False
    spec = parse_t3_spec(task) or {}
    return bool(spec.get("swe_instance_id"))


def extract_swe_patch(output) -> str:
    """从 produced output 抽 git unified diff(swebench model_patch)。

    🔴 contract(2026-06-20):SWE produce 必须给 **unified diff**(output.patch/diff·或
    text/code 本身是 diff)。V5 当前的 annotated code block(``# ... existing code ...``)
    **非 diff** → 返 ""(清晰信号·不拿去 swebench garbage-apply 误判 genuine fail)。
    """
    if isinstance(output, dict):
        for k in ("patch", "diff"):
            v = output.get(k)
            if v and str(v).strip():
                return strip_code_fence(str(v))
        cand = strip_code_fence(str(output.get("text") or output.get("code") or ""))
    else:
        cand = strip_code_fence(str(output or ""))
    return cand if ("diff --git" in cand or cand.lstrip().startswith(("--- ", "diff "))) else ""


def coerce_swe_patch_from_full_file(output, spec: dict) -> str:
    """Fallback(C·6/21):produce 是整文件(非 diff)→ 用内嵌原文 coerce 成 git unified diff。

    防 producer 格式不一致——kairos/v7(非 SWE-aware 路径)抢到 SWE 燃料会产**整文件 +
    `{"code":"v5-daemon-fde-produce"}` wrapper**(非 unified diff)→ extract_swe_patch 返 ""
    → verify errored 永卡。本兜底用 mint 内嵌原文(spec.original_files)与产出整文件做 diff,
    使 verify 对 producer 格式鲁棒(谁产都能验·正确性仍由 swebench 判·错 fix→reward 0)。

    仅当**单一 edit_path** 且有该原文时 coerce(多 edit_path 无法把整文件对应到具体文件 →
    保守返 ""·让 verify 走"need unified diff"诚信失败)。无变化/缺原文/空产出 → ""。
    """
    import difflib
    orig_files = spec.get("original_files") or {}
    edit_paths = spec.get("edit_paths") or []
    if len(edit_paths) != 1 or not isinstance(orig_files, dict) or not orig_files:
        return ""
    path = edit_paths[0]
    original = orig_files.get(path)
    if not isinstance(original, str) or not original:
        return ""
    # 🔴 text 优先:kairos 格式 code="v5-daemon-fde-produce"(marker)·真文件在 text。
    # extract_solution_code 优先 code 会拿到 marker → 这里单独取 text 优先。
    if isinstance(output, dict):
        raw = output.get("text") or output.get("solution") or output.get("code") or ""
    else:
        raw = str(output or "")
    produced = strip_code_fence(str(raw))
    if not produced.strip():
        return ""
    # 剥 producer 常加的 "# <path>" 文件头注释(原文无·否则污染 diff)
    lines = produced.split("\n")
    if lines and lines[0].lstrip().startswith("#"):
        head = lines[0].lstrip("#").strip()
        base = path.rsplit("/", 1)[-1]
        if head == path or head.endswith(base):
            lines = lines[1:]
    produced = "\n".join(lines)
    if produced.strip() == original.strip():
        return ""  # 无变化 = 非修复
    a = original.splitlines(keepends=True)
    b = produced.splitlines(keepends=True)
    if a and not a[-1].endswith("\n"):
        a[-1] += "\n"
    if b and not b[-1].endswith("\n"):
        b[-1] += "\n"
    body = "".join(difflib.unified_diff(a, b, fromfile="a/%s" % path, tofile="b/%s" % path))
    if not body.strip():
        return ""
    return "diff --git a/%s b/%s\n%s" % (path, path, body)


def swe_verdict_from_report(report: dict | None, sol_hash: str) -> dict:
    """swebench harness report → verify_fn 契约(三态诚实)。

    parsed=False / error(harness 超时/崩/ssh 失败)→ ok=False(不写 verdict·retry·非真 fail)。
    parsed=True:applied=False(patch 没 apply=坏 patch)= genuine fail(reward 0)·
    否则 reward=f2p_passed/f2p_total(梯度)·overall_pass=resolved(全 F2P+P2P 过才算 full)。
    """
    base = {"sol_hash": sol_hash, "source": "compass/bench_eval"}
    if not report or report.get("error") or not report.get("parsed"):
        return {**base, "ok": False, "passed": False, "reward": 0.0,
                "reason": "swe harness no report (%s)" % (
                    (report or {}).get("error") or "not parsed")}
    f2p_total = int(report.get("f2p_total") or 0)
    f2p_passed = report.get("f2p_passed")
    if not report.get("applied") or f2p_passed is None:
        return {**base, "ok": True, "passed": False, "reward": 0.0,
                "n_pass": 0, "n_total": f2p_total, "reason": "patch not applied"}
    f2p_passed = int(f2p_passed)
    passed = bool(report.get("resolved"))
    score = (f2p_passed / f2p_total) if f2p_total else (1.0 if passed else 0.0)
    return {**base, "ok": True, "passed": passed, "reward": round(score, 4),
            "n_pass": f2p_passed, "n_total": f2p_total,
            "reason": "resolved" if passed else "partial %d/%d" % (f2p_passed, f2p_total)}


def make_swe_verify_fn() -> Callable[[dict], dict]:
    """gate/verify: SWE produced patch → ssh GPU box swebench harness → verdict 契约。

    复用 services.swe_docker.remote_swe_eval(scp patch→GPU box run_candidate_docker→report)。
    desc 取 swe_instance_id;task['output'] 取 V5 produce 的 patch(unified diff)。
    """
    from services.swe_docker import remote_swe_eval

    def verify_fn(task: dict) -> dict:
        spec = parse_t3_spec(task) or {}
        inst = spec.get("swe_instance_id")
        patch = extract_swe_patch(task.get("output"))  # 优先:producer 直给真 unified diff
        if not patch.strip():
            # C 兜底:producer 产整文件(非 diff·如 kairos/v7)→ 用内嵌原文 coerce 成 diff
            patch = coerce_swe_patch_from_full_file(task.get("output"), spec)
        sol_hash = hashlib.sha256((patch or "").encode("utf-8")).hexdigest()[:8] if patch else "default"
        if not inst or not patch.strip():
            return {"ok": False, "passed": False, "reward": 0.0, "sol_hash": sol_hash,
                    "reason": "missing swe_instance_id or non-diff patch (need unified diff)",
                    "source": "compass/bench_eval"}
        report = remote_swe_eval(inst, patch, run_id="verify_%s" % sol_hash)
        return swe_verdict_from_report(report, sol_hash)

    return verify_fn


def fast1_verdict_from_kb_eval(kb: dict | None, sol_hash: str, fast1: bool = True) -> dict:
    """kb_eval 结果 → verify_fn 契约(fast1 门·soul 6/17 裁定)。

    fast1=True : passed = pass_final AND speedup>1(窗口 1<su≤2·>2× 已被 G2 排除)。
    fast1=False: passed = pass_final(correctness-only 旧口径)。
    GPU eval 自身崩(error)→ ok=False(verifier 失败·poller 不写 verdict·重试)。
    """
    base = {"sol_hash": sol_hash, "source": "compass/bench_eval"}
    if not kb or kb.get("error"):
        return {**base, "ok": False, "passed": False, "reward": 0.0,
                "reason": "gpu_eval failed: %s" % (kb.get("error") if kb else "empty")}
    correct = kb.get("pass_final") is True
    su = kb.get("speedup_vs_eager")
    if fast1:
        passed = bool(correct and isinstance(su, (int, float)) and su > 1.0)
        if passed:
            reason = kb.get("reason", "pass") + " (fast1 speedup=%.3f)" % su
        elif correct:
            reason = "correct_but_slow(speedup=%s ≤1·fast1门未过)" % su
        else:
            reason = kb.get("reason", "incorrect")
    else:
        passed = correct
        reason = kb.get("reason", "")
    return {**base, "ok": True, "passed": passed, "reward": 1.0 if passed else 0.0,
            "reason": reason, "speedup": su}


def make_gpu_verify_fn(level_default: int = 2, fast1: bool = True) -> Callable[[dict], dict]:
    """gate B: KernelBench produced kernel → scp T4 → kb_eval.sh → fast1 verdict。

    复用 fde_sdiagnose_run.gpu_eval_candidate(scp→T4 kb_eval.sh flock→解析 JSON)。
    desc 取 kb_level/kb_problem_id/fast1;task['output'] 取 V5 产出 kernel 源。
    """
    from services.fde_sdiagnose_run import gpu_eval_candidate

    def verify_fn(task: dict) -> dict:
        spec = parse_t3_spec(task) or {}
        sol = extract_solution_code(task.get("output"))
        sol_hash = hashlib.sha256(sol.encode("utf-8")).hexdigest()[:8] if sol else "default"
        if not sol.strip():
            return {"ok": False, "passed": False, "reward": 0.0, "sol_hash": sol_hash,
                    "reason": "produced output has no solution code", "source": "compass/bench_eval"}
        level = int(spec.get("kb_level", level_default))
        pid = int(spec["kb_problem_id"])
        use_fast1 = bool(spec.get("fast1", fast1))
        kb = gpu_eval_candidate(sol, 0, level, pid)
        return fast1_verdict_from_kb_eval(kb, sol_hash, fast1=use_fast1)

    return verify_fn


def make_dispatch_verify_fn(bench_verify_path: str = None, timeout: float = _VERIFY_TIMEOUT) -> Callable[[dict], dict]:
    """路由 verify_fn:SWE → swebench harness(GPU box ssh)· KernelBench → GPU kb_eval ·
    其余第3类 → CPU(verifier_inline)。三路惰性建。"""
    gpu_fn = None   # KernelBench(import fde_sdiagnose_run)
    swe_fn = None   # SWE(import swe_docker)
    cpu_fn = make_verify_fn(bench_verify_path, timeout)

    def verify_fn(task: dict) -> dict:
        nonlocal gpu_fn, swe_fn
        if is_swe_task(task):
            if swe_fn is None:
                swe_fn = make_swe_verify_fn()
            return swe_fn(task)
        if is_kernelbench_task(task):
            if gpu_fn is None:
                gpu_fn = make_gpu_verify_fn()
            return gpu_fn(task)
        return cpu_fn(task)

    return verify_fn


def make_verify_fn(bench_verify_path: str = None, timeout: float = _VERIFY_TIMEOUT) -> Callable[[dict], dict]:
    """真 verify_fn: 内联 verifier + 产出代码 → 临时文件 → fde_bench_verify → reward.

    返回 dict 含 ``sol_hash``(产出代码 sha256[:8]·verdict_id per-version 键). 缺
    verifier/产出 → ``ok=False``(verifier 自身失败·poller 不写 verdict·可重试).
    """
    bv = _load_module(bench_verify_path or os.environ.get("FDE_BENCH_VERIFY", _DEFAULT_BENCH_VERIFY),
                      "fde_bench_verify")

    def verify_fn(task: dict) -> dict:
        src = verifier_source(task)
        if not src:
            return {"ok": False, "passed": False, "reward": 0.0,
                    "reason": "task spec has no verifier_inline", "source": "compass/bench_eval"}
        sol = extract_solution_code(task.get("output"))
        if not sol.strip():
            return {"ok": False, "passed": False, "reward": 0.0,
                    "reason": "produced output has no solution code", "source": "compass/bench_eval"}
        tmpdir = tempfile.mkdtemp(prefix="fde_bench_")
        bench_path = os.path.join(tmpdir, "bench_eval.py")
        sol_path = os.path.join(tmpdir, "produced_solution.py")
        with open(bench_path, "w", encoding="utf-8") as fh:
            fh.write(src)
        with open(sol_path, "w", encoding="utf-8") as fh:
            fh.write(sol)
        res = bv.verify(bench_path, sol_path, timeout)
        res["sol_hash"] = hashlib.sha256(sol.encode("utf-8")).hexdigest()[:8]
        return res

    return verify_fn


def make_http_source(base: str):
    class _Src:
        def list_produced_tasks(self):
            url = f"{base.rstrip('/')}/api/platform/fde/tasks?status=produced"
            with urllib.request.urlopen(url, timeout=30) as r:
                body = json.loads(r.read().decode())
            tasks = body.get("data", {}).get("tasks", [])
            # 只取第3类且未判(有 verdict 的 settled 不重判·与 scorer_runner 同).
            return [t for t in tasks if t.get("verdict") is None and is_t3_bench_task(t)]
    return _Src()


def make_http_capability_fn(base: str):
    """verify-side 能力回写(HTTP)· poller 安全(纯 derive·无 models/utils 依赖)。

    derive_capability(纯·fde_capability_logic)从 (task, result) 推归因记录 → POST
    /api/platform/fde/capability(服务端 upsert). fail-soft: 写崩绝不影响 verify 主链。
    """
    from services.fde_capability_logic import derive_capability
    url = f"{base.rstrip('/')}/api/platform/fde/capability"

    def capability_fn(task: dict, result: dict) -> None:
        try:
            d = derive_capability(task, result)
            if d is None:
                return
            data = json.dumps(d).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15):
                pass
        except Exception:  # noqa: BLE001 — 能力写绝不影响 verify/verdict 主链
            pass

    return capability_fn


def make_http_verdict_fn(base: str, dry_run: bool = False):
    url = f"{base.rstrip('/')}/api/platform/fde/verdict"

    def verdict_fn(body: dict):
        if dry_run:
            print(f"[dry-run] would POST verdict {body['verdict_id']} "
                  f"pass={body['overall_pass']} score={body['score']}")
            return {"dry_run": True}
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode()).get("data")

    return verdict_fn


def main(argv=None):
    ap = argparse.ArgumentParser(description="第3类确定性 verify poller (produced → bench reward → verdict)")
    ap.add_argument("--base", default=os.environ.get("FDE_BASE", "http://localhost:8000"))
    ap.add_argument("--dry-run", action="store_true", help="verify but do not POST verdicts")
    ap.add_argument("--no-capability", action="store_true",
                    help="不回写 producer 能力台账(platform_agent_capability_stats)")
    a = ap.parse_args(argv)

    source = make_http_source(a.base)
    verify_fn = make_dispatch_verify_fn()  # KernelBench→GPU(gate B)· 其余→CPU
    verdict_fn = make_http_verdict_fn(a.base, dry_run=a.dry_run)

    # verify-side 能力回写(单写点·producer claimed_by 的格式合规/质量分 → V5 路由读端).
    # 走 HTTP(poller vendored 无 models/utils·不能进程内 DB). dry-run/--no-capability 关闭.
    capability_fn = None
    if not a.dry_run and not a.no_capability:
        capability_fn = make_http_capability_fn(a.base)

    result = poll_and_verify(source, verify_fn, verdict_fn, capability_fn=capability_fn)
    print(f"[bench-verify] base={a.base} dry_run={a.dry_run} capability={capability_fn is not None} → "
          f"verified={result['verified']} skipped={result['skipped']} "
          f"errored={result['errored']} failed={result['failed']}")
    return 0 if not result["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
