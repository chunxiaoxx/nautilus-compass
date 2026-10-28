"""Produce a batch of GENUINELY DISTINCT JobShop GenOpt tasks.

Each task = a distinct set of OR-Library instances (different makespans/difficulty).
The generic naive-scheduler baseline + verifier are legitimately shared (what makes
tasks distinct is the DATA/instances, per buyer spec). Data is regenerated from the
tracked .orlib_jobshop1.txt; optima are the authoritative OR-Library proven optima
(validated 6/6 against the value that reproduced the documented baseline 24.6755).

For each task: build full spec-compliant dir + regenerate data + run verifier green.

Buyer 7/7 delivery contract (see reference_buyer_genopt_delivery_format_checklist):
every file declared in frontier_eval/artifact_files.txt MUST be regenerable by
running the workspace. This generator therefore:
  * evaluate.py (template) writes metrics.json + artifacts.json
  * ships reproduce.sh + Dockerfile CMD that capture eval.stdout.txt / eval.stderr.txt
  * runs the full reproduce step so each shipped task already contains all 4 artifacts
  * declares all 4 in artifact_files.txt and evaluate.py in agent_files.txt
"""
import os
import re
import json
import shutil
import subprocess
import sys

SP = os.path.dirname(__file__)
BASE_TASK = r"C:\Users\chunx\Projects\nautilus-core\genopt_factory\tasks\operations_research_and_decision_science\JobShop\jobshop_orlib_v1_001"
ORLIB = os.path.join(BASE_TASK, ".orlib_jobshop1.txt")
OUT = os.path.join(SP, "genopt_jobshop_batch")

# authoritative OR-Library proven optima (validated against ground-truth 6/6)
OPTIMA = {
    "ft06": 55, "ft10": 930, "ft20": 1165,
    "la01": 666, "la02": 655, "la03": 597, "la04": 590, "la05": 593,
    "la06": 926, "la07": 890, "la08": 863, "la09": 951, "la10": 958,
    "la11": 1222, "la12": 1039, "la13": 1150, "la14": 1292, "la15": 1207,
    "la16": 945, "la17": 784, "la18": 848, "la19": 842, "la20": 902,
    "la21": 1046, "la22": 927, "la23": 1032, "la24": 935, "la25": 977,
    "la36": 1268, "la37": 1397, "la38": 1196, "la39": 1233, "la40": 1222,
    # hard instances (JSPLIB best-known / proven-optimal) for best<95 Easy tier
    "la26": 1218, "la27": 1235, "la28": 1216, "la29": 1152, "la30": 1355,
    "la31": 1784, "la32": 1850, "la33": 1719, "la34": 1721, "la35": 1888,
    "abz7": 656, "abz8": 665, "abz9": 679,
    "swv01": 1407, "swv02": 1475, "swv03": 1398, "swv04": 1474, "swv05": 1424,
    "swv06": 1678, "swv07": 1600, "swv08": 1763, "swv09": 1661, "swv10": 1767,
    "swv11": 2991, "swv12": 3003, "swv13": 3104, "swv14": 2968, "swv15": 2904,
    "swv16": 2924, "swv17": 2794, "swv18": 2852, "swv19": 2843, "swv20": 2823,
    "yn1": 885, "yn2": 909, "yn3": 892, "yn4": 968,
    "orb01": 1059, "orb02": 888, "orb03": 1005, "orb04": 1005, "orb05": 887,
}

# 7 distinct tasks by problem class (no instance overlap)
TASKS = [
    ("jssp_ft_mixed_v1_001",   "Fisher-Thompson classic (mixed sizes)", ["ft06", "ft10", "ft20"]),
    ("jssp_la_10x5_v1_001",    "Lawrence 10 jobs x 5 machines",         ["la01", "la02", "la03", "la04", "la05"]),
    ("jssp_la_15x5_v1_001",    "Lawrence 15 jobs x 5 machines",         ["la06", "la07", "la08", "la09", "la10"]),
    ("jssp_la_20x5_v1_001",    "Lawrence 20 jobs x 5 machines",         ["la11", "la12", "la13", "la14", "la15"]),
    ("jssp_la_10x10_v1_001",   "Lawrence 10 jobs x 10 machines",        ["la16", "la17", "la18", "la19", "la20"]),
    ("jssp_la_15x10_v1_001",   "Lawrence 15 jobs x 10 machines",        ["la21", "la22", "la23", "la24", "la25"]),
    ("jssp_la_15x15_v1_001",   "Lawrence 15 jobs x 15 machines",        ["la36", "la37", "la38", "la39", "la40"]),
    # hard batch (20x10+): weak greedy seed -> big gap but best<95 = Easy tier
    ("jssp_la_20x10_v1_001",   "Lawrence 20 jobs x 10 machines",          ["la26", "la27", "la28", "la29", "la30"]),
    ("jssp_la_30x10_v1_001",   "Lawrence 30 jobs x 10 machines",          ["la31", "la32", "la33", "la34", "la35"]),
    ("jssp_swv_20x10_v1_001",  "Storer-Wu-Vaccari 20 jobs x 10 machines", ["swv01", "swv02", "swv03", "swv04", "swv05"]),
    ("jssp_swv_20x15_v1_001",  "Storer-Wu-Vaccari 20 jobs x 15 machines", ["swv06", "swv07", "swv08", "swv09", "swv10"]),
    ("jssp_abz_20x15_v1_001",  "Adams-Balas-Zawack 20 jobs x 15 machines", ["abz7", "abz8", "abz9"]),
    ("jssp_yn_20x20_v1_001",   "Yamada-Nakano 20 jobs x 20 machines",     ["yn1", "yn2", "yn3", "yn4"]),
    ("jssp_swv_50x10a_v1_001", "Storer-Wu-Vaccari 50 jobs x 10 machines (a)", ["swv11", "swv12", "swv13", "swv14", "swv15"]),
    ("jssp_swv_50x10b_v1_001", "Storer-Wu-Vaccari 50 jobs x 10 machines (b)", ["swv16", "swv17", "swv18", "swv19", "swv20"]),
    ("jssp_orb_10x10_v1_001",  "Applegate-Cook 10 jobs x 10 machines",    ["orb01", "orb02", "orb03", "orb04", "orb05"]),
]

