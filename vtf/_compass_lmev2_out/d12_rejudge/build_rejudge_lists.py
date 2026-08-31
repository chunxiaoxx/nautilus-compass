"""d12 基线 451 题全量重判清单构造(d14 口径双侧对齐)。

背景:d14 judge 换 low/16384 后,d12 基线(0.367/0.403,medium/4096 口径,含
同样的 reasoning 压 0 偏置)必须同口径重判——单边换口径 = 两把尺子 = d14
口径性虚高假过门风险。判据锚数值以重判版为准,判据结构不变
(详见 d14_PREREGISTERED_CRITERIA.md 执行口径更正段)。

从 d12 per_question.jsonl(web 240 + ent 211)提取重判所需字段,
输出 schema 与 d13 重判清单完全一致,重判脚本复用 d13 逻辑。
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
D12 = HERE.parent / "d12"
RESCUED = HERE.parent / "d13" / "rescued_upstream"

FIELDS = [
    "question_id",
    "eval_function",
    "question_text",
    "answer_gold",
    "response_raw",
    "response_parsed_boxed",
    "score",
]


def build(domain: str, subdir: str) -> tuple[list[dict], int, int]:
    """只提取 LLM checker 题(mc_choice_match 等确定性判定不受 judge 口径影响,保持原分)。"""
    rows, mc_kept, llm_rows = [], 0, 0
    with (D12 / subdir / "per_question.jsonl").open(encoding="utf-8") as fin:
        for line in fin:
            if not line.strip():
                continue
            r = json.loads(line)
            if not r["eval_function"].startswith("llm_"):
                mc_kept += 1
                continue
            llm_rows += 1
            out = {k: r[k] for k in FIELDS}
            out["domain"] = domain
            out["d12_score"] = r.get("score")
            rows.append(out)
    return rows, mc_kept, llm_rows


def main() -> int:
    for domain, subdir in [("ent", "compass_enterprise_small"), ("web", "compass_web_small")]:
        rows, mc_kept, _ = build(domain, subdir)
        out_path = HERE / f"{domain}_rejudge_list.jsonl"
        with out_path.open("w", encoding="utf-8") as fout:
            for r in rows:
                fout.write(json.dumps(r, ensure_ascii=False) + "\n")
        scores = [r["d12_score"] for r in rows]
        mean = sum(scores) / len(scores) if scores else 0
        print(f"{domain}: llm_checkers={len(rows)} (mc_kept_at_orig={mc_kept}) -> {out_path.name}  llm_subset_d12_mean={mean:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
