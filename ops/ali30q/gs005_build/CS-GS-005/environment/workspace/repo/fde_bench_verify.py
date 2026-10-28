#!/usr/bin/env python3
"""
fde_bench_verify.py — 第三类经验题统一确定性 verifier 适配器(给 platform settle 路径调用)。

所有 compass 第三类经验题(c2/c2b/c2c/c3/c2d/f1/…)的 bench_eval.py 共享同一接口:
    PYTHONUTF8=1 python <bench_eval.py> <candidate_solution.py>
    → stdout 一段 JSON {passed: bool, n_pass, n_total, reason, cases:[...]}
本适配器把它包成 platform 要的「task + produced output → reward」契约,屏蔽各题差异。

用法:
    python fde_bench_verify.py --bench <bench_eval.py> --produced <produced_solution.py>
    （produced_solution.py = consumer/agent 产出的修复后代码文件）

输出(stdout·单行 JSON·platform 写 verdict-bus 用):
    {"reward": 1.0|0.0, "passed": bool, "n_pass": int, "n_total": int,
     "reason": str, "source": "compass/bench_eval", "bench": "<path>", "ok": bool}
  - reward = 1.0 当且仅当 bench_eval 判 passed=True(全部 G 门通过),否则 0.0。
  - ok=False 表示 verifier 自身执行失败(bench 缺失/超时/非法 JSON)→ 不可当 reward 0 误判,
    platform 应重试或人工查(区别于「跑通但没过」的 reward 0)。
确定性:reward 只由 bench_eval 的 G 门决定;ground truth 由 bench_eval 现场用输入算,记答案无用。
"""
import sys
import os
import json
import argparse
import subprocess

# 外层 verify timeout(秒)。env 可覆盖。默认 720s 以容纳 verifier_inline 内部自 ssh→T4
# 跑 KernelBench kb_eval(内层各步 40+60+540+40≈680s 预算·见 bench_eval_kernelbench.py)。
# 纯 CPU 确定性 verifier(c2/c3 等)远低于此·抬高对它们无害。
_DEFAULT_TIMEOUT = float(os.environ.get("FDE_BENCH_VERIFY_TIMEOUT", "720"))


def verify(bench_path: str, produced_path: str, timeout: float = _DEFAULT_TIMEOUT) -> dict:
    if not os.path.exists(bench_path):
        return {"reward": 0.0, "passed": False, "ok": False,
                "reason": f"bench_eval not found: {bench_path}", "source": "compass/bench_eval"}
    if not os.path.exists(produced_path):
        return {"reward": 0.0, "passed": False, "ok": False,
                "reason": f"produced solution not found: {produced_path}", "source": "compass/bench_eval"}
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    try:
        p = subprocess.run([sys.executable, bench_path, produced_path],
                           capture_output=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return {"reward": 0.0, "passed": False, "ok": False,
                "reason": f"bench_eval timeout > {timeout}s", "source": "compass/bench_eval"}
    out = p.stdout.decode("utf-8", "replace").strip()
    # bench_eval 把 JSON 打到 stdout（可能多行 indent=1）；取最后一个 JSON 对象
    try:
        start = out.index("{")
        res = json.loads(out[start:])
    except (ValueError, json.JSONDecodeError) as e:
        return {"reward": 0.0, "passed": False, "ok": False,
                "reason": f"bench_eval output not JSON: {e}; stdout_tail={out[-200:]}",
                "source": "compass/bench_eval"}
    passed = bool(res.get("passed"))
    return {"reward": 1.0 if passed else 0.0, "passed": passed, "ok": True,
            "n_pass": res.get("n_pass"), "n_total": res.get("n_total"),
            "reason": res.get("reason", ""), "bench": bench_path,
            "source": "compass/bench_eval"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True, help="path to the task's bench_eval.py (feishu 附件)")
    ap.add_argument("--produced", required=True, help="path to consumer-produced solution .py")
    ap.add_argument("--timeout", type=float, default=_DEFAULT_TIMEOUT)
    a = ap.parse_args()
    print(json.dumps(verify(a.bench, a.produced, a.timeout), ensure_ascii=False))


if __name__ == "__main__":
    main()
