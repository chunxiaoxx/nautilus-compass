#!/usr/bin/env python3
"""GPU-box-side: 采集 SWE 燃料 mint 需的 buggy 原文 + edit_paths(契约 B·2026-06-20)。

soul mint 内嵌 original_files → V5 producer 出修正全文 → difflib 算 git-apply 兼容 diff
(零网络零 dataset 依赖)。本脚本在 GPU box(有 SWE-bench_Lite dataset + repo clones)跑,
输出 JSON {instance_id, repo, base_commit, problem_statement, edit_paths, original_files, n_f2p}
→ scp 回 cloud → mint_swe_fuel.py --prep-file 消费。

自包含(不依赖 scripts 包·防遮蔽):dataset 直载 + gold patch 解 edit paths + git checkout 读原文。

用法(GPU box·venv):
  /mnt/datadisk0/swe-rsi/venv/bin/python scripts/swe_fuel_prep.py psf__requests-2148 \
     --clones /mnt/datadisk0/swe-rsi/clones --out /tmp/prep_requests2148.json
"""
import argparse
import json
import os
import subprocess
import sys

_REPO_URL = {
    "psf/requests": "https://github.com/psf/requests.git",
    "sympy/sympy": "https://github.com/sympy/sympy.git",
    "pallets/flask": "https://github.com/pallets/flask.git",
    "django/django": "https://github.com/django/django.git",
    "astropy/astropy": "https://github.com/astropy/astropy.git",
    "scikit-learn/scikit-learn": "https://github.com/scikit-learn/scikit-learn.git",
    "pytest-dev/pytest": "https://github.com/pytest-dev/pytest.git",
    "matplotlib/matplotlib": "https://github.com/matplotlib/matplotlib.git",
    "sphinx-doc/sphinx": "https://github.com/sphinx-doc/sphinx.git",
    "pylint-dev/pylint": "https://github.com/pylint-dev/pylint.git",
    "pydata/xarray": "https://github.com/pydata/xarray.git",
    "mwaskom/seaborn": "https://github.com/mwaskom/seaborn.git",
}


def edit_paths_from_patch(patch: str) -> list:
    """gold patch → 被改文件相对路径(用 '+++ b/<path>' 行·最可靠)。"""
    paths = []
    for ln in (patch or "").splitlines():
        if ln.startswith("+++ b/"):
            p = ln[len("+++ b/"):].strip()
            if p and p != "/dev/null" and p not in paths:
                paths.append(p)
    return paths


def load_instance(instance_id: str) -> dict:
    from datasets import load_dataset
    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    for r in ds:
        if r["instance_id"] == instance_id:
            return r
    raise SystemExit("instance not found: %s" % instance_id)


def read_prep(inst: dict, clones_dir: str) -> str:
    repo = inst["repo"]
    url = _REPO_URL.get(repo)
    if not url:
        raise SystemExit("no clone url for %s" % repo)
    d = os.path.join(clones_dir, repo.replace("/", "__"))
    if not os.path.isdir(os.path.join(d, ".git")):
        os.makedirs(clones_dir, exist_ok=True)
        subprocess.run(["git", "clone", url, d], check=True, capture_output=True,
                       text=True, timeout=1800)
    subprocess.run(["git", "-C", d, "checkout", "-f", inst["base_commit"]],
                   check=True, capture_output=True, text=True, timeout=300)
    subprocess.run(["git", "-C", d, "clean", "-fdx", "-q"], capture_output=True,
                   text=True, timeout=300)
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("instance_id")
    ap.add_argument("--clones", default="/mnt/datadisk0/swe-rsi/clones")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    inst = load_instance(a.instance_id)
    edit_paths = edit_paths_from_patch(inst["patch"])
    if not edit_paths:
        print("WARN: no edit paths from gold patch", file=sys.stderr)
    base_dir = read_prep(inst, a.clones)
    original_files = {}
    for p in edit_paths:
        fp = os.path.join(base_dir, p.replace("/", os.sep))
        if os.path.exists(fp):
            original_files[p] = open(fp, encoding="utf-8", errors="replace").read()
    f2p = inst["FAIL_TO_PASS"]
    n_f2p = len(json.loads(f2p) if isinstance(f2p, str) else f2p)

    out = {
        "instance_id": a.instance_id, "repo": inst["repo"],
        "base_commit": inst["base_commit"], "problem_statement": inst["problem_statement"],
        "edit_paths": edit_paths, "original_files": original_files, "n_f2p": n_f2p,
    }
    payload = json.dumps(out, ensure_ascii=False)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(payload)
        print("[prep] wrote %s (edit_paths=%s n_f2p=%d files=%d)"
              % (a.out, edit_paths, n_f2p, len(original_files)))
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
