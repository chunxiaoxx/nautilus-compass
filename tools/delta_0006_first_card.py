#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""delta_0006 首卡判例入池生成器(2026-10-09 · 判读岗 SOP 第⑥步入册首例)。

判读卡 nautilus-l1-0002(S6 首卡,72fdcb66 平台自检单)升格为结构化 delta
registry 条目。truth_label=判读流程先例语义(零新判定):按预注册判据对
无评测产物提交正确出 insufficient_evidence 判定——管线首例+平台独立复现
通过(#10727)即第三方复算门首例 PASS。判据零放宽。
输出:runtime/verdict_corpus/delta/delta_0006.jsonl(+manifest)
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runtime/verdict_corpus/delta/delta_0006.jsonl"
EXPORTED = "2026-10-09"


def build_case() -> dict:
    return {
        "id": "nautilus_l1_0002_first_card",
        "exported_at": EXPORTED,
        "source": "判读卡 nautilus-l1-0002(S6 首卡:72fdcb66 平台自检单 #10713 派单→delivered,平台独立复现通过 #10727;PR 前预检与验收口径同链)",
        "criteria_ref": "判据档 docs/metering/L3_HARNESS_BOARD_ROUND1_PREREG_20261005.md sha16=5c8e0a7ce3a0048b(LF 口径;API 历史锚 b81eca84 工作树口径,双口径注见 .gitattributes 固化记录)",
        "artifact": {
            "qid": "nautilus-l1-0002",
            "artifact_ref": "GET https://nautilus.social/api/judge_status?id=nautilus-l1-0002(criteria_sha16 随卡 live)",
            "original_verdict": "insufficient_evidence——[实测] repo=anthropics/claude-code HTTP 200(149820 stars)/version_anchor=1.0.0 npm 口径可锚(git tag 无,披露);[实测缺失] 任务集读数(SWE-bench Verified resolved%)=零/评测产物=零/模型配置与采样参数=零",
            "domain": "judge_pipeline",
            "claims": [
                "无评测产物的提交按预注册判据出 insufficient_evidence,不进名次区亦不进观察区",
                "处置=不予收录,可携评测产物重提走正常判读(管线验证目标与真实评测需求分离)",
                "criteria_sha16 随卡 live=首张带 sha 真卡(S6 尾环闭环)",
            ],
        },
        "original_judgment": {
            "verdict": "insufficient_evidence",
            "judge_reason": "单据自述『平台自检单,非真实评测需求』与证据状态一致;无可判读评测读数;判读五步含 metadata_check(本单新增步)",
            "issued_at": "2026-10-08T16:45+08",
        },
        "recompute": {
            "verdict": "平台独立复现通过(#10727:verdict/sha16/steps 逐项命中)——第三方复算门首例 PASS;关单 5 件+72fdcb66 回写 delivered",
            "by": "platform",
            "at": "2026-10-08",
        },
        "truth_label": "pass",
        "label_origin": "first_card_delivered",
        "reason": "判读流程先例:对无产物自检单按预注册判据正确出 IE 判定,不予收录可重提;delivered→复现→关单全链走通(判读管线信用首例)",
        "domain": "judge_pipeline",
        "fuel_eligible": True,
    }


def main() -> int:
    case = build_case()
    body = json.dumps(case, ensure_ascii=False, sort_keys=True).encode("utf-8")
    case["content_hash16"] = hashlib.sha256(body).hexdigest()[:16]
    OUT.write_text(json.dumps(case, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = {
        "delta": "0006",
        "exported_at": EXPORTED,
        "records": 1,
        "generator": "tools/delta_0006_first_card.py",
        "source_chain": ["#10713 派单", "#10723 delivered 回函", "#10727 平台复现通过"],
        "note": "判读岗 SOP 第⑥步入册首例;truth_label=判读流程先例语义(零新判定)",
    }
    OUT.with_name("manifest_delta_0006.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"delta_0006: 1 case -> {OUT.name} (hash={case['content_hash16']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
