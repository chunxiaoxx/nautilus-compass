#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""触发日合并池导出+held-out 切分(SEVENB_COMPARE_PREREG 零现场清单 步2)。

池=corpus_pipeline 的 merged 全量(与 manifest sha16 同构复算);
标签口径如实申报:org_fuel 系条目 truth_label=judge_verdict(NACRE 1.7B 自判,
自举标注——局限进 report G4 披露);三 split 系条目=原始 truth_label 不动。
切分:held-out 300(SEED 20261005,均匀抽),train=余量;qid 防泄漏审计落 report。
"""
import hashlib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
# 复用 pipeline 的 source 注册逻辑(直接 import 执行其 main 前的构建段太重,这里独立重建)
ROOT = Path("runtime")
SEED = 20261005
HOLDOUT_N = 300
LABELS = {"pass": "pass", "fail": "fail",
          "insufficient_evidence": "insufficient_evidence"}


def load_jsonl(p: Path):
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def qid_of(e):
    return ((e.get("artifact") or {}).get("qid") or e.get("id") or e.get("pf_id", ""))


def leak_key(sid: str) -> str:
    """泄漏防护键:与训练脚本 qid_of(id) 同构(rejudge-<q>/lme-<...>-<q> 归并裸 qid)。
    R528: 切分审计键必须与训练脚本比对键同构——2026-10-13 首跑 73 交集即因
    本地按完整 id 审计、A100 按归并键审计,变体行(rejudge-/lme-)跨集漏判。"""
    if sid.startswith("rejudge-"):
        return sid[len("rejudge-"):]
    if sid.startswith("lme-"):
        return sid.rsplit("-", 1)[-1]
    return sid


def gate_rows(fname):
    return [r for r in load_jsonl(ROOT / f"org_fuel/{fname}")
            if r.get("judge_verdict") == "pass"
            and r.get("anchor_level") in ("L0", "L1")]


def main() -> int:
    sources = {}
    for name in ("split_train_v1", "split_dev_v1", "split_test_v1"):
        sources[name] = load_jsonl(ROOT / f"verdict_corpus/{name}.jsonl")
    for d in sorted((ROOT / "verdict_corpus/delta").glob("delta_*.jsonl")):
        sources[f"delta:{d.name}"] = load_jsonl(d)
    # org_fuel 各源(与 corpus_pipeline R524/R526 后口径一致)
    sources["org_fuel:gate_passed"] = gate_rows("fuel_verdicts.jsonl")
    for tag, f in [("letters", "fuel_verdicts_letters.jsonl"),
                   ("docs", "fuel_verdicts_docs.jsonl"),
                   ("outreach", "fuel_verdicts_outreach.jsonl"),
                   ("queue", "fuel_verdicts_queue.jsonl"),
                   ("memory", "fuel_verdicts_memory.jsonl"),
                   ("flywheel", "fuel_verdicts_flywheel.jsonl"),
                   ("flywheel_vetted", "fuel_verdicts_flywheel_vetted.jsonl"),
                   ("queue_r3", "fuel_verdicts_queue_r3.jsonl"),
                   ("memory_r3", "fuel_verdicts_memory_r3.jsonl"),
                   ("flywheel_r3", "fuel_verdicts_flywheel_r3.jsonl"),
                   ("grain_r4", "fuel_verdicts_grain_r4.jsonl"),
                   ("commits_r5", "fuel_verdicts_commits_r5.jsonl")]:
        rows = gate_rows(f)
        if rows:
            sources[f"org_fuel:{tag}"] = rows

    # 源池(完整 qid 口径)——与 manifest sha 同构校验
    seen0, base = {}, {}
    for src, items in sources.items():
        for e in items:
            q = qid_of(e)
            if not q or q in seen0:
                continue
            seen0[q] = src
            base[q] = {"src": src, "entry": e}
    man = json.loads((ROOT / "verdict_corpus/manifest_corpus_pipeline.json").read_text(encoding="utf-8"))
    base_bytes = json.dumps([base[q]["entry"] for q in sorted(base)],
                            ensure_ascii=False, sort_keys=True).encode()
    base_sha = hashlib.sha256(base_bytes).hexdigest()[:16]
    assert base_sha == man["merged_sha16"], f"sha mismatch: {base_sha} != manifest {man['merged_sha16']}"
    print(f"[OK] source pool sha16={base_sha} n={len(base)} (== manifest)")

    # 触发池(leak_key 严化口径,合并 rejudge-/lme- 变体行)——独立 sha 记档
    seen, merged = {}, {}
    for q in sorted(base):
        k = leak_key(q)
        if k in seen:
            continue
        seen[k] = q
        merged[k] = base[q]
    trig_bytes = json.dumps([merged[k]["entry"] for k in sorted(merged)],
                            ensure_ascii=False, sort_keys=True).encode()
    trig_sha = hashlib.sha256(trig_bytes).hexdigest()[:16]
    print(f"[OK] trigger pool sha16={trig_sha} n={len(merged)} (leak_key 严化, 合并变体 {len(base)-len(merged)} 行)")

    # 转训练行 schema(id/criteria_ref/artifact/truth_label)
    rows = []
    n_self = 0
    for q in sorted(merged):
        src, e = merged[q]["src"], merged[q]["entry"]
        if src.startswith(("split_", "delta:")):
            label = e.get("truth_label")
        else:
            label = LABELS.get(e.get("judge_verdict"))
            n_self += 1
        if label not in LABELS.values():
            continue
        # R533 空输入修复:org_fuel 系 verdicts 行无 content 字段(只有 situation),
        # delta_0003/4/5 内容在 artifact_ref,delta_0001 为聚合数值行——分级兜底,
        # 杜绝"空输入+标签"进训练(审计 R532 发现 28.9% 空输入后的根修)
        art = e.get("artifact") or {}
        has_text = any(isinstance(art.get(k), str) and art[k].strip()
                       for k in ("question", "response", "content", "model_answer",
                                 "official_truth", "answer_gold", "reason", "rationale"))
        if not has_text:
            fill = (e.get("content") or e.get("situation")
                    or (art.get("artifact_ref") if isinstance(art.get("artifact_ref"), str) else "")
                    or json.dumps({k: v for k, v in art.items() if not isinstance(v, (dict, list))},
                                  ensure_ascii=False))
            art = {"content": (fill or "").strip()}
        rows.append({"id": q, "criteria_ref": e.get("criteria_ref", ""),
                     "artifact": art,
                     "truth_label": label, "_src": src})
    print(f"[OK] trainable rows={len(rows)} (self_labeled={n_self})")

    rng = random.Random(SEED)
    idx = list(range(len(rows)))
    rng.shuffle(idx)
    hold_idx = set(idx[:HOLDOUT_N])
    holdout = [rows[i] for i in sorted(hold_idx)]
    train = [rows[i] for i in idx[HOLDOUT_N:]]

    # qid 防泄漏审计(一行,落 report 附件)
    t_ids = {leak_key(r["id"]) for r in train}
    h_ids = {leak_key(r["id"]) for r in holdout}
    audit = {"pool_sha16": trig_sha, "source_pool_sha16": base_sha,
             "variant_rows_merged": len(base) - len(merged),
             "pool_n": len(rows), "holdout_n": len(holdout),
             "train_n": len(train), "qid_intersection": len(t_ids & h_ids),
             "self_labeled_n": n_self,
             "seed": SEED, "ts": "2026-10-13"}
    assert audit["qid_intersection"] == 0

    out = ROOT / "verdict_corpus/orgfuel_v2"  # R533: v1(2843 含空输入)为 8B/1.7B-v2 对拍历史数据集保留不动;v2=空输入修复+对齐 manifest 最新源
    out.mkdir(parents=True, exist_ok=True)
    for name, data in [("split_train.jsonl", train), ("split_dev.jsonl", holdout)]:
        (out / name).write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in data) + "\n",
            encoding="utf-8")
    (out / "split_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    print(f"[OK] written: train={len(train)} holdout={len(holdout)} audit={audit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