FE_9 = {
    "eval_command.txt": "python verification/evaluate.py --benchmark-dir . --candidate baseline/init.py\n",
    "eval_cwd.txt": ".\n",
    "candidate_destination.txt": "baseline/init.py\n",
    "initial_program.txt": "baseline/init.py\n",
    # evaluate.py IS exposed to the agent (buyer checklist 2: model must read the verifier).
    "agent_files.txt": "Task.md\nREADME.md\nbaseline/init.py\nverification/evaluate.py\n",
    "readonly_files.txt": "verification/\ndata/\nfrontier_eval/\n",
    # all four artifacts are regenerable by running the workspace (buyer 7/7).
    "artifact_files.txt": "metrics.json\nartifacts.json\neval.stdout.txt\neval.stderr.txt\n",
    "constraints.txt": "minimize makespan; pure Python stdlib only; preserve solve_instance output {\"starts\": [[int]]}\n",
    "copy_files.txt": "data/\n",
}

README_REPRODUCE = (
    "\n## Reproduce the full artifact set\n"
    "Run `sh reproduce.sh` (or `docker build -t t . && docker run --rm t`).\n"
    "Regenerates every file in `frontier_eval/artifact_files.txt`:\n"
    "- `metrics.json`, `artifacts.json` — written by `verification/evaluate.py`\n"
    "- `eval.stdout.txt`, `eval.stderr.txt` — captured stdout/stderr of the eval command\n"
)


def parse_all(path):
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    starts = {}
    for i, ln in enumerate(lines):
        m = re.match(r"\s*instance\s+(\S+)\s*$", ln)
        if m:
            starts[m.group(1)] = i
    out = {}
    for name, i in starts.items():
        j = i + 1
        njobs = nmach = None
        while j < len(lines):
            toks = lines[j].split()
            if len(toks) == 2 and all(t.lstrip("-").isdigit() for t in toks):
                a, b = int(toks[0]), int(toks[1])
                if 1 <= a <= 100 and 1 <= b <= 100:
                    njobs, nmach = a, b
                    break
            j += 1
        if njobs is None:
            continue
        jobs, k = [], j + 1
        while k < len(lines) and len(jobs) < njobs:
            toks = lines[k].split()
            if len(toks) == 2 * nmach and all(t.lstrip("-").isdigit() for t in toks):
                nums = list(map(int, toks))
                jobs.append([(nums[2 * o], nums[2 * o + 1]) for o in range(nmach)])
            k += 1
        if len(jobs) == njobs:
            out[name] = {"name": name, "num_jobs": njobs, "num_machines": nmach, "jobs": jobs}
    return out


