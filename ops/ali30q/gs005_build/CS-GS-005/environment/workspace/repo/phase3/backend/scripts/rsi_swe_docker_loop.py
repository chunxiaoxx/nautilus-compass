#!/usr/bin/env python3
"""Path B 2-turn RSI 环(Docker 官方 harness 版·跑在 Linux·2026-06-19)。

本地 pytest 路(rsi_swe_loop）受装环境地狱限(老题 Py3.13 装不上）+ Docker-on-Windows
CRLF 破容器。本版在 Linux(cloud）跑官方 SWE-bench harness(per-instance 镜像=正确老
Python）→ 解锁全 Lite 池(含高 F2P:requests-2148/astropy/django）。

复用 rsi_swe_loop 的 producer 纯函数(prompt/SEARCH-REPLACE/apply/diff·已 TDD）+ swe_verify
（记忆/rsi_improved）+ swe_docker（Docker effect + report 解析）。只换两件:
  prep = clone+checkout(只读·读 oracle 源文件·不装不跑·Docker 负责跑）
  effect = run_candidate_docker（替 swe_runner.run_candidate）。

用法(cloud·venv python·带 BAILIAN_API_KEY env）:
  python scripts/rsi_swe_docker_loop.py astropy__astropy-6938 --model qwen3.7-max --k 4 \
      --workdir ~/swe-rsi/harness --out ~/swe-rsi/rsi_astropy.json
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.fde_sdiagnose_run import bailian_complete, load_secrets  # noqa: E402
from services.swe_docker import parse_harness_report, run_candidate_docker  # noqa: E402
from services.swe_verify import (  # noqa: E402
    build_swe_memory, extract_failures_section, rsi_improved,
)
from scripts.rsi_swe_loop import (  # noqa: E402
    _build_prompt, _source_files_from_gold, apply_edits, build_unified_diff,
    parse_search_replace,
)

REPO_URL = {
    "astropy/astropy": "https://github.com/astropy/astropy.git",
    "django/django": "https://github.com/django/django.git",
    "psf/requests": "https://github.com/psf/requests.git",
    "sympy/sympy": "https://github.com/sympy/sympy.git",
    "pytest-dev/pytest": "https://github.com/pytest-dev/pytest.git",
    "scikit-learn/scikit-learn": "https://github.com/scikit-learn/scikit-learn.git",
    "matplotlib/matplotlib": "https://github.com/matplotlib/matplotlib.git",
    "sphinx-doc/sphinx": "https://github.com/sphinx-doc/sphinx.git",
    "pylint-dev/pylint": "https://github.com/pylint-dev/pylint.git",
    "pydata/xarray": "https://github.com/pydata/xarray.git",
    "mwaskom/seaborn": "https://github.com/mwaskom/seaborn.git",
    "pallets/flask": "https://github.com/pallets/flask.git",
}


def _load_instance(instance_id):
    from datasets import load_dataset
    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    for r in ds:
        if r["instance_id"] == instance_id:
            return r
    raise SystemExit("instance not found: %s" % instance_id)


def _read_prep(inst, clones_dir):
    """clone repo + checkout base_commit(只读·读 oracle 源文件·Docker 负责真跑）。回 base_dir。"""
    repo = inst["repo"]
    url = REPO_URL.get(repo)
    if not url:
        raise SystemExit("no clone url for %s" % repo)
    slug = repo.replace("/", "__")
    d = os.path.join(clones_dir, slug)
    if not os.path.isdir(os.path.join(d, ".git")):
        os.makedirs(clones_dir, exist_ok=True)
        print("[prep] cloning %s (one-time)..." % repo, flush=True)
        subprocess.run(["git", "clone", url, d], check=True, capture_output=True, text=True, timeout=1800)
    subprocess.run(["git", "-C", d, "checkout", "-f", inst["base_commit"]],
                   check=True, capture_output=True, text=True, timeout=300)
    subprocess.run(["git", "-C", d, "clean", "-fdx", "-q"], capture_output=True, text=True, timeout=300)
    return d


def _attempt(prompt, src_files, base_dir, instance_id, run_id, model, tag, workdir):
    """produce → SEARCH/REPLACE → diff → Docker harness → 离散 reward。

    回 (report_dict, fails, diff, test_output)。report_dict 含 f2p_passed(reward）。
    """
    resp = ""
    for _t in range(2):
        try:
            resp = bailian_complete(prompt, model=model)
        except Exception as ex:  # noqa: BLE001
            print("  [%s] produce_error %s" % (tag, str(ex)[:120]), flush=True)
            return None, [], "", ""
        if resp and resp.strip():
            break
        print("  [%s] empty resp retry %d" % (tag, _t + 1), flush=True)
    edits = parse_search_replace(resp)
    if not edits:
        print("  [%s] no SEARCH/REPLACE parsed (head %r)" % (tag, resp[:100]), flush=True)
        return None, [], "", ""
    new_files = {}
    for rel in src_files:
        fp = os.path.join(base_dir, rel.replace("/", os.sep))
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            orig = f.read()
        nt, applied, _ = apply_edits(orig, edits)
        if applied > 0:
            new_files[rel] = nt
    if not new_files:
        print("  [%s] %d edits parsed but 0 applied" % (tag, len(edits)), flush=True)
        return None, [], "", ""
    diff = build_unified_diff(base_dir, new_files)
    if not diff.strip():
        print("  [%s] empty diff" % tag, flush=True)
        return None, [], "", ""
    res = run_candidate_docker(instance_id, diff, run_id=run_id, workdir=workdir)
    rep = res["report"]
    fails = rep.get("f2p_fail_tests", [])
    print("  [%s] %d edits applied · f2p_passed=%s/%s applied=%s resolved=%s"
          % (tag, len(edits), rep.get("f2p_passed"), rep.get("f2p_total"),
             rep.get("applied"), rep.get("resolved")), flush=True)
    return rep, fails, diff, res.get("test_output", "")


def _best_of_k(prompt, src_files, base_dir, instance_id, run_id_base, model, tag, k, workdir):
    best = None
    rewards = []
    info = None
    for i in range(k):
        rid = "%s_%s_%d" % (run_id_base, tag, i + 1)
        rep, fails, diff, tout = _attempt(prompt, src_files, base_dir, instance_id,
                                          rid, model, "%s.%d" % (tag, i + 1), workdir)
        r = rep.get("f2p_passed") if rep else None
        rewards.append(r)
        rv = r if r is not None else -1
        if best is None or rv > best:
            best = rv
            info = (rep, fails, diff, tout)
    print("  [%s] rewards k=%d: %s → best=%s" % (tag, k, rewards, best), flush=True)
    return best, info, rewards


def run(instance_id, model, out_path, k, workdir, clones_dir, probe=False):
    load_secrets()
    inst = _load_instance(instance_id)
    problem = inst["problem_statement"]
    src_files = _source_files_from_gold(inst["patch"])
    f2p_n = len(json.loads(inst["FAIL_TO_PASS"]) if isinstance(inst["FAIL_TO_PASS"], str) else inst["FAIL_TO_PASS"])
    base_dir = _read_prep(inst, clones_dir)
    print("[swe-rsi-docker] %s model=%s src_files=%s k=%d n_f2p=%d probe=%s"
          % (instance_id, model, src_files, k, f2p_n, probe), flush=True)

    print("\n=== TURN 1 (no memory, k=%d) ===" % k, flush=True)
    p1 = _build_prompt(problem, src_files, base_dir)
    x, info1, rew1 = _best_of_k(p1, src_files, base_dir, instance_id, "t1", model, "t1", k, workdir)
    xv = x if x is not None and x >= 0 else None
    print("[swe-rsi-docker] turn-1 best f2p_passed = %s" % xv, flush=True)

    if probe:
        # 只探甜点:turn-1 落 0<X<N = sweet。写精简 report·跳 turn-2。
        sweet = xv is not None and 0 < xv < f2p_n
        rep = {"instance_id": instance_id, "n_f2p": f2p_n, "turn1_passed": xv,
               "turn1_rewards_k": rew1, "sweet_spot": sweet, "probe": True}
        print("[probe] %s X=%s/%s sweet=%s" % (instance_id, xv, f2p_n, sweet), flush=True)
        if out_path:
            json.dump(rep, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return rep

    y, rew2, memory = None, [], None
    if xv is None or info1 is None:
        print("[swe-rsi-docker] turn-1 no parseable result — abort.", flush=True)
    else:
        rep1, fails1, diff1, tout1 = info1
        summ = {"passed": rep1["f2p_passed"], "failed": len(fails1), "errored": 0}
        memory = build_swe_memory(diff1, summ, [{"test": t, "reason": ""} for t in fails1],
                                  traceback_text=extract_failures_section(tout1 or "") or (tout1 or "")[-3000:])
        print("\n=== TURN 2 (memory injected, k=%d) ===" % k, flush=True)
        p2 = _build_prompt(problem, src_files, base_dir, memory="\n" + memory)
        yb, _info2, rew2 = _best_of_k(p2, src_files, base_dir, instance_id, "t2", model, "t2", k, workdir)
        y = yb if yb is not None and yb >= 0 else None
        print("[swe-rsi-docker] turn-2 best f2p_passed = %s" % y, flush=True)

    proven = rsi_improved(xv, y)
    report = {"instance_id": instance_id, "model": model, "k": k,
              "turn1_passed": xv, "turn2_passed": y,
              "turn1_rewards_k": rew1, "turn2_rewards_k": rew2,
              "rsi_proven": proven, "memory_injected": memory is not None,
              "src_files": src_files}
    print("\n===== SWE-RSI-DOCKER %s =====" % instance_id, flush=True)
    print("turn-1=%s · turn-2=%s · rsi_proven(Y>X)=%s" % (xv, y, proven), flush=True)
    if out_path:
        json.dump(report, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("[swe-rsi-docker] wrote %s" % out_path, flush=True)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("instance_id")
    ap.add_argument("--model", default="qwen3.7-max")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--out", default=None)
    ap.add_argument("--workdir", default=os.path.expanduser("~/swe-rsi/harness"))
    ap.add_argument("--clones", default=os.path.expanduser("~/swe-rsi/clones"))
    ap.add_argument("--probe", action="store_true", help="只跑 turn-1 探甜点(0<X<N)·跳 turn-2")
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    os.makedirs(a.clones, exist_ok=True)
    run(a.instance_id, a.model, a.out, a.k, a.workdir, a.clones, probe=a.probe)


if __name__ == "__main__":
    main()
