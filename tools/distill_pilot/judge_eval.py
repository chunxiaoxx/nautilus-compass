#!/usr/bin/env python3
"""D3 评器:J3 机械实体召回 + J2 大模型盲评幻觉率。

J3(机械,无 LLM): 源文去重锚点(非CJK路径/日期/编号)在纪要【总纪要段】中的覆盖率 → 实体召回。
J2(LLM 盲评): glm-5.3 审"纪要总纪要 vs 脱敏源文",逐条实质陈述判支持性 → unsupported/claims。
用法:
  judge_eval.py j3 --out DIR                     # 全量本地臂(可加 --ref 也算参考臂)
  judge_eval.py j2 --out DIR --ids id1,id2 ...   # 盲评指定会话(两臂都评)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from anchor_check import CJK_RE, collect_anchors  # noqa: E402
from compress_arm import scrub  # noqa: E402
from ref_arm import chat_anthropic  # noqa: E402

FINAL_SPLIT = "## 附"

JUDGE_SYSTEM = (
    "你是独立审计员。给你一份【源文】与一份【纪要】,只依据源文审查纪要总纪要部分的实质陈述"
    "(事实/数字/路径/因果/结论)。输出严格 JSON(不要其他文字):"
    '{"claims": <纪要实质陈述总条数>, "unsupported": <源文中找不到支持的条数>,'
    ' "unsupported_list": [<最多10条原文摘录>]}。'
    "只判断'源文是否支持',不判断陈述本身对错;纪要未提及的源文内容不算 unsupported。"
)


def final_section(text: str) -> str:
    return text.split(FINAL_SPLIT)[0]


def j3_one(summary_text: str, source_text: str) -> dict:
    src_anchors = {
        a["value"]
        for a in collect_anchors(source_text)
        if a["type"] in ("path", "date", "tag_id", "url") and not CJK_RE.search(a["value"])
    }
    if not src_anchors:
        return {"n_entities": 0, "recall": None}
    final = final_section(summary_text)
    hit = sum(1 for v in src_anchors if v in final)
    return {"n_entities": len(src_anchors), "n_covered": hit, "recall": round(hit / len(src_anchors), 4)}


def cmd_j3(args: argparse.Namespace) -> None:
    out = Path(args.out).expanduser()
    arms = {"local": out / "summaries_local"}
    if args.ref:
        arms["ref"] = out / "summaries_ref"
    report: dict = {}
    for arm, folder in arms.items():
        rows = {}
        for md in sorted(folder.glob("*.md")):
            src = out / "extracted" / f"{md.stem}.txt"
            if not src.exists():
                continue
            rows[md.stem[:8]] = j3_one(
                md.read_text(encoding="utf-8", errors="replace"),
                src.read_text(encoding="utf-8", errors="replace"),
            )
        rates = [r["recall"] for r in rows.values() if r["recall"] is not None]
        report[arm] = {
            "n": len(rows),
            "mean_recall": round(sum(rates) / len(rates), 4) if rates else None,
            "below_90": sum(1 for x in rates if x < 0.90),
            "worst3": sorted([(v["recall"], k) for k, v in rows.items() if v["recall"] is not None])[:3],
            "per_session": rows,
        }
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "per_session"} for k, v in report.items()}, ensure_ascii=False, indent=1))
    json.dump(report, open(out / "j3_results.json", "w"), ensure_ascii=False, indent=1)


def j2_one(summ_id: str, arm_folder: Path, out: Path, key: str, model: str, base_url: str | None = None) -> dict:
    md = next(arm_folder.glob(f"{summ_id}*.md"))
    src = out / "extracted" / f"{md.stem}.txt"
    final = final_section(md.read_text(encoding="utf-8", errors="replace"))
    user = f"【源文】\n{scrub(src.read_text(encoding='utf-8', errors='replace'))[:140000]}\n\n【纪要】\n{final}"
    raw = chat_anthropic(JUDGE_SYSTEM, user, key, model, 1500, base_url=base_url)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return {"session": summ_id[:8], "parse_fail": raw[:120]}
    try:
        d = json.loads(m.group(0))
        rate = round(d["unsupported"] / d["claims"], 4) if d.get("claims") else None
        return {"session": summ_id[:8], "claims": d.get("claims"), "unsupported": d.get("unsupported"), "j2_rate": rate}
    except (json.JSONDecodeError, KeyError, ZeroDivisionError) as exc:
        return {"session": summ_id[:8], "parse_fail": f"{exc}: {raw[:120]}"}


def cmd_j2(args: argparse.Namespace) -> None:
    out = Path(args.out).expanduser()
    key = os.environ.get("COMPASS_WRITER_KEY", "")
    base_url = os.environ.get("JUDGE_BASE_URL") or None
    if not key:
        print("缺 COMPASS_WRITER_KEY(或判官 key)", file=sys.stderr)
        sys.exit(2)
    results = {"local": [], "ref": []}
    for sid in [x for x in args.ids.split(",") if x]:
        for arm, folder in (("local", out / args.local_dir), ("ref", out / "summaries_ref")):
            if not list(folder.glob(f"{sid}*.md")):
                continue
            try:
                r = j2_one(sid, folder, out, key, args.model, base_url=base_url)
            except RuntimeError as exc:
                r = {"session": sid[:8], "error": str(exc)[:150]}
                time.sleep(3)
            results[arm].append(r)
            print(f"[j2/{arm}] {r}", file=sys.stderr)
    for arm in results:
        rates = [r["j2_rate"] for r in results[arm] if r.get("j2_rate") is not None]
        if rates:
            print(f"{arm}({args.local_dir if arm=='local' else 'ref'}): mean_j2={round(sum(rates)/len(rates),4)} n={len(rates)}", file=sys.stderr)
    json.dump(results, open(out / f"j2_results_{args.tag}.json", "w"), ensure_ascii=False, indent=1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p3 = sub.add_parser("j3")
    p3.add_argument("--out", required=True)
    p3.add_argument("--ref", action="store_true")
    p3.set_defaults(func=cmd_j3)
    p2 = sub.add_parser("j2")
    p2.add_argument("--out", required=True)
    p2.add_argument("--ids", required=True)
    p2.add_argument("--model", default="glm-5.3")
    p2.add_argument("--local-dir", default="summaries_local")
    p2.add_argument("--tag", default="v1")
    p2.set_defaults(func=cmd_j2)
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
