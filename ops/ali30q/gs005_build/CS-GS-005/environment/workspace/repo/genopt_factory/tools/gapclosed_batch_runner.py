"""Batch GPT5.5 N=3 calibration runner.

Reads a list of task dirs, fires one H800 worker per task (or sequentially on
this machine if --h800-host omitted). Each worker produces a gpt55_trajectory.json.

Usage:
    python gapclosed_batch_runner.py --task-list tasks.json --workers 3 \\
        --h800-host root@connect.westc.seetacloud.com --h800-port 34467 \\
        --ssh-key ~/.ssh/h800_ed25519 --out-dir trajectories/

    python gapclosed_batch_runner.py --task-list tasks.json --workers 1  # local-only

tasks.json schema:
    [
      {"task_dir": "genopt_factory/tasks/OR/TSP/tsp_tsplib_v2_001",
       "n": 3, "effort": "xhigh", "timeout": 900},
      ...
    ]

Output:
    {out_dir}/{task_basename}.gpt55_trajectory.json  (one per task)
    {out_dir}/batch_summary.json                     (gap_closed + difficulty per task)
"""

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def _run_local(task_dir, n, effort, timeout, env_extras):
    cmd = [sys.executable, "genopt_factory/tools/gapclosed_runner.py",
           "--task-dir", task_dir, "--n", str(n),
           "--effort", effort, "--timeout", str(timeout),
           "--out", os.path.join(task_dir, "gpt55_trajectory.json")]
    env = os.environ.copy()
    env.update(env_extras)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * (n + 1) + 600, env=env)


def _run_h800(task_dir, n, effort, timeout, h800, port, key, env_extras):
    """Copy task to H800 then invoke the local harness there (uses H800 OPENAI_BASE_URL)."""
    base = os.path.basename(task_dir.rstrip("/"))
    remote_root = "/root/autodl-tmp/genopt"
    remote_factory = f"{remote_root}/factory"
    rel = os.path.relpath(task_dir, "genopt_factory/tasks")
    remote_task_dir = f"{remote_factory}/tasks/{rel}"

    ssh = ["ssh", "-i", key, "-p", str(port), "-o", "StrictHostKeyChecking=no",
           "-o", "UserKnownHostsFile=/dev/null", "-o", f"ConnectTimeout={15}",
           h800]

    # mkdir + scp task dir
    parts = rel.split("/")
    mk_remote = " && ".join([f"mkdir -p {remote_factory}/tasks/{'/'.join(parts[:i+1])}"
                             for i in range(len(parts))])
    subprocess.run(ssh + [mk_remote], capture_output=True, timeout=30)

    scp = ["scp", "-i", key, "-P", str(port), "-o", "StrictHostKeyChecking=no",
           "-o", "UserKnownHostsFile=/dev/null", "-r",
           task_dir, f"{h800}:{os.path.dirname(remote_task_dir)}/"]
    r = subprocess.run(scp, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        return r

    env_assigns = " && ".join([f"export {k}={v}" for k, v in env_extras.items()])
    remote_cmd = (
        f"{env_assigns} && "
        f"cd {remote_root} && python -u harness/genopt_orlib_run.py "
        f"--task-dir {remote_task_dir} --n {n} --effort {effort} --timeout {timeout} "
        f"--out {remote_task_dir}/gpt55_trajectory_h800.json"
    )
    r = subprocess.run(ssh + [remote_cmd], capture_output=True, text=True,
                       timeout=timeout * (n + 1) + 600)
    return r


def _grade_from_traj(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        t = json.load(f)
    start = (t.get("start_score")
             if t.get("start_score") is not None else t.get("seed_score"))
    best = (t.get("best_score")
            if t.get("best_score") is not None else t.get("seed_score"))
    gap = t.get("gap_closed")
    diff = t.get("difficulty") or t.get("difficulty_bucket")
    if gap is None and start is not None and best is not None:
        gap = round((best - start) / 100.0, 4)
    if diff is None and gap is not None:
        if gap >= 0.6: diff = "Easy" if (best or 0) < 95 else "Rejected(too_easy)"
        elif gap >= 0.3: diff = "Medium"
        elif gap >= 0.1: diff = "Hard"
        else: diff = "Rejected"
    return {"start": start, "best": best, "gap_closed": gap, "difficulty": diff}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-list", required=True)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--h800-host", default=None)
    ap.add_argument("--h800-port", type=int, default=34467)
    ap.add_argument("--ssh-key", default="~/.ssh/h800_ed25519")
    ap.add_argument("--out-dir", default="trajectories")
    args = ap.parse_args()

    with open(args.task_list, encoding="utf-8") as f:
        tasks = json.load(f)

    env_extras = {
        "OPENAI_API_KEY": os.environ.get("GENOPT_GPT55_API_KEY") or os.environ.get("OPENAI_API_KEY", ""),
        "OPENAI_BASE_URL": os.environ.get("GENOPT_GPT55_BASE_URL") or "https://v2.qixuw.com/v1",
        "OPENAI_MODEL": os.environ.get("GENOPT_GPT55_MODEL") or "gpt-5.5",
    }

    use_h800 = bool(args.h800_host)
    runner = (lambda spec: _run_h800(spec["task_dir"], spec.get("n", 3),
                                      spec.get("effort", "xhigh"),
                                      spec.get("timeout", 600),
                                      args.h800_host, args.h800_port,
                                      os.path.expanduser(args.ssh_key), env_extras)
              ) if use_h800 else (lambda spec: _run_local(spec["task_dir"],
                                                          spec.get("n", 3),
                                                          spec.get("effort", "xhigh"),
                                                          spec.get("timeout", 600),
                                                          env_extras))

    os.makedirs(args.out_dir, exist_ok=True)
    summary = {}

    print(f"[batch] {len(tasks)} tasks, workers={args.workers}, h800={use_h800}")
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(runner, spec): spec["task_dir"] for spec in tasks}
        for fut in as_completed(futs):
            td = futs[fut]
            slug = os.path.basename(td.rstrip("/"))
            try:
                r = fut.result()
                print(f"[{slug}] rc={r.returncode}")
                if r.returncode != 0:
                    print(f"  stderr: {r.stderr[-500:]}", file=sys.stderr)
            except Exception as exc:
                print(f"[{slug}] EXC {exc}", file=sys.stderr)
                continue
            # try both possible trajectory paths
            for cand in [os.path.join(td, "gpt55_trajectory.json"),
                         os.path.join(td, "gpt55_trajectory_h800.json")]:
                gr = _grade_from_traj(cand)
                if gr:
                    out_traj = os.path.join(args.out_dir, f"{slug}.gpt55_trajectory.json")
                    try:
                        shutil_copy(cand, out_traj)
                    except Exception:
                        pass
                    summary[slug] = {"task_dir": td, **gr}
                    print(f"  -> {gr}")
                    break

    with open(os.path.join(args.out_dir, "batch_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print(f"[done] batch_summary -> {os.path.join(args.out_dir, 'batch_summary.json')}")


def shutil_copy(src, dst):
    import shutil
    shutil.copy2(src, dst)


if __name__ == "__main__":
    main()