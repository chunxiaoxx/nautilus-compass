#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""delta_0005 判例集 v1.4 入池生成器(2026-10-08 · 7B 语料第三段)。

docs/cases/CASEBOOK_V1.md(16 案,v1.4 封版即 10/12 榜页挂墙版)→ 结构化
delta registry 条目。truth_label 逐案映射自判例正文终判短语(见 LABEL_EVIDENCE,
零新判定);其余字段解析自正文(背景/判据/材料锚/verdict 正本/复算)。
输出:runtime/verdict_corpus/delta/delta_0005.jsonl + manifest
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs/cases/CASEBOOK_V1.md"
OUT = ROOT / "runtime/verdict_corpus/delta/delta_0005.jsonl"
EXPORTED = "2026-10-08"

# truth_label 映射:value=正文终判依据短语(零新判定,逐条可溯)
LABELS = {
    1: ("pass", "材料双臂合格,门槛裁断留预注册语义实验"),
    2: ("fail", '"方向稳健可判"不成立;U 态维持'),
    3: ("pass", "方向支持修复有效(欠幅减轻 0.63 vs 0.39)"),
    4: ("fail", "大半系抽样混杂坐实(效应量 +0.0627 vs 未配对 +0.24)"),
    5: ("insufficient_evidence", "地板效应 0/20 判不动,U 态"),
    6: ("pass", "coverage 连续主判显著(配对 Wilcoxon p=0.00181)"),
    7: ("pass", "判据演进 v1→v2-final 全链审定(T1/T2)"),
    8: ("pass", "燃料入池判据三连裁(口径裁定合订)"),
    9: ("insufficient_evidence", "verdict=PARTIAL"),
    10: ("insufficient_evidence", "verdict=PARTIAL"),
    11: ("insufficient_evidence", "verdict=PARTIAL"),
    12: ("pass", "established(J2 升格后判定主权第 2 演)"),
    13: ("pass", "归因制式 v1 首件回填+非实现者复算闭环"),
    14: ("fail", "+5pp 门槛未过,未证实分支成立(负结果照报)"),
    15: ("pass", "self-reported→measured upgrade 闭环首例"),
    16: ("pass", "Round1 定版 A 26.7%/B 16.7%(+10.0pp),勘误第 6 例入账"),
}

DOMAINS = {  # 案号→domain(源自案题语境)
    1: "embodied_data_judgment", 2: "embodied_data_judgment",
    3: "embodied_data_judgment", 4: "embodied_data_judgment",
    5: "embodied_data_judgment", 6: "embodied_data_judgment",
    7: "criteria_evolution", 8: "criteria_evolution",
    9: "agent_track_judgment", 10: "agent_track_judgment",
    11: "embodied_data_judgment", 12: "embodied_data_judgment",
    13: "embodied_data_judgment", 14: "embodied_data_judgment",
    15: "embodied_data_judgment", 16: "harness_board_judgment",
}


def field(block: str, name: str) -> str:
    m = re.search(rf"- \*\*{name}\*\*[::]?\s*(.{{0,600}})", block, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def main():
    text = SRC.read_text(encoding="utf-8")
    cases = []
    for block in re.split(r"\n(?=## 案 \d+)", text):
        m = re.match(r"## 案 (\d+)[ ·]*(.+)", block)
        if not m:
            continue
        n, title = int(m.group(1)), m.group(2).strip()
        label, evidence = LABELS[n]
        body = {
            "id": f"casebook_v14_case{n:02d}",
            "exported_at": EXPORTED,
            "source": f"docs/cases/CASEBOOK_V1.md 案 {n}({title})",
            "criteria_ref": field(block, "判据")[:300] or "(见正文,过程/裁定案)",
            "artifact": {
                "qid": f"casebook-v14-c{n:02d}",
                "artifact_ref": field(block, "材料锚")[:200] or field(block, "背景")[:200],
                "original_verdict": title,
                "domain": DOMAINS[n],
                "fuel_eligible": True,
            },
            "judge_output": {
                "recompute_verdict": evidence,
                "judge_reason": field(block, "claims")[:300] or field(block, "判读")[:300],
            },
            "truth_label": label,
            "label_origin": "casebook_v1_4_final_verdict",
            "reason": f"判例集 v1.4 封版案;标签映射自正文终判短语:«{evidence}»;复算:{field(block, '复算')[:150]}",
        }
        body["content_hash"] = hashlib.sha256(
            json.dumps(body, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()[:16]
        cases.append(body)

    # qid 防撞
    existing = set()
    for f in ("split_train_v1", "split_dev_v1", "split_test_v1"):
        for l in (ROOT / f"runtime/verdict_corpus/{f}.jsonl").read_text(encoding="utf-8").splitlines():
            if l.strip():
                existing.add(json.loads(l).get("qid") or "")
    for f in sorted((ROOT / "runtime/verdict_corpus/delta").glob("delta_*.jsonl")):
        for l in f.read_text(encoding="utf-8").splitlines():
            if l.strip():
                existing.add((json.loads(l).get("artifact") or {}).get("qid") or "")
    clash = [c["id"] for c in cases if c["artifact"]["qid"] in existing]
    if clash:
        raise SystemExit(f"qid 撞池: {clash}")

    OUT.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cases) + "\n",
                   encoding="utf-8")
    from collections import Counter
    by = Counter(c["truth_label"] for c in cases)
    manifest = {
        "delta": "delta_0005.jsonl",
        "exported_at": EXPORTED,
        "n_cases": len(cases),
        "by_label": dict(by),
        "label_origin": "casebook_v1_4_final_verdict",
        "source": "docs/cases/CASEBOOK_V1.md(v1.4 封版,10/12 榜页挂墙版)",
        "note": "判例集 16 案入池;标签=正文终判短语映射,零新判定;判据零放宽",
    }
    (ROOT / "runtime/verdict_corpus/delta/manifest_delta_0005.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"delta_0005: {len(cases)} cases | {dict(by)}")


if __name__ == "__main__":
    main()
