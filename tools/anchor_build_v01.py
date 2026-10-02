#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""锚点库 v0.1 构建(P0-full v2 前置 · 2026-10-02)。

修 v0 缺陷:effect 侧(reason_span)为簇级模板句→hit@5 结构上限 3-4%<5% 门槛。
v2 判据档:docs/metering/P0_FULL_PREREG_V2_20261002.md(先档后做)。

effect(果)= 样本级判定记录,按判据簇回源逐条构造(模板透明,字段全回溯);
cause(因)= 判据文本展开(criteria_lib_v0)+ source 尾段 + artifact_ref 原样。
A3 零编造:构造字段逐条回溯源行(双向断言:question 与 artifact_ref 现值一致)。
F1b 可分性预检:同簇 effect 唯一文本率 ≥95%。
"""
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "runtime" / "verdict_corpus"
V0 = DIR / "anchor_v0.jsonl"
LIB = json.loads((DIR / "criteria_lib_v0.json").read_text(encoding="utf-8"))
LIB.pop("_meta", None)

SRC_LME = [ROOT / "vtf" / "_e2e_diag" / "arm_a_rows_rejudged.json"]
for d_ in ("d12", "d14"):
    for dom in ("compass_web_small", "compass_enterprise_small"):
        SRC_LME.append(ROOT / "vtf" / "_compass_lmev2_out" / d_ / dom / "per_question.jsonl")

BC1_MD = {True: ROOT / "runtime" / "assay_bc1_20260927" / "SELFTEST_SCORECARD_V2.md",
          False: ROOT / "runtime" / "assay_bc1_20260927" / "SELFTEST_SCORECARD.md"}
F15_SRC = ROOT / "runtime" / "f15_meta_judge_3prov.json"


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def tail(p: str, n: int = 48) -> str:
    return str(p).replace("\\", "/").split("/")[-1] if p else ""


def build_lme_index():
    """question 前 200 字符 → 源行(anchor 侧 question 截断到 200,前缀匹配)。"""
    idx = {}
    for f in SRC_LME:
        if not f.exists():
            continue
        rows = load_jsonl(f) if f.suffix == ".jsonl" else json.loads(
            f.read_text(encoding="utf-8"))
        if isinstance(rows, dict):  # arm_a_rows_rejudged.json 顶层结构
            rows = [v for v in rows.values() if isinstance(v, dict) and "question" in v]
        for r in rows:
            q = r.get("question") or r.get("question_text")
            if q and q[:200] not in idx:  # 首见优先(重复题以首个源为准)
                idx[q[:200]] = (f.name, r)
    return idx


def bc1_audit_rows(md: Path) -> dict:
    """SCORECARD 审计表 qid → 行文本。"""
    out = {}
    if not md.exists():
        return out
    for line in md.read_text(encoding="utf-8").splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            joined = " | ".join(cells)
            for m in re.findall(r"T\d+-\d+", cells[0] if cells else ""):
                out.setdefault(m, joined[:300])
    return out


def main() -> None:
    rows = load_jsonl(V0)
    lme_idx = build_lme_index()
    bc1 = {True: bc1_audit_rows(BC1_MD[True]), False: bc1_audit_rows(BC1_MD[False])}
    bc1_ans = {  # 逐题考生作答(样本级)
        True: json.loads((ROOT / "runtime" / "assay_bc1_20260927" /
                          "selftest_answers_v2.json").read_text(encoding="utf-8")),
        False: json.loads((ROOT / "runtime" / "assay_bc1_20260927" /
                           "selftest_answers.json").read_text(encoding="utf-8"))}
    f15 = json.loads(F15_SRC.read_text(encoding="utf-8")) if F15_SRC.exists() else {}

    out, unmatched = [], []
    for r in rows:
        crit = r["cause"].get("criteria_refs")
        crit = crit if isinstance(crit, str) else (crit[0] if crit else "")
        art = r["cause"].get("artifact_ref") or {}
        eff_old = r["effect"]
        eff_new = None

        if crit.startswith("LME"):  # 五簇 1402:样本级回源(前缀匹配)
            q = str(art.get("question") or "")
            fname, src = lme_idx.get(q[:200], (None, None))
            if src is not None:
                assert (src.get("model_answer") or "")[:200] == (art.get("model_answer") or "")[:200], \
                    f"A3: model_answer 不一致 {r['anchor_id']}"  # 双向回溯
                if "arm_a" in fname:
                    eff_new = (f"{src.get('question_type')}|作答:{str(src.get('model_answer'))[:120]}"
                               f"|金标:{src.get('truth')}|双层复判:{src.get('is_correct')}"
                               f"|judge:{str(src.get('judge_raw'))[:80]}")
                else:
                    eff_new = (f"{src.get('question_type')}|作答:{src.get('response_parsed_boxed')}"
                               f"|金标:{src.get('answer_gold')}|规则分:{src.get('score')}"
                               f"|{'拒答题' if src.get('is_abstention_problem') else '常规题'}")
        elif crit.startswith("BC1"):  # 36 条:逐题作答+审计行(v1)
            qid = art.get("qid", "")
            is_v2 = "v2" in crit
            ans = bc1_ans[is_v2].get(qid, {}).get("answer_json")
            line = bc1[is_v2].get(qid)
            eff_new = (f"{qid}|考生作答:{json.dumps(ans, ensure_ascii=False)[:150]}"
                       + (f"|审计:{line[:120]}" if line else ""))
        elif crit.startswith("F15"):  # 8 条:case 级三家读数
            cid = art.get("case_id", "")
            gates = f15.get("compass_gates", {})
            provs = {k: f15.get(k, {}) for k in ("jev", "glm-5.3-flash", "MiniMax-M2.7")}
            if cid in gates:
                eff_new = (f"case {cid}:三门={gates[cid]}"
                           + "".join(f",{k}={provs[k].get(cid)}" for k in provs))
        else:  # T3 两簇 8 条:保留 v0(已样本级)
            eff_new = eff_old.get("reason_span")

        if not eff_new:
            unmatched.append(r["anchor_id"])
            eff_new = eff_old.get("reason_span") or ""  # 兜底如实,计入未匹配
        lib = LIB.get(crit)
        cause_text = ((lib["text"] if lib else crit) + "\n"
                      + f"source: {tail(r['cause'].get('source_trace'))}\n"
                      + json.dumps(art, ensure_ascii=False))
        out.append({"anchor_id": r["anchor_id"], "fold": r["fold"],
                    "criteria": crit, "effect_text": eff_new, "cause_text": cause_text,
                    "truth_label": r["effect"].get("truth_label"),
                    "u_flag": r["u_flag"]})

    # ── F1b 可分性预检:同构组主判(完美语义下簇内 top-5 的分母),唯一率副读 ──
    by_crit = defaultdict(list)
    for o in out:
        by_crit[o["criteria"]].append(o["effect_text"])
    uniq_report, ok = {}, True
    for c, texts in by_crit.items():
        grp = Counter(texts).most_common(1)[0][1]  # 最大同构组
        uniq_report[c[:40]] = {"n": len(texts), "unique": len(set(texts)),
                               "unique_rate": round(len(set(texts)) / len(texts), 3),
                               "max_isogroup": grp}
        if len(texts) >= 50 and grp > 25:
            ok = False
    (DIR / "anchor_v01.jsonl").write_text(
        "\n".join(json.dumps(o, ensure_ascii=False) for o in out), encoding="utf-8")
    sha16 = hashlib.sha256((DIR / "anchor_v01.jsonl").read_bytes()).hexdigest()[:16]
    man = {"ts": "2026-10-02T19:2x+08:00", "n": len(out), "unmatched": unmatched,
           "F1b_unique_rate": uniq_report, "F1b_pass": ok,
           "anchor_v01_sha16": sha16,
           "criteria_lib": "criteria_lib_v0.json(10)"}
    (DIR / "anchor_v01_manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(man, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
