#!/usr/bin/env python3
"""compass · AutoLab A-cluster eval 提交接口(V5 producer 2-arm 用).

给定 候选解文件 → 用官方 AutoLab task 文件(environment/Makefile/main.c)编译+计时
→ 按 task.toml 锚(baseline=0.0/reference=0.5)算 reward → 输出 {reward, feedback}。
不重建 harness:复用官方 task 的 environment/ + test.sh 的打分公式(log-stretch / anchored-linear)。
打分只需 gcc/make/python3·不跑 agent loop(候选在别处产·只交文件来 eval)。

用法:
  python3 autolab_eval.py --task radix_sort --candidate path/to/solve.c [--trials 3] [--json out.json]
约束:v1 支持 runtime_seconds 类(系统优化·候选=solve.c)。其他 metric 类(comparator/cycles/params)TODO。
"""
import argparse, json, math, os, shutil, subprocess, tempfile, tomllib

AUTOLAB = os.environ.get("AUTOLAB_DIR", "/mnt/datadisk0/autolab")

def load_task(task):
    tdir = os.path.join(AUTOLAB, "tasks", task)
    with open(os.path.join(tdir, "task.toml"), "rb") as f:
        meta = tomllib.load(f)
    return tdir, meta

def reward_from_metric(median, meta):
    opt = meta.get("optimization", {})
    base = opt.get("baseline", {}).get("score")
    ref = opt.get("reference", {}).get("score")
    direction = opt.get("direction", "lower")
    if base is None or ref is None:
        return None, "no anchors in task.toml"
    if direction == "lower":
        if median <= 0:
            return 0.0, "non-positive metric"
        speedup = base / median
        ref_speedup = base / ref
        if speedup <= 1.0:
            return 0.0, f"speedup {speedup:.2f}x <= 1.0 (slower than baseline {base})"
        reward = min(1.0, 0.5 * math.log(speedup) / math.log(ref_speedup))
        return round(max(0.0, reward), 4), f"speedup {speedup:.2f}x (baseline {base}/ref {ref})"
    else:  # higher
        if base == 0:
            frac = median / ref if ref else 0
        else:
            frac = (median - base) / (ref - base) if ref != base else 0
        return round(min(1.0, max(0.0, 0.5 * frac / 1.0)), 4), f"value {median} (baseline {base}/ref {ref})"

def eval_candidate(task, candidate, trials=3):
    tdir, meta = load_task(task)
    env = os.path.join(tdir, "environment")
    metric = meta.get("optimization", {}).get("metric", "")
    if metric != "runtime_seconds":
        return {"task": task, "error": f"v1 only supports runtime_seconds tasks; {task} uses {metric}"}
    work = tempfile.mkdtemp(prefix=f"alab_{task}_")
    try:
        # 官方 environment 文件(只读源)+ 候选 solve.c
        for fn in os.listdir(env):
            if fn != "solve.c":
                shutil.copy(os.path.join(env, fn), os.path.join(work, fn))
        # 防御:剥离 LLM 常带的 markdown 代码围栏(```c ... ```)·否则 stray '`' 编译失败(artifact 非真失败)
        src = open(candidate, encoding="utf-8", errors="replace").read()
        lines, stripped = src.splitlines(keepends=True), 0
        clean = []
        for ln in lines:
            s = ln.strip()
            if s.startswith("```") or s == "```":
                stripped += 1
                continue
            clean.append(ln)
        open(os.path.join(work, "solve.c"), "w", encoding="utf-8").write("".join(clean))
        self_fence_note = f" [stripped {stripped} markdown-fence line(s)]" if stripped else ""
        # build
        b = subprocess.run(["make"], cwd=work, capture_output=True, text=True)
        if b.returncode != 0:
            return {"task": task, "candidate": os.path.basename(candidate), "build": False,
                    "correct": False, "reward": 0.0,
                    "feedback": f"build_failed: {b.stderr.strip()[-400:]}"}
        # run trials
        times, sortbad = [], False
        for _ in range(trials):
            r = subprocess.run(["./solve"], cwd=work, capture_output=True, text=True)
            out = r.stdout
            import re
            mt = re.search(r"time=([0-9.]+)", out)
            ms = re.search(r"sorted=(\S+)", out)
            if ms and ms.group(1) != "ok":
                sortbad = True
            if mt:
                times.append(float(mt.group(1)))
        if sortbad or not times:
            return {"task": task, "candidate": os.path.basename(candidate), "build": True,
                    "correct": False, "reward": 0.0,
                    "feedback": "correctness_FAIL: output not sorted (wrong answer scores 0)"}
        times.sort()
        n = len(times)
        median = times[n // 2] if n % 2 else (times[n // 2 - 1] + times[n // 2]) / 2
        reward, note = reward_from_metric(median, meta)
        fb = f"correct; median={median:.4f}s; {note}; reward={reward}{self_fence_note}"
        if reward == 0.0:
            fb += " | 避坑: 候选未超 baseline 锚,优化方向无效或退化"
        elif reward < 0.3:
            fb += " | 避坑: 远低于 reference,需更深优化(访存合并/SIMD/并行/cache)"
        return {"task": task, "candidate": os.path.basename(candidate), "build": True,
                "correct": True, "median": round(median, 4), "reward": reward, "feedback": fb}
    finally:
        shutil.rmtree(work, ignore_errors=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--json")
    a = ap.parse_args()
    res = eval_candidate(a.task, a.candidate, a.trials)
    s = json.dumps(res, ensure_ascii=False, indent=1)
    print(s)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(s)
