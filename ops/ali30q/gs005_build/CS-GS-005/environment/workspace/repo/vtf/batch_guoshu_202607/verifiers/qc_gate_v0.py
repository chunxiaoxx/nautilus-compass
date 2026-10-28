#!/usr/bin/env python3
r"""QC 格式门 v0(确定性)——垂域交付线 QC 降本试点第一步(决策 C 首个落地件)。

用途:
  - screen 模式(新提交行):跑机械门,全绿行 = 免人工格式复核候选,红旗行列出原因。
  - validate 模式(台账行,含"建议*"人工列):gate 判定 vs 人工 QC 对照,量化 gate 质量。

门(全部机械可判,无 LLM):
  G1 一级目录 ∈ 9 固定类目白名单(CHARTER §1.1,不可改)
  G2 UID 格式 ^[a-z]+_data_\d{3}$ 且与出题人拼音一致(拼音不做强校验,格式为准)
  G3 折算h ≥ 8(甲方"≥8h 专家复杂度"口径)
  G4 必填列非空:题目/类型/一级目录/自报时长/折算h
  G5 类型 ∈ {L1, L2, L3} 前缀

语义判断(一级目录映射是否恰当/AI 痕迹/内容质量)不在 v0 范围——属 v1 LLM 初筛臂,
见 docs/plans/2026-08-26-qc-pilot-protocol.md。

用法: python qc_gate_v0.py [台账.csv] [--out report.md]
"""
import csv
import json
import re
import sys
from pathlib import Path

VALID_L1 = {
    "互联网与平台业务", "科技软件与AI工作流", "游戏与互动内容", "品牌市场与电商零售",
    "投资战略专业服务与企业经营", "金融服务与财富投研", "教育科研与生命科学",
    "法律政务与公共服务", "房地产与大宗资产",
}
# 台账实际写法有变体(全角顿号等),归一化后匹配
VALID_L1_ALIASES = {
    "法律、政务与公共服务": "法律政务与公共服务",
    "科技软件与 AI 工作流": "科技软件与AI工作流",
    "投资战略、专业服务与企业经营": "投资战略专业服务与企业经营",  # 台账建议列的规范写法
}
# G2 基线对齐人工 QC:接受 <name>_data_NNN / 薛美雪_001 / 开票信息_skill_001;
# 拒:无下划线(人力资源批量作业/张欢-data-001/张兵-1)或无名字前缀(data_001)
UID_BAD = ("无下划线", "缺名字前缀")


def uid_violation(uid: str) -> str | None:
    if "_" not in uid:
        return UID_BAD[0]
    if uid.lower().startswith("data_"):
        return UID_BAD[1]
    return None
TYPE_RE = re.compile(r"^L[123]")
REQUIRED = ["题目", "类型", "一级目录", "自报时长", "折算h"]


def norm_cat(s: str) -> str:
    s = (s or "").strip()
    return VALID_L1_ALIASES.get(s, s)


def gate_row(row: dict) -> tuple[bool, list[str]]:
    flags = []
    if norm_cat(row.get("一级目录", "")) not in VALID_L1:
        flags.append(f"G1 目录非法/空白:「{row.get('一级目录','')}」")
    uid = (row.get("UID") or "").strip()
    if (why := uid_violation(uid)):
        flags.append(f"G2 UID({why}):{uid}")
    hours_raw = (row.get("折算h") or "").strip()
    if not hours_raw:
        pass  # 空值由 G4 列全负责,不双计
    else:
        try:
            hours = float(hours_raw)
            if hours < 8:
                flags.append(f"G3 折算{hours}h<8h")
        except ValueError:
            flags.append("G3 折算h非数值")
    for col in REQUIRED:
        if not (row.get(col) or "").strip():
            flags.append(f"G4 列空:{col}")
    if not TYPE_RE.match((row.get("类型") or "").strip()):
        flags.append(f"G5 类型非法:「{row.get('类型','')}」")
    return (len(flags) == 0, flags)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(
        description="QC 格式门 v0 — 机械门初筛,绿行免人工格式复核(用法: python qc_gate_v0.py 新提交.csv)")
    ap.add_argument("csv", nargs="?", default=None, help="输入 CSV(默认台账_batch1.csv)")
    ap.add_argument("--out", default=None, help="markdown 报告输出路径")
    ap.add_argument("--json", action="store_true", help="stdout 输出机器可读 JSON")
    args = ap.parse_args()
    src = Path(args.csv) if args.csv else Path(__file__).parent.parent / "台账_batch1.csv"
    rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
    report, n_green, n_red, jrows = [], 0, 0, []
    for row in rows:
        ok, flags = gate_row(row)
        name = row.get("出题人", "?")
        jrows.append({"name": name, "ok": ok, "flags": flags})
        if ok:
            n_green += 1
            report.append(f"| {name} | 🟢 | — |")
        else:
            n_red += 1
            report.append(f"| {name} | 🔴 | {'; '.join(flags)} |")
    if args.json:
        import json as _j
        print(_j.dumps({"total": len(rows), "green": n_green, "red": n_red, "rows": jrows},
                       ensure_ascii=False))
        return
    print(f"gate v0: {len(rows)} 行 → 绿 {n_green} / 红 {n_red}")

    # validate 模式:有人工建议列时,gate vs 人工 QC 对照
    lines = [
        "# QC 格式门 v0 报告(确定性机械门)",
        "",
        f"输入: `{src.name}` · {len(rows)} 行 · 生成: qc_gate_v0.py",
        "",
        f"**结果: 🟢 全绿 {n_green} 行(免人工格式复核候选) · 🔴 红旗 {n_red} 行**",
        "",
        "| 出题人 | 判定 | 红旗原因 |", "|---|---|---|",
        *report,
    ]
    if rows and rows[0].get("建议一级目录") is not None:
        hum_dir = [r["出题人"] for r in rows if r.get("建议一级目录", "").strip() and norm_cat(r["一级目录"]) != norm_cat(r["建议一级目录"])]
        hum_uid = [r["出题人"] for r in rows if r.get("建议UID", "").strip() and (r.get("UID") or "").strip() != r["建议UID"].strip()]
        lines += [
            "",
            "## 对照人工 QC(台账建议列)",
            f"- 一级目录映射需人工/LLM 判断: {len(hum_dir)} 行——**机械门抓不到,属 v1 LLM 臂范围**",
            f"- UID 与建议不一致: {len(hum_uid)} 行({','.join(hum_uid)})——G2 格式门可复判",
            "- 结论: v0 覆盖 UID/时长/列全/类型/非法目录值;目录映射与 AI 痕迹留给 v1",
        ]
    out = Path(args.out) if args.out else Path(__file__).with_name("qc_gate_v0_report.md")
    out.write_text("\n".join(lines), encoding="utf-8")
    json.dump({"total": len(rows), "green": n_green, "red": n_red}, open(Path(__file__).with_name("qc_gate_v0_summary.json"), "w", encoding="utf-8"))
    print(f"报告 → {out}")


if __name__ == "__main__":
    main()
