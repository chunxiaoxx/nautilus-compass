#!/usr/bin/env python3
"""L3 Round 1 双臂全量读数合并器(判分工序预注册 §判分工序兑现件)。

读四份 schema v2 report:
  rest_report_a.json / django_report_a.json / b_rest_report_b.json / b_django_report_b.json
输出:双臂全量三档口径 + 30 题 instance 级配对矩阵 + 镜像 EOF 补跑候选清单。
缺任一 report 时标 pending 不出终数(读数以全量为准,半程不填榜)。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPORTS = {
    "A_rest": HERE / "rest_report_a.json",
    "A_django": HERE / "django_report_a.json",
    "B_rest": HERE / "b_rest_report_b.json",
    "B_django": HERE / "b_django_report_b.json",
}
KEYS = ("resolved_ids", "unresolved_ids", "error_ids", "empty_patch_ids")
# A 臂 2 题镜像 EOF(dockerhub auth token EOF)=评测环境侧,双臂机会不等补跑候选
MIRROR_EOF = {"sympy__sympy-13974", "sphinx-doc__sphinx-8475"}
# 补跑折入后(fold_eof.py):环境层名单以 mirror_eof_final.txt 为准
# (补跑后仍判环境层的题;其余补跑 error 归 patch 格式层;空文件=补跑 error 全格式)
_ov = HERE / "mirror_eof_final.txt"
if _ov.exists():
    MIRROR_EOF = {x.strip() for x in _ov.read_text(encoding="utf-8").splitlines() if x.strip()}


def load_arm(prefix: str) -> tuple[dict, set]:
    merged: dict[str, list] = {k: [] for k in KEYS}
    seen: set = set()
    files = [REPORTS[f"{prefix}_rest"], REPORTS[f"{prefix}_django"]]
    missing = [f.name for f in files if not f.exists()]
    if missing:
        return merged, set()
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        for k in KEYS:
            for iid in d.get(k, []):
                if iid in seen:
                    raise SystemExit(f"DUP {iid} in {f.name}")
                seen.add(iid)
                merged[k].append(iid)
    return merged, seen


def main() -> int:
    pending = [name for name, p in REPORTS.items() if not p.exists()]
    a, a_ids = load_arm("A")
    b, b_ids = load_arm("B")
    ok = not pending and a_ids and b_ids
    n = 30
    print(f"pending={pending or 'none'}")
    for arm, m, ids in (("A", a, a_ids), ("B", b, b_ids)):
        if not ids:
            print(f"{arm} 臂: PENDING(report 缺,不出指标)")
            continue
        assert len(ids) == n, f"{arm} 臂 instance 数 {len(ids)} != {n}"
        r = len(m["resolved_ids"])
        comp = r + len(m["unresolved_ids"])
        # patch 合规率(预注册口径,见 L3_BOARD_PAGE_DRAFT §读数注记):
        # = 非格式 error 题数 / 30;格式 error = error 中剔除 2 题环境镜像 EOF
        fmt_err = [i for i in m["error_ids"] if i not in MIRROR_EOF]
        patch_ok = n - len(fmt_err)
        print(
            f"{arm} 臂: resolved {r}/{n} ({r/n:.1%}) | completed内率 "
            f"{f'{r}/{comp}={r/max(comp,1):.1%}' if comp else 'n/a'} | patch合规 "
            f"{patch_ok}/{n}={patch_ok/n:.1%} (格式error {len(fmt_err)}/环境error "
            f"{len(m['error_ids']) - len(fmt_err)}) | empty_patch {len(m['empty_patch_ids'])}"
        )
    if not ok:
        print("== PENDING:全量 report 未齐,不出终数不填榜 ==")
        return 1
    # 配对矩阵
    both = a_ids & b_ids
    assert len(both) == n, f"双臂 instance 对齐失败 {len(both)}"
    buckets = {"A_only": [], "B_only": [], "both": [], "neither": []}
    for iid in sorted(both):
        ar, br = iid in set(a["resolved_ids"]), iid in set(b["resolved_ids"])
        buckets["both" if ar and br else "A_only" if ar else "B_only" if br else "neither"].append(iid)
    for k, v in buckets.items():
        print(f"resolved {k}: {len(v)} {v[:6]}")
    cand = sorted(
        (set(a["error_ids"]) | set(b["error_ids"])) & MIRROR_EOF
    )
    print(f"镜像 EOF 补跑候选(双臂 error 交集 MIRROR_EOF): {cand}")
    out = {
        "arm_a": {k: len(v) for k, v in a.items()},
        "arm_b": {k: len(v) for k, v in b.items()},
        "pairing": {k: v for k, v in buckets.items()},
        "mirror_eof_rerun": cand,
    }
    (HERE / "round1_merged.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("written round1_merged.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
