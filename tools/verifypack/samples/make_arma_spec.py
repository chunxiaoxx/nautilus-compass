"""A 臂摘要层终判 → VerifyPack v0.2 spec(两线会师①:压缩侧产物首次进仲裁栈)。

口径纪律(2026-09-10 定):
- 0.7540 = 重判后全量 377/500(源:vtf/_e2e_diag/arm_a_rows_rejudged.json)——主 claim
- 0.700  = 保守口径 350/500(源:arm_a_final_verdict_raw.json 分型 ok/n 加总)——conservative claim
- 81.6%(350/429 剔除断连)不可从单文件复算 → 不进 claim(能验的才进包)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "vtf" / "_e2e_diag"
OUT = REPO / "runtime" / "verifypack" / "arma_summary" / "payload"

TYPES = [
    "single-session-user", "single-session-assistant", "single-session-preference",
    "multi-session", "temporal-reasoning", "knowledge-update",
]


def main() -> int:
    rows_src = json.loads((SRC / "arm_a_rows_rejudged.json").read_text(encoding="utf-8"))
    verdict = json.loads((SRC / "arm_a_final_verdict_raw.json").read_text(encoding="utf-8"))

    # 1) payload/rows.json:轻量化行(只留复算必需字段)
    rows = [
        {"qid": qid, "type": r["question_type"], "judge": r["judge_raw"],
         "rc": 1 if r["is_correct"] else 0}
        for qid, r in sorted(rows_src.items(), key=lambda kv: kv[1]["i"])
    ]
    # 2) payload/verdict_by_type.json:分型汇总 → rows 形态(保守口径复算源)
    vrows = [{"type": t, "ok": verdict[t]["ok"], "n": verdict[t]["n"]} for t in TYPES]

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "rows.json").write_text(json.dumps({"rows": rows}, ensure_ascii=False), encoding="utf-8")
    (OUT / "verdict_by_type.json").write_text(json.dumps({"rows": vrows}, ensure_ascii=False), encoding="utf-8")

    # 3) claims(全部从上两文件可复算;数字由本脚本算出,不手填)
    def agg(from_ref, num, den="count()", flt=None):
        primary = {"kind": "aggregate", "from": from_ref, "num": num, "den": den, "op": "ratio_eq"}
        if flt:
            primary["filter"] = flt
        return primary

    overall = sum(r["rc"] for r in rows) / len(rows)
    claims = [{
        "id": "ARMA-OVERALL-500",
        "statement": "A 臂摘要层 e2e 终判,重判后全量(71 断连题已补判,#40 定案)",
        "level": "L1",
        "value": round(overall, 6),
        "checks": {"primary": agg("payload/rows.json#rows", "count(rc == 1)")},
    }]
    for t in TYPES:
        sub = [r for r in rows if r["type"] == t]
        claims.append({
            "id": f"ARMA-TYPE-{t}",
            "statement": f"分型 {t}",
            "level": "L1",
            "value": round(sum(r["rc"] for r in sub) / len(sub), 6),
            "checks": {"primary": agg("payload/rows.json#rows", "count(rc == 1)",
                                      flt=[{"field": "type", "op": "==", "value": t}])},
        })
    cons = sum(v["ok"] for v in vrows) / sum(v["n"] for v in vrows)
    claims.append({
        "id": "ARMA-CONSERVATIVE-70",
        "statement": "保守口径(断连题按错计);81.6% 剔除断连口径不可从包内复算,不进 claim",
        "level": "L1",
        "value": round(cons, 6),
        "checks": {"primary": agg("payload/verdict_by_type.json#rows", "sum(ok)", "sum(n)")},
    })

    spec = {
        "pack": {
            "pack": "arma-summary-e2e-v1",
            "protocol_version": "verifypack-0.2",
            "generated_at": "2026-09-10T09:30:00",
            "requested_by": "nautilus-compass",
            "upstream_protocol": "lme-s-retrieval-e2e-protocol-d12",
            "inputs": [],
            "claims": claims,
        },
        "files": {
            "payload/rows.json": str(OUT / "rows.json"),
            "payload/verdict_by_type.json": str(OUT / "verdict_by_type.json"),
        },
    }
    spec_path = OUT.parent / "spec_arma.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[ok] rows={len(rows)} overall={overall:.4f} conservative={cons:.4f} claims={len(claims)}")
    print(f"[ok] spec -> {spec_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
