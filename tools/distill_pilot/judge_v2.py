#!/usr/bin/env python3
"""D5-B: 判官协议 v2——声明级拆解+双判官+温度 0,重造 J2 仪器。

与 v1(整段打分,已证仪器失效:同判官两轮差 9.5pt)的区别:
  1. 声明级: 判官先把纪要拆成原子声明,逐条给"支持引用(源文≥10字原文)"或"无支持";
  2. 幻觉判定机械化: 有引用即支持(引用须与源文逐字匹配,程序复核),无引用即无支持——判官只做拆解与引用,不做"算不算支持"的自由裁量;
  3. 双判官(glm+kimi)独立跑,报告按声明交集/并集两种口径;
  4. temperature=0。
用法: judge_v2.py --out DIR --ids id1,... --arm-dir summaries_9b [--tag x]
环境: COMPASS_WRITER_KEY(glm)/JUDGE2_KEY+JUDGE2_BASE_URL+JUDGE2_MODEL(kimi)
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
from compress_arm import scrub  # noqa: E402
from ref_arm import chat_anthropic  # noqa: E402

JUDGE_V2_SYSTEM = (
    "你是审计员。把【纪要】拆成原子声明(每条一个可独立核查的事实/数字/路径/因果),"
    "并对每条在【源文】中找出逐字支持引用(≥10个连续字符,原样复制),找不到就标无支持。"
    "只输出严格 JSON 数组(不要其他文字):"
    '\n[{"claim": "...", "quote": "源文逐字引用或空串"}]'
    "\n规则: 引用必须与源文逐字一致;找不到逐字引用=quote 空串;不判断对错只找支持;最多 40 条,挑实质声明。"
)


def run_judge(final: str, source: str, key: str, model: str, base_url: str | None) -> list[dict]:
    user = f"【源文】\n{source[:120000]}\n\n【纪要】\n{final}"
    raw = chat_anthropic(JUDGE_V2_SYSTEM, user, key, model, 16000, base_url=base_url, temperature=0.0)
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        raise RuntimeError(f"no-json: {raw[:100]}")
    claims = json.loads(m.group(0))
    # 机械复核: quote 逐字在源文中才算支持
    for c in claims:
        q = (c.get("quote") or "").strip()
        c["supported"] = bool(q) and q in source
        c["quote_ok_len"] = len(q)
    return claims


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--ids", required=True)
    parser.add_argument("--arm-dir", default="summaries_9b")
    parser.add_argument("--tag", default="v2")
    args = parser.parse_args()

    out = Path(args.out).expanduser()
    glm_key = os.environ.get("COMPASS_WRITER_KEY", "")
    kimi_key = os.environ.get("JUDGE2_KEY", "")
    judges = {}
    if glm_key and not os.environ.get("JUDGE_SKIP_GLM"):
        judges["glm"] = (glm_key, "glm-5.3", None)
    if kimi_key:
        judges["kimi"] = (kimi_key, os.environ.get("JUDGE2_MODEL", "kimi-k2-turbo-preview"),
                          os.environ.get("JUDGE2_BASE_URL"))
    if not judges:
        print("无判官可用(需 COMPASS_WRITER_KEY 或 JUDGE2_KEY)", file=sys.stderr)
        return 1
    results = []
    for sid in [x for x in args.ids.split(",") if x]:
        md = next((out / args.arm_dir).glob(f"{sid}*.md"), None)
        if not md:
            continue
        final = md.read_text(encoding="utf-8", errors="replace").split("## 附")[0]
        source = scrub((out / "extracted" / f"{md.stem}.txt").read_text(encoding="utf-8", errors="replace"))
        row = {"session": sid[:8], "judges": {}}
        for jname, (key, model, base) in judges.items():
            try:
                claims = run_judge(final, source, key, model, base)
                n = len(claims)
                sup = sum(1 for c in claims if c["supported"])
                row["judges"][jname] = {"n_claims": n, "supported": sup,
                                        "j2_rate": round(1 - sup / n, 4) if n else None,
                                        "claims": claims}
            except RuntimeError as exc:
                row["judges"][jname] = {"error": str(exc)[:120]}
            time.sleep(2)
        results.append(row)
        print(f"[j2v2] {row['session']}: " + " ".join(
            f"{k}={v.get('j2_rate','ERR')}" for k, v in row["judges"].items()), file=sys.stderr)
    json.dump(results, open(out / f"j2v2_{args.tag}.json", "w"), ensure_ascii=False, indent=1)
    for jname in ("glm", "kimi"):
        rates = [r["judges"][jname]["j2_rate"] for r in results
                 if jname in r["judges"] and r["judges"][jname].get("j2_rate") is not None]
        if rates:
            print(f"{jname}: mean_j2v2={round(sum(rates)/len(rates),4)} n={len(rates)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
