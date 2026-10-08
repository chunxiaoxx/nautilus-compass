#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rsi-bench 格式回归集 v1 定版构建器(2026-10-08 · A 臂补齐,PR 件)。

选入判据(全实锚,零推断):
  A 臂 error 15 = django_report_a.error_ids(8) + a_eof_report.error_ids(1=sympy-13974
                  补跑后仍 apply fail 归格式,L3_BOARD_PAGE 脚注坐实)
                  + 归因简报 P3 rest 批 6 题(run_instance.log 实测 malformed)
  B 臂 error 11 = b_django/b_eof/b_rest 三报告 error_ids 并集
  合计 26 行(20 unique 题,双臂交集 6)——超外部承诺 25 的 +1 来自 A 臂补跑折入
  (sphinx-8475 补跑 resolved 移出后又由 sympy-13974 折入),如实交付不凑数。
缺陷标注(伴随特征,非选入门;口径=归因终版:malformed hunk 为主阻断,
缺尾换行为伴随特征非充分条件):
  no_trailing_newline / malformed_hunk / bad_newfile_path
patch 来源:A=preds_arm_a.json(model_patch),B=board_b/task_*/patch.diff。
输出:runtime/outreach/rsi_regression_set_v1.jsonl
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "runtime/loop/_r181_board30"
JUDGE = ROOT / "runtime/loop/_r198_judging"
OUT = ROOT / "runtime/outreach/rsi_regression_set_v1.jsonl"
EXPECT = ("after harness fix, same task reapply should pass "
          "or fail-for-content (not format)")
REST_P3 = [  # 归因简报 P3 rest 批 6 题(run_instance.log 实测)
    "matplotlib__matplotlib-26291", "pylint__pylint-4661",
    "pytest__pytest-5262", "scikit-learn__scikit-13779",
    "sympy__sympy-16792", "sympy__sympy-23262",
]


def check_format(patch: str) -> list[str]:
    hits = []
    if patch and not patch.endswith("\n"):
        hits.append("no_trailing_newline")
    lines = patch.splitlines() if patch else []
    i = 0
    while i < len(lines):
        m = re.match(r"@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", lines[i])
        if not m:
            i += 1
            continue
        a_n, b_n = int(m.group(1) or 1), int(m.group(3) or 1)
        i += 1
        ca = cb = 0
        while i < len(lines) and not lines[i].startswith("@@"):
            ln = lines[i]
            if ln.startswith("+"):
                cb += 1
            elif ln.startswith("-"):
                ca += 1
            elif ln.startswith("\\"):
                pass
            elif ln.startswith(("diff --git", "--- ", "+++ ")):
                break
            else:
                ca += 1
                cb += 1
            i += 1
        if (ca, cb) != (a_n, b_n):
            hits.append(f"malformed_hunk(decl {a_n},{b_n} != actual {ca},{cb})")
    if patch and re.search(r"^\+\+\+ b/(?:/|\.\.)", patch, re.M):
        hits.append("bad_newfile_path")
    return hits


def report_ids(name: str) -> list[str]:
    d = json.loads((JUDGE / name).read_text(encoding="utf-8"))
    return [x if isinstance(x, str) else str(x) for x in d.get("error_ids", [])]


def main():
    # A 臂 patches
    preds = json.load(open(DIR / "preds_arm_a.json", encoding="utf-8"))
    patch_a = {r["instance_id"]: r.get("model_patch") or ""
               for r in preds if isinstance(r, dict)}
    a_ids = (report_ids("django_report_a.json")
             + report_ids("a_eof_report.json") + REST_P3)
    # B 臂 patches + ids
    b_ids = set(report_ids("b_django_report_b.json")
                + report_ids("b_eof_report.json")
                + report_ids("b_rest_report_b.json"))
    patch_b = {}
    for td in sorted(DIR.glob("board_b/task_*")):
        pj, pp = td / "result.json", td / "patch.diff"
        if pj.exists():
            r = json.loads(pj.read_text(encoding="utf-8"))
            iid = r.get("instance_id")
            if iid and pp.exists():
                patch_b[iid] = pp.read_text(encoding="utf-8", errors="replace")

    rows = []
    for iid in a_ids:
        p = patch_a.get(iid, "")
        rows.append({"qid": iid, "arm": "A",
                     "defects": check_format(p), "patch_found": bool(p),
                     "patch_chars": len(p), "expectation": EXPECT,
                     "anchor": "round1_merged.arm_a error_ids=15(脚注:补跑折入)"})
    for iid in sorted(b_ids):
        p = patch_b.get(iid, "")
        rows.append({"qid": iid, "arm": "B",
                     "defects": check_format(p), "patch_found": bool(p),
                     "patch_chars": len(p), "expectation": EXPECT,
                     "anchor": "b_django/b_eof/b_rest error_ids 并集"})
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                   encoding="utf-8")
    from collections import Counter
    by_arm = Counter(r["arm"] for r in rows)
    uniq = len({r["qid"] for r in rows})
    both = {r["qid"] for r in rows if r["arm"] == "A"} & b_ids
    print(f"rows={len(rows)} | by arm: {dict(by_arm)} | unique tasks={uniq} "
          f"| both-arm errors={len(both)}")
    print("defects:", dict(Counter(d.split("(")[0] for r in rows for d in r["defects"])))
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
