#!/usr/bin/env python3
"""L3 Round 1 抽查件:①全 30 题"解在题面"污染扫描 ②分层抽 6 题/臂复核。
数据源:tasks.json(题面)+gold30.json(A100 HF cache 导出的 {iid:{patch,problem_statement}})。
判据:抽查 ≥6 题/臂(预注册 §判分工序);解在题面=gold patch 新增行(有效≥10 字符)规范化子串
命中 problem_statement 即 flag(近似检测,标 [推断])。"""
import json, re
from pathlib import Path

HERE = Path(__file__).parent
BASE = HERE.parent / "_r181_board30"
TASKS = BASE / "tasks.json"
PREDS = {"A": BASE / "preds_arm_a.json", "B": BASE / "preds_arm_b.json"}
GOLD = HERE / "gold30.json"
REPORTS = {"A": [HERE / "rest_report_a.json", HERE / "django_report_a.json", HERE / "a_eof_report.json"],
           "B": [HERE / "b_rest_report_b.json", HERE / "b_django_report_b.json", HERE / "b_eof_report.json"]}
KEYS = ("resolved_ids", "unresolved_ids", "error_ids", "empty_patch_ids")
STAT = {"resolved_ids": "resolved", "unresolved_ids": "unresolved", "empty_patch_ids": "empty", "error_ids": "error"}


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def gold_added_lines(patch: str):
    return [ln[1:].strip() for ln in patch.splitlines()
            if ln.startswith("+") and not ln.startswith("+++") and len(ln[1:].strip()) >= 10]


def main() -> int:
    tasks = {t["instance_id"]: t for t in json.loads(TASKS.read_text(encoding="utf-8"))}
    assert len(tasks) == 30
    gold = json.loads(GOLD.read_text(encoding="utf-8")) if GOLD.exists() else {}

    status = {a: {} for a in "AB"}
    for arm, files in REPORTS.items():
        for f in files:  # EOF report 后写覆盖前写(同 instance 以后到为准)
            d = json.loads(f.read_text(encoding="utf-8"))
            for k, s in STAT.items():
                status[arm].update({iid: s for iid in d.get(k, [])})

    preds = {a: {p["instance_id"]: p.get("model_patch") or ""
                 for p in json.loads(f.read_text(encoding="utf-8"))} for a, f in PREDS.items()}

    leak = []
    if gold:
        for iid in tasks:
            g = gold.get(iid) or {}
            stmt_n = norm((g.get("problem_statement") or tasks[iid].get("task_text") or ""))
            hits = [t for t in gold_added_lines(g.get("patch") or "") if norm(t) in stmt_n]
            if hits:
                leak.append({"instance_id": iid, "hit_lines": len(hits), "sample": hits[0][:60]})
    print(f"== 解在题面扫描(30 题,gold {len(gold)}/30):flag {len(leak)}")
    for x in leak:
        print("  ", x["instance_id"], x["hit_lines"], "|", x["sample"])

    want = {"resolved": 2, "unresolved": 1, "error": 2, "empty": 1}
    spot = {}
    for arm in "AB":
        by = {}
        for iid, s in status[arm].items():
            by.setdefault(s, []).append(iid)
        pick = []
        for s, n in want.items():
            pick += sorted(by.get(s, []))[:n]
        spot[arm] = pick[:6]
        print(f"== {arm} 臂抽查 {len(spot[arm])} 题:", spot[arm])
        for iid in spot[arm]:
            p = preds[arm].get(iid, "")
            print(f"   {iid:42s} {status[arm][iid]:10s} patch={len(p):5d}ch 尾换行={p.endswith(chr(10))} "
                  f"题面泄漏={'Y' if any(x['instance_id'] == iid for x in leak) else 'N'}")

    (HERE / "spot_check_r1.json").write_text(
        json.dumps({"leak_scan": leak, "spot": spot, "status_map": status,
                    "note": "解在题面=近似子串检测 [推断];抽查=patch 特征 vs report 桶一致性"},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("written spot_check_r1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
