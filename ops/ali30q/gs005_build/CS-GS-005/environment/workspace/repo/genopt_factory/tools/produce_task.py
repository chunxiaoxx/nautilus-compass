"""GenOpt task factory: emit K variant tasks from a single template.

A template is a directory under genopt_factory/tasks/<domain>/<template>/ that
already contains the full skeleton: Task.md (with placeholders), baseline/init.py,
reference/solve.py, verification/evaluate.py, 9 frontier_eval/*.txt, Dockerfile.

This script:
  1. Copies the template to a new task dir (e.g. tsp_tsplib_v2_001)
  2. Substitutes {{placeholders}} in every text file (Task.md, README.md,
     frontier_eval/*.txt) using values from --vars (JSON)
  3. Runs the task's fetch_*.py to regenerate data/instances/ with new seed
     (so instances are deterministic per variant, not duplicated from template)
  4. Re-scores baseline/reference to populate metrics.json with REAL numbers
  5. Writes frontier_eval/delivery_metadata.txt with task_uid + spec ref

Usage:
    python produce_task.py --template genopt_factory/tasks/OR/TSP/tsp_tsplib_v1_001 \\
        --vars '{"name_suffix": "v2", "instance_set": "larger", "master_seed": 17, \\
                "scale": 1.5, "label": "TSP-Large"}' \\
        --out genopt_factory/tasks/OR/TSP/tsp_tsplib_v2_001

The template must contain a fetch_*.py script named in --fetch-script
(default: fetch_tsplib_synth.py for OR; or detect from naming).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys


PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def render_string(s, vars_):
    def sub(m):
        k = m.group(1)
        if k not in vars_:
            raise KeyError(f"missing var: {k}")
        return str(vars_[k])
    return PLACEHOLDER_RE.sub(sub, s)


def render_file(path, vars_):
    with open(path, encoding="utf-8") as f:
        s = f.read()
    s2 = render_string(s, vars_)
    if s2 != s:
        with open(path, "w", encoding="utf-8") as f:
            f.write(s2)


def render_tree(root, vars_):
    for d, _, files in os.walk(root):
        for fn in files:
            p = os.path.join(d, fn)
            if not (fn.endswith(".txt") or fn.endswith(".md") or fn.endswith(".json")):
                continue
            try:
                render_file(p, vars_)
            except (UnicodeDecodeError, KeyError) as exc:
                print(f"  skip {p}: {exc}", file=sys.stderr)


def detect_fetch_script(template_root):
    """Look for a tools/.../fetch_*.py that lives next to the template."""
    candidates = []
    for d, _, files in os.walk(os.path.dirname(template_root)):
        for fn in files:
            if fn.startswith("fetch_") and fn.endswith(".py"):
                candidates.append(os.path.join(d, fn))
    return candidates[0] if candidates else None


def run(cmd, cwd, timeout=600):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True,
                    help="source task dir (with full skeleton)")
    ap.add_argument("--out", required=True,
                    help="destination task dir (will be created)")
    ap.add_argument("--vars", required=True,
                    help="JSON string of placeholder values")
    ap.add_argument("--fetch-script", default=None,
                    help="path to fetch_*.py to regenerate data; auto-detect if omitted")
    ap.add_argument("--skip-fetch", action="store_true",
                    help="reuse template's data/ as-is (only for purely copy-style variants)")
    ap.add_argument("--skip-baseline", action="store_true",
                    help="don't re-score baseline after copy")
    args = ap.parse_args()

    template = os.path.abspath(args.template)
    out = os.path.abspath(args.out)
    if not os.path.isdir(template):
        print(f"template not found: {template}", file=sys.stderr)
        sys.exit(1)
    if os.path.exists(out):
        print(f"output already exists: {out}", file=sys.stderr)
        sys.exit(1)

    vars_ = json.loads(args.vars)

    print(f"[copy] {template} -> {out}")
    shutil.copytree(template, out)

    print(f"[render] placeholders in {out}")
    render_tree(out, vars_)

    fetch = args.fetch_script or detect_fetch_script(template)
    if not args.skip_fetch and fetch:
        # Point the fetch script at the variant's data/ dir.
        data_dir = os.path.join(out, "data")
        print(f"[fetch] running {fetch} against {data_dir}")
        rel_fetch = os.path.relpath(fetch, os.path.dirname(args.template) or ".")
        # If fetch lives outside the template, prefer absolute path.
        fetch_arg = fetch if os.path.isabs(fetch) else os.path.abspath(fetch)
        r = run([sys.executable, fetch_arg, data_dir], cwd=os.path.dirname(fetch) or ".")
        print(r.stdout[-1000:])
        if r.returncode != 0:
            print(f"  fetch stderr: {r.stderr[-1000:]}", file=sys.stderr)
            sys.exit(r.returncode)
    else:
        print("[fetch] skipped")

    if not args.skip_baseline:
        eval_py = os.path.join(out, "verification", "evaluate.py")
        baseline = os.path.join(out, "baseline", "init.py")
        if os.path.isfile(eval_py) and os.path.isfile(baseline):
            print(f"[score] baseline")
            r = run([sys.executable, eval_py, "--benchmark-dir", out, "--candidate", baseline],
                    cwd=out, timeout=1800)
            print(r.stdout[-800:])
            if r.returncode != 0:
                print(f"  baseline stderr: {r.stderr[-1000:]}", file=sys.stderr)
        else:
            print("[score] no evaluate.py / baseline/init.py — skipped")

    # Stamp delivery_metadata with task_uid derived from out path + date.
    today = __import__("datetime").datetime.utcnow().strftime("%Y%m%d")
    slug = os.path.basename(out.rstrip("/").rstrip("\\"))
    parts = out.replace("\\", "/").split("/")
    # Find domain segment (operations_research_and_decision_science, ...)
    domain = "?"
    for i, p in enumerate(parts):
        if p == "operations_research_and_decision_science":
            domain = "OR"; break
        if p in ("kernel_engineering", "computer_systems", "quantum_information",
                 "robotics_control", "optical_communication", "energy_systems",
                 "physics_engineering"):
            domain = p; break
    task_uid = f"genopt_{domain.lower()}_{slug}_{today}"
    meta_path = os.path.join(out, "frontier_eval", "delivery_metadata.txt")
    if os.path.isfile(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            md = f.read()
        md2 = re.sub(r"task_uid:\s*\S+", f"task_uid: {task_uid}", md)
        if "task_uid:" not in md2:
            md2 = f"task_uid: {task_uid}\n" + md2
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(md2)
    print(f"[done] {out}  task_uid={task_uid}")


if __name__ == "__main__":
    main()