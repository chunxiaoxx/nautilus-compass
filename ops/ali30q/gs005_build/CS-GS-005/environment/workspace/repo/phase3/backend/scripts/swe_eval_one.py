#!/usr/bin/env python3
"""GPU-box-side: 单 SWE patch → swebench 官方 harness → report JSON 到 stdout(P1.3b·2026-06-20)。

cloud 侧 services.swe_docker.remote_swe_eval ssh 调本脚本。薄包 run_candidate_docker
(已在 GPU box·rsi_swe_docker_loop 用同一函数)。stdout 末尾打印单行 JSON = report
(parse_harness_report 输出:parsed/applied/resolved/f2p_total/f2p_passed/f2p_fail_tests)。

🔴 跑在 GPU box(43.166.8.20)·非 cloud 生产 box(重 Docker·铁律)。串行(harness max_workers=1)。

用法:
  /mnt/datadisk0/swe-rsi/venv/bin/python scripts/swe_eval_one.py psf__requests-2148 \
     --patch-file /tmp/p.diff --run-id verify_x --workdir /mnt/datadisk0/swe-rsi/harness
"""
import argparse
import json
import os
import sys

# backend on path(GPU box vendored)
sys.path.insert(0, os.environ.get("SWE_BACKEND", "/mnt/datadisk0/swe-rsi/backend"))
from services.swe_docker import run_candidate_docker  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("instance_id")
    ap.add_argument("--patch-file", required=True)
    ap.add_argument("--run-id", default="verify")
    ap.add_argument("--workdir", default="/mnt/datadisk0/swe-rsi/harness")
    ap.add_argument("--dataset", default="princeton-nlp/SWE-bench_Lite")
    a = ap.parse_args()

    try:
        patch = open(a.patch_file, encoding="utf-8").read()
    except OSError as ex:
        print(json.dumps({"parsed": False, "error": "patch read fail: %s" % ex}))
        return 1

    os.makedirs(a.workdir, exist_ok=True)
    try:
        res = run_candidate_docker(a.instance_id, patch, run_id=a.run_id,
                                   dataset=a.dataset, workdir=a.workdir)
        report = res.get("report") if isinstance(res, dict) else None
        report = report or {"parsed": False, "error": "no report"}
    except Exception as ex:  # noqa: BLE001 — 诚实回 error·cloud 侧判 ok=False retry
        report = {"parsed": False, "error": "harness exc: %s" % str(ex)[:200]}

    print("SWE_REPORT_JSON " + json.dumps(report))  # 前缀便于 cloud 侧抓单行
    return 0


if __name__ == "__main__":
    sys.exit(main())