def build_task(all_inst, tid, desc, inst_names, dst):
    os.makedirs(dst, exist_ok=True)
    # framework files (generic, legitimately shared)
    shutil.copytree(os.path.join(BASE_TASK, "baseline"), os.path.join(dst, "baseline"))
    shutil.copytree(os.path.join(BASE_TASK, "verification"), os.path.join(dst, "verification"))
    shutil.copy2(os.path.join(BASE_TASK, "Dockerfile"), dst)
    shutil.copy2(os.path.join(BASE_TASK, "requirements.txt"), dst)
    # reproduce.sh: single-command regeneration of the full artifact set (buyer 7/7).
    shutil.copy2(os.path.join(BASE_TASK, "reproduce.sh"), dst)
    # data (distinct per task)
    inst_dir = os.path.join(dst, "data", "instances")
    os.makedirs(inst_dir, exist_ok=True)
    for n in inst_names:
        json.dump(all_inst[n], open(os.path.join(inst_dir, f"{n}.json"), "w"), indent=2)
    json.dump({n: OPTIMA[n] for n in inst_names},
              open(os.path.join(dst, "data", "optima.json"), "w"), indent=2)
    open(os.path.join(dst, "data", "SOURCE.txt"), "w").write(
        "OR-Library JSSP instances parsed from OR-Library (Fisher-Thompson/Lawrence).\n"
        "Optima: proven-optimal makespans (OR-Library canonical).\n")
    # frontier_eval 9
    fe = os.path.join(dst, "frontier_eval")
    os.makedirs(fe, exist_ok=True)
    for name, content in FE_9.items():
        open(os.path.join(fe, name), "w").write(content)
    # Task.md + README
    inst_list = ", ".join(inst_names)
    open(os.path.join(dst, "Task.md"), "w", encoding="utf-8").write(
        f"# Job-Shop Scheduling: Minimize Makespan ({desc})\n\n"
        f"## Problem\nMinimize the makespan on OR-Library JSSP instances: {inst_list}.\n"
        "Each instance has jobs with an ordered sequence of (machine, duration) operations.\n"
        "Precedence + machine-capacity + no-preemption constraints apply.\n\n"
        "## What to implement\nEdit `baseline/init.py`, keep `solve_instance(instance) -> {\"starts\": [[int]]}`.\n"
        "`starts[j][k]` = start time of op k of job j. Minimize the makespan.\n\n"
        "## Verify current score\n`python verification/evaluate.py --benchmark-dir . --candidate baseline/init.py`\n"
        "Score per instance = 100 * optimum / makespan; combined = mean over feasible instances; any infeasible => valid=0.\n")
    open(os.path.join(dst, "README.md"), "w", encoding="utf-8").write(
        f"# {desc}\n\nJSSP GenOpt task. Instances: {inst_list}.\n"
        "Baseline = naive list scheduler (suboptimal). Optimize toward known optima.\n"
        "Self-contained: data/instances/*.json + data/optima.json included.\n"
        + README_REPRODUCE)


def run_verifier(dst):
    """Run the full reproduce step so the shipped task already contains all four
    declared artifacts (metrics.json, artifacts.json, eval.stdout.txt, eval.stderr.txt).
    stdout/stderr are captured to files exactly as the buyer's harness / Dockerfile would.
    """
    out_path = os.path.join(dst, "eval.stdout.txt")
    err_path = os.path.join(dst, "eval.stderr.txt")
    with open(out_path, "w", encoding="utf-8") as so, open(err_path, "w", encoding="utf-8") as se:
        subprocess.run(
            [sys.executable, "verification/evaluate.py", "--benchmark-dir", ".",
             "--candidate", "baseline/init.py"],
            cwd=dst, stdout=so, stderr=se, text=True, timeout=300)
    mj = os.path.join(dst, "metrics.json")
    if os.path.exists(mj):
        return json.load(open(mj))
    return {"error": open(err_path, encoding="utf-8").read()[-300:]}


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    all_inst = parse_all(ORLIB)
    print(f"parsed {len(all_inst)} instances from OR-Library source\n")
    results = []
    for tid, desc, inst_names in TASKS:
        missing = [n for n in inst_names if n not in all_inst]
        if missing:
            print(f"[SKIP] {tid}: missing instances {missing}")
            continue
        dst = os.path.join(OUT, tid)
        build_task(all_inst, tid, desc, inst_names, dst)
        m = run_verifier(dst)
        cs, valid = m.get("combined_score"), m.get("valid")
        # verify every declared artifact was actually produced (buyer 7/7 contract)
        declared = [ln for ln in FE_9["artifact_files.txt"].splitlines() if ln.strip()]
        produced = {f: os.path.getsize(os.path.join(dst, f)) if os.path.exists(os.path.join(dst, f)) else -1
                    for f in declared}
        missing_art = [f for f, sz in produced.items() if sz < 0]
        results.append((tid, desc, inst_names, cs, valid, m))
        art_ok = "ARTIFACTS_OK" if not missing_art else f"MISSING_ARTIFACTS={missing_art}"
        status = "GREEN" if valid == 1.0 else "RED"
        print(f"[{status}] {tid:24s} instances={len(inst_names)} combined_score={cs} valid={valid} {art_ok}")
    json.dump([{"task_id": t, "desc": d, "instances": i, "combined_score": c, "valid": v}
               for t, d, i, c, v, _ in results],
              open(os.path.join(OUT, "batch_metrics.json"), "w"), indent=2)
    green = sum(1 for *_, v, _ in results if v == 1.0)
    print(f"\n=== {green}/{len(results)} tasks verifier GREEN (self-contained, runnable) ===")


if __name__ == "__main__":
    main()
