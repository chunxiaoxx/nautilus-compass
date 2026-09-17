# -*- coding: utf-8 -*-
"""Assay BC1 出题生成器 v0(2026-09-18 · 程序化参数化,防背题;判据显式引用)。

一道题 = {id, dim, type, statement, criteria_ref, input, expected, check}
check ∈ {json_map_equal, script, aggregate, expr}——直接可编译为 VerifyPack claim。
种子确定性:同 seed 同题集。60/40 hold-out 切分附 manifest(sha256)。

用法:
  python -m tools.assay_items.gen_bc1 --all --seed S --n 每型题数 --out items.jsonl
  python -m tools.assay_items.gen_bc1 --all --seed S --n 5 --out s.jsonl \
      --split 60/40 --split-prefix out_prefix
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

CRIT = {
    "provenance": "external-verified-provenance-v1@catalog-v0",
    "schema": "evidence-schema-v1@catalog-v0",
    "skip": "skip-label-fidelity-v1@catalog-v0",
    "anchorpool": "anchor-pool-selection-bias-v1@catalog-v0",
    "judge": "judge-systematic-inconsistency-v1@catalog-v0",
    "recompute": "verdict-recomputability-v1@catalog-v0",
}


def _t21_gate_rows(rng, n, k):
    """写入门毒写拒收(ev=true 无 verifier=生产者自置,种子=10verdict 案)。"""
    rows, gate = [], {}
    for i in range(n):
        rid = f"R{i:02d}"
        bad = rng.random() < 0.4
        row = {"row_id": rid, "claim": f"claim_{rng.randrange(10**6)}",
               "external_verified": bad, "verifier": None if bad else f"v_{rng.randrange(999)}",
               "has_evidence": rng.random() > 0.2}
        rows.append(row)
        gate[rid] = "reject" if bad else "accept"
    return {"dim": 2, "type": "t2.1-gate-rows",
            "statement": f"写入门判定:以下 {n} 行记忆候选,生产者自置 external_verified "
                         f"(=true 且无 verifier 身份)必须拒收;判每行 accept/reject"
                         f"(锚引用 {CRIT['provenance']})",
            "criteria_ref": CRIT["provenance"],
            "input": {"rows": rows}, "expected": {"gate": gate},
            "check": "json_map_equal"}


def _t22_dedup(rng, n, k):
    rows, dups = [], []
    for i in range(n // 2):
        base = f"fact_{rng.randrange(10**6)}"
        rows += [{"row_id": f"D{i}a", "text": base}, {"row_id": f"D{i}b", "text": base}]
        dups.append([f"D{i}a", f"D{i}b"])
    return {"dim": 2, "type": "t2.2-dedup",
            "statement": f"去重:找出 {len(rows)} 行中的重复对(全等文本)",
            "criteria_ref": CRIT["recompute"],
            "input": {"rows": rows}, "expected": {"dup_pairs": dups},
            "check": "json_map_equal"}


def _t23_anchor_gate(rng, n, k):
    """语义门:候选与锚库极性冲突→疑;一致→收(锚=分布假设,种子=锚池偏差)。"""
    anchors = {f"A{j}": rng.choice(["+", "-"]) for j in range(6)}
    cand, expect = [], {}
    for i in range(n):
        key = rng.choice(list(anchors))
        agree = rng.random() < 0.6
        pol = anchors[key] if agree else ("-" if anchors[key] == "+" else "+")
        cid = f"C{i:02d}"
        cand.append({"cand_id": cid, "anchor": key, "polarity": pol})
        expect[cid] = "accept" if agree else "suspect"
    return {"dim": 2, "type": "t2.3-anchor-gate",
            "statement": "语义门判定:候选极性与锚库冲突者标 suspect,一致者 accept"
                         f"(锚引用 {CRIT['anchorpool']})",
            "criteria_ref": CRIT["anchorpool"],
            "input": {"anchor_bank": anchors, "candidates": cand},
            "expected": {"gate": expect}, "check": "json_map_equal"}


def _t41_stage_violation(rng, n, k):
    """环节违例:五件套链中植入三类违例,判环节→判据映射。"""
    kinds = ["clean", "schema", "provenance", "skip"]
    chain, viol = [], {}
    for i in range(n):
        rid = f"S{i:02d}"
        kind = kinds[i % 4] if rng.random() < 0.7 else "clean"
        row = {"row_id": rid, "turns": rng.randrange(1, 5)}
        if kind == "schema":
            row.update(total_tokens=0, turn_usage_tokens=rng.randrange(500, 9000),
                       external_verified=False, verifier=None)
            viol[rid] = CRIT["schema"]
        elif kind == "provenance":
            row.update(total_tokens=rng.randrange(100, 9000), turn_usage_tokens=0,
                       external_verified=True, verifier=None)
            viol[rid] = CRIT["provenance"]
        elif kind == "skip":
            row.update(total_tokens=rng.randrange(100, 9000), turn_usage_tokens=0,
                       external_verified=False, verifier="v_ext",
                       skip_label="fixture_broken_red", rerun_outcome="no_red")
            viol[rid] = CRIT["skip"]
        else:
            row.update(total_tokens=rng.randrange(100, 9000), turn_usage_tokens=0,
                       external_verified=False, verifier="v_ext")
        chain.append(row)
    return {"dim": 4, "type": "t4.1-stage-violation",
            "statement": f"归因判定:以下 {n} 行证据链,判各行违反哪条判据"
                         f"(干净行不列;三类违例=schema/provenance/skip)",
            "criteria_ref": CRIT["recompute"],
            "input": {"chain": chain}, "expected": {"violations": viol},
            "check": "json_map_equal"}


def _t42_anchor_pool(rng, n, k):
    """锚池审判:三组对照离群率,判规则有罪/无罪(种子=sim50 32/47→3/47)。"""
    design = round(rng.uniform(0.04, 0.09), 3)
    innocent = rng.random() < 0.5
    g_in = design
    g_self = design + (0.0 if innocent else rng.uniform(0.05, 0.15))
    g_prod = round(rng.uniform(0.5, 0.8), 3)
    verdict = "rule_innocent" if abs(g_self - design) < 0.02 else "rule_guilty"
    return {"dim": 4, "type": "t4.2-anchor-pool-verdict",
            "statement": f"锚池审判:设计线 {design},三组对照离群率已给——批内自锚回不到"
                         f"设计线即规则有罪(锚引用 {CRIT['anchorpool']})",
            "criteria_ref": CRIT["anchorpool"],
            "input": {"design_line": design,
                      "groups": {"in_batch_self_anchor": g_in,
                                 "same_composition": round(g_self, 3),
                                 "production_pool": g_prod}},
            "expected": {"verdict": verdict},
            "check": "json_map_equal"}


def _t43_skip_label(rng, n, k):
    """skip 标签保真:结局 vs 病因双判(种子=f08c/d821 失真案)。"""
    rows, expect = [], {}
    for i in range(n):
        rid = f"L{i:02d}"
        outcome = rng.choice(["no_red", "fixture_broken_red", "collection_error"])
        faithful = rng.random() < 0.6
        label = outcome if faithful else rng.choice(
            [o for o in ("no_red", "fixture_broken_red") if o != outcome])
        rows.append({"row_id": rid, "skip_label": label, "rerun_outcome": outcome})
        expect[rid] = "agree" if label == outcome else "degrade"
    return {"dim": 4, "type": "t4.3-skip-label-fidelity",
            "statement": f"标签保真判定:skip 标签与独立重跑结局逐一对照,复现=agree,"
                         f"失真=degrade(锚引用 {CRIT['skip']})",
            "criteria_ref": CRIT["skip"],
            "input": {"rows": rows}, "expected": {"fidelity": expect},
            "check": "json_map_equal"}


GENERATORS = [_t21_gate_rows, _t22_dedup, _t23_anchor_gate,
              _t41_stage_violation, _t42_anchor_pool, _t43_skip_label]


def generate(seed: int, n_per_type: int) -> list[dict]:
    rng = random.Random(seed)
    items = []
    for gi, g in enumerate(GENERATORS):
        for j in range(n_per_type):
            it = g(rng, max(4, n_per_type + 2), j)
            h = hashlib.sha256(
                f"{seed}|{gi}|{j}".encode()).hexdigest()[:12]
            it["id"] = f"bc1:{h}"
            items.append(it)
    return items


def split(items: list[dict], pct: int, prefix: Path) -> None:
    rng = random.Random(hashlib.sha256("split".encode()).hexdigest()[:8])
    shuffled = items[:]
    rng.shuffle(shuffled)
    k = max(1, round(len(shuffled) * pct / 100))
    pub, hold = shuffled[:k], shuffled[k:]
    prefix.with_name(prefix.name + "_public.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in pub),
        encoding="utf-8", newline="\n")
    prefix.with_name(prefix.name + "_holdout.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in hold),
        encoding="utf-8", newline="\n")
    hsha = hashlib.sha256(
        "".join(sorted(x["id"] for x in hold)).encode()).hexdigest()
    prefix.with_name(prefix.name + "_manifest.json").write_text(
        json.dumps({"public_pct": round(100 * len(pub) / len(items), 1),
                    "public_n": len(pub), "holdout_n": len(hold),
                    "holdout_sha256": hsha, "rule": "holdout 永不入自测"},
                   ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=20260918)
    ap.add_argument("--n", type=int, default=5, help="每题型题数")
    ap.add_argument("--out", required=True)
    ap.add_argument("--split", default=None, help="如 60/40")
    ap.add_argument("--split-prefix", default=None)
    a = ap.parse_args(argv)
    items = generate(a.seed, a.n)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in items),
        encoding="utf-8", newline="\n")
    print(f"[OK] {len(items)} items → {a.out} (seed {a.seed})")
    if a.split and a.split_prefix:
        pct = int(a.split.split("/")[0])
        split(items, pct, Path(a.split_prefix))
        print(f"[OK] split {pct}/{100-pct} → {a.split_prefix}_public/_holdout/_manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
