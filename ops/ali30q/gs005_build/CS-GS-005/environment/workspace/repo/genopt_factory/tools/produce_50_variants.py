"""Generate 50 GenOpt RL task variants from 7/3 grounded 5 tasks (anchors #3 + #5).

Reads _v6_50_variants.json (5 domains × 10 variants each = 50 tasks),
runs produce_task.py for each, then re-generates data instances with
new seed. Reuses the existing 5 grounded task templates (JobShop/TSP/
BinPack/Attention/Cache) — only data/instances are re-seeded.

Output: 50 new task directories under genopt_factory/tasks/<domain>/<subtype>/.
Each task is then ready for H800 N=3 GPT5.5 calibration (separate runner).
"""

import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPEC_PATH = os.path.join(REPO, "genopt_factory", "tools", "_v6_50_variants.json")
TEMPLATE_DIR = os.path.join(REPO, "genopt_factory", "tasks")

TEMPLATE_MAP = {
    ("operations_research_and_decision_science", "JobShop"): "JobShop/jobshop_orlib_v1_001",
    ("operations_research_and_decision_science", "TSP"):     "TSP/tsp_tsplib_v1_001",
    ("operations_research_and_decision_science", "BinPack"): "BinPack/bin_packing_ffd_v1_001",
    ("kernel_engineering_and_systems",        "Attention"): "Attention/attention_flash_v1_001",
    ("computer_systems",                      "Cache"):     "Cache/cache_lru_v1_001",
}


def main():
    with open(SPEC_PATH, encoding="utf-8") as f:
        specs = json.load(f)
    print(f"[spec] {len(specs)} variants loaded", flush=True)
    success = 0
    failures = []
    # Real template convention: <subtype>/<subtype>_<variant_name>_v1_001
    # (e.g. JobShop/jobshop_orlib_a_v1_001, NOT <domain>/<subtype>/...)
    for idx, spec in enumerate(specs):
        dom = spec["domain"]
        subtype = spec["subtype"]
        variant = spec["variant"]
        var_safe = variant.replace("-", "_").replace(".", "_")
        out_subpath = f"{subtype}/{subtype}_{var_safe}_v1_001"
        out_path = os.path.join(TEMPLATE_DIR, dom, out_subpath)
        template_path = os.path.join(TEMPLATE_DIR, dom, TEMPLATE_MAP[(dom, subtype)])
        if os.path.isdir(out_path):
            print(f"[{idx+1}/{len(specs)}] skip (exists): {out_subpath}", flush=True)
            success += 1
            continue
        # Strip timestamp from variant name to keep dirs short
        vars_json = json.dumps({
            "name_suffix": f"_{var_safe}",
            "master_seed": 20260704 + idx,
            "domain": dom,
            "task_subtype": subtype,
            "variant": variant,
        })
        try:
            r = subprocess.run(
                ["python", os.path.join(REPO, "genopt_factory", "tools", "produce_task.py"),
                 "--template", template_path, "--vars", vars_json, "--out", out_path],
                capture_output=True, text=True, timeout=60, cwd=REPO,
            )
            if r.returncode == 0:
                print(f"[{idx+1}/{len(specs)}] OK: {out_subpath}", flush=True)
                success += 1
            else:
                msg = (r.stderr or r.stdout)[-200:]
                print(f"[{idx+1}/{len(specs)}] FAIL: {out_subpath}: {msg}", flush=True)
                failures.append((variant, msg))
        except subprocess.TimeoutExpired:
            failures.append((variant, "timeout"))
            print(f"[{idx+1}/{len(specs)}] TIMEOUT: {variant}", flush=True)
        except Exception as exc:
            failures.append((variant, str(exc)))
            print(f"[{idx+1}/{len(specs)}] EXC: {variant}: {exc}", flush=True)
    print(f"\n[summary] {success}/{len(specs)} generated; {len(failures)} failed", flush=True)
    if failures:
        for v, m in failures[:10]:
            print(f"  - {v}: {m}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())