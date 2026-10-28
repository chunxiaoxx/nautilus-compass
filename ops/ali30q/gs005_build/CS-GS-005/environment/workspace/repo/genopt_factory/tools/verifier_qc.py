"""verifier 三铁律黑盒 QC 脚本(给 soul 用 · buyer §5.2 valid gate 防违规)。

3 关:
  (a) 确定性 — 同输入两跑 → tour/starts 必须完全一致
  (b) 只读 — candidate 不得写 verification/ / data/ / frontier_eval/ 之外(允许写临时目录)
  (c) 60s/120s 单实例硬超时 — 任何实例超时 = combined_score=0

跑法:
    python verifier_qc.py --task-dir genopt_factory/tasks/.../jobshop_orlib_v1_001

输出:
    JSON 三关 PASS/FAIL + 违规 traceback(若有)
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile


def _run_determinism_check(task_dir, candidate, python_exe):
    """Same input two runs -> candidate output must match exactly."""
    sample_path = os.path.join(task_dir, "data", "instances")
    if not os.path.isdir(sample_path):
        return {"check": "determinism", "pass": False,
                "reason": f"no data/instances dir at {sample_path}"}
    instances = sorted([f for f in os.listdir(sample_path) if f.endswith(".json")])
    if not instances:
        return {"check": "determinism", "pass": False,
                "reason": "no instance JSON files"}
    # Use smallest instance to keep it fast
    sample = os.path.join(sample_path, instances[0])
    a = tempfile.mkdtemp(prefix="qc_a_")
    b = tempfile.mkdtemp(prefix="qc_b_")
    sa = os.path.join(a, "out.json")
    sb = os.path.join(b, "out.json")
    # We capture stdout/stderr from a tiny driver that imports candidate and
    # prints json of the result. Two runs must produce identical JSON.
    driver = (
        "import sys, json, importlib.util, os;\n"
        "sys.path.insert(0, os.path.dirname(r'{candidate}'));\n"
        "spec = importlib.util.spec_from_file_location('cand', r'{candidate}');\n"
        "mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod);\n"
        "inst = json.load(open(r'{sample}', encoding='utf-8'));\n"
        "print(json.dumps(mod.solve_instance(inst), sort_keys=True));\n"
    ).format(candidate=candidate.replace("\\", "\\\\"), sample=sample.replace("\\", "\\\\"))
    drv_path = os.path.join(tempfile.gettempdir(), "qc_driver.py")
    with open(drv_path, "w", encoding="utf-8") as f:
        f.write(driver)
    out_a = subprocess.run([python_exe, drv_path], capture_output=True, text=True, timeout=120)
    out_b = subprocess.run([python_exe, drv_path], capture_output=True, text=True, timeout=120)
    if out_a.returncode != 0 or out_b.returncode != 0:
        return {"check": "determinism", "pass": False,
                "reason": f"driver exit A={out_a.returncode} B={out_b.returncode}",
                "stderr_a": out_a.stderr[-500:],
                "stderr_b": out_b.stderr[-500:]}
    h_a = hashlib.sha256(out_a.stdout.encode()).hexdigest()
    h_b = hashlib.sha256(out_b.stdout.encode()).hexdigest()
    return {"check": "determinism", "pass": h_a == h_b,
            "sha_a": h_a, "sha_b": h_b}


def _run_readonly_check(task_dir, candidate):
    """Parse candidate source for forbidden I/O patterns:
       - any open(..., 'w') outside tempfile
       - any os.remove / shutil.rmtree on verification/, data/, frontier_eval/
       - any import of verification / data subpackages
       (Static check; not bullet-proof but catches common violations.)
    """
    with open(candidate, encoding="utf-8") as f:
        src = f.read()
    violations = []
    forbidden_writes = ["verification", "data", "frontier_eval"]
    # crude regex sweep
    import re
    for line_no, line in enumerate(src.splitlines(), 1):
        low = line.lower()
        if re.search(r"open\([^)]*['\"](w|a|x)\b", line):
            for kw in forbidden_writes:
                if kw in low:
                    violations.append({"line": line_no, "kind": "open_write_forbidden",
                                       "text": line.strip()})
        if re.search(r"(os\.remove|shutil\.rmtree|os\.unlink)", line):
            for kw in forbidden_writes:
                if kw in low:
                    violations.append({"line": line_no, "kind": "delete_forbidden",
                                       "text": line.strip()})
        if "import verification" in low or "from verification" in low:
            violations.append({"line": line_no, "kind": "import_verification",
                               "text": line.strip()})
        if "import data" in low or "from data" in low:
            violations.append({"line": line_no, "kind": "import_data",
                               "text": line.strip()})
        if "import frontier_eval" in low or "from frontier_eval" in low:
            violations.append({"line": line_no, "kind": "import_frontier_eval",
                               "text": line.strip()})
    return {"check": "readonly", "pass": len(violations) == 0, "violations": violations}


def _run_timeout_check(task_dir, candidate, python_exe, default_timeout):
    """Run the task's own verifier with a tighter timeout to surface hangs.
       Reuses task's evaluate.py; any single instance timeout => fail.
    """
    eval_py = os.path.join(task_dir, "verification", "evaluate.py")
    if not os.path.isfile(eval_py):
        return {"check": "timeout", "pass": False,
                "reason": f"missing {eval_py}"}
    # Hard outer kill = max(2 * per_instance_timeout, default)
    outer = max(2 * default_timeout, default_timeout + 30)
    try:
        out = subprocess.run(
            [python_exe, eval_py, "--benchmark-dir", task_dir, "--candidate", candidate],
            capture_output=True, text=True, timeout=outer, cwd=tempfile.gettempdir(),
        )
    except subprocess.TimeoutExpired:
        return {"check": "timeout", "pass": False,
                "reason": f"verifier hard-killed at {outer}s (implies hang)"}
    metrics_path = os.path.join(tempfile.gettempdir(), "metrics.json")
    if not os.path.exists(metrics_path):
        # Fallback: evaluate.py writes to CWD when called with cwd=tempdir.
        return {"check": "timeout", "pass": False,
                "reason": "verifier ran but did not produce metrics.json",
                "stderr_tail": out.stderr[-500:]}
    with open(metrics_path, encoding="utf-8") as f:
        m = json.load(f)
    per_instance = m.get("per_instance", [])
    timeout_hits = [p["instance"] for p in per_instance
                    if (not p.get("feasible")) and "timeout" in (p.get("reason") or "").lower()]
    valid = m.get("valid", 0)
    return {"check": "timeout", "pass": (valid == 1 and not timeout_hits),
            "timeout_instances": timeout_hits, "combined_score": m.get("combined_score"),
            "valid": valid}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-dir", required=True)
    ap.add_argument("--candidate", default=None,
                    help="default: <task_dir>/baseline/init.py")
    ap.add_argument("--per-instance-timeout", type=int, default=120,
                    help="buyer's per-instance hard limit (s)")
    args = ap.parse_args()

    task_dir = os.path.abspath(args.task_dir)
    candidate = args.candidate or os.path.join(task_dir, "baseline", "init.py")
    if not os.path.isfile(candidate):
        print(json.dumps({"qc": "fail", "reason": f"candidate missing: {candidate}"},
                         indent=1))
        sys.exit(1)
    python_exe = sys.executable

    results = []
    results.append(_run_determinism_check(task_dir, candidate, python_exe))
    results.append(_run_readonly_check(task_dir, candidate))
    results.append(_run_timeout_check(task_dir, candidate, python_exe,
                                     args.per_instance_timeout))

    overall = all(r["pass"] for r in results)
    summary = {"task_dir": task_dir, "candidate": candidate,
               "qc_overall_pass": overall, "checks": results}
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    sys.exit(0 if overall else 2)


if __name__ == "__main__":
    main()