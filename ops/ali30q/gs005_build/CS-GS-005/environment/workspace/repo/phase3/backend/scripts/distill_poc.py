#!/usr/bin/env python3
"""中心环蒸馏 PoC driver(2026-06-22)：ALE records → ingest → split → QLoRA → 真 judge eval → 证/杀。

串起齿轮⑦整条真链(端到端从没真跑过)：
  ingest_fuel_records(A类判定) → split_train_heldout → distill_qlora(SFT 出 adapter)
  → distill_eval(base vs distilled vs doubao·真 judge 连续分数 delta) → prove_or_kill。

两种用法：
  minimal dry-run(de-risk·V5 提议)：4 条真 A 类 + 1.5B + epochs=1 → 验管线串通(非验蒸馏效果)。
    别等 12 撞 train/eval 集成 bug → 小池先把整条真链跑一遍。
  首证(放大)：≥12 条 + 7B(先 ping compass 切 CPU 让位)+ epochs=3 → 看 delta 方向证/杀。

用法(GPU 盒 43.166.8.20·训练 venv)：
  /mnt/datadisk0/distill-venv/bin/python distill_poc.py \
    --records /mnt/datadisk0/distill-code/ale_fuel_records.jsonl \
    --workdir /mnt/datadisk0/distill-code/poc_run \
    --base-model Qwen/Qwen2.5-Coder-1.5B-Instruct --epochs 1

🔴 真 judge(judge_version 锁同版·见 _distill_runtime)·不设 ALE_MOCK_SCORE。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)
from services.distill_mint_runner import ingest_fuel_records  # noqa: E402
from services.distill_train import (  # noqa: E402
    split_train_heldout, held_out_eval_record)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="蒸馏 PoC 端到端 driver")
    ap.add_argument("--records", required=True, help="ALE/SWE 燃料 records jsonl(producer 输出)")
    ap.add_argument("--workdir", required=True, help="中间产物目录")
    ap.add_argument("--base-model", default="Qwen/Qwen2.5-Coder-1.5B-Instruct")
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--max-seq", type=int, default=4096)   # 透传 distill_qlora(解完整可见·别截断)
    ap.add_argument("--lora-r", type=int, default=64)      # 透传(强化 LoRA·记长解)
    ap.add_argument("--lr", type=float, default=3e-4)      # 透传(constant·避早衰)
    ap.add_argument("--heldout-frac", type=float, default=0.5)
    ap.add_argument("--min-heldout", type=int, default=2)
    ap.add_argument("--max-heldout", type=int, default=6)
    ap.add_argument("--ale-margin", type=float, default=0.2)
    ap.add_argument("--overfit-sanity", action="store_true",
                    help="train=held=全部样本(跳 split)·验蒸馏机制在训练分布上活没活"
                         "(非泛化)。distilled 应在训练题上 reward>base=SFT 学进去了→"
                         "minimal KILLED 是泛化(燃料量)问题;若训练题也学不会=训练管线更深 bug。")
    a = ap.parse_args(argv)

    if os.environ.get("ALE_MOCK_SCORE"):
        print("[poc] REFUSE: ALE_MOCK_SCORE set — PoC 要真 judge·unset it")
        return 3

    os.makedirs(a.workdir, exist_ok=True)
    records = [json.loads(ln) for ln in open(a.records, encoding="utf-8") if ln.strip()]

    # 1) ingest：records → A 类 SFT 样本(per-record kind 多基准合池)
    samples: list[dict] = []
    res = ingest_fuel_records(records, kind="ale", sink=samples.append,
                              ale_rel_margin=a.ale_margin)
    print(f"[poc] ingest: A={len(res['a_bucket'])} reject={len(res['rejected'])} "
          f"B={len(res['b_bucket'])} err={len(res['errored'])} → samples={len(samples)}")
    print(f"[poc] A-class ids: {res['a_bucket']}")
    if len(samples) < 2:
        print("[poc] FAIL: <2 A类样本·无法 split(先补燃料)")
        return 2

    # 2) split：同分布 A 类题分 train / held-out(确定性·按 task_id)
    tids = lambda xs: [s["meta"]["task_id"] for s in xs]
    if a.overfit_sanity:
        # over-fit sanity：train=held=全部·验蒸馏机制(非泛化)。distilled 应在训练题上 > base。
        train = held = samples
        print(f"[poc] ⚠️ OVERFIT-SANITY: train=held=all {len(samples)}{tids(samples)} "
              f"(验机制·非泛化·distilled 应在训练题上 reward>base)")
    else:
        train, held = split_train_heldout(samples, heldout_frac=a.heldout_frac,
                                          min_heldout=a.min_heldout, max_heldout=a.max_heldout)
        print(f"[poc] split: train={len(train)}{tids(train)} held={len(held)}{tids(held)}")

    fuel_p = os.path.join(a.workdir, "fuel_train.jsonl")
    held_p = os.path.join(a.workdir, "heldout.jsonl")
    adapter_p = os.path.join(a.workdir, "adapter")
    result_p = os.path.join(a.workdir, "eval_result.json")
    with open(fuel_p, "w", encoding="utf-8") as fh:
        for s in train:
            fh.write(json.dumps(s, ensure_ascii=False) + "\n")
    with open(held_p, "w", encoding="utf-8") as fh:
        for s in held:
            fh.write(json.dumps(held_out_eval_record(s), ensure_ascii=False) + "\n")

    py = sys.executable
    env = dict(os.environ)
    env["DISTILL_MIN_N"] = str(len(train))   # minimal 故意小·别 warn

    # 3) 训练：QLoRA SFT
    print(f"[poc] === 训练(QLoRA·{a.base_model}·epochs={a.epochs}·train={len(train)}) ===",
          flush=True)
    r1 = subprocess.run([py, os.path.join(HERE, "distill_qlora.py"),
                         "--fuel", fuel_p, "--out", adapter_p,
                         "--base-model", a.base_model, "--epochs", str(a.epochs),
                         "--max-seq", str(a.max_seq), "--lora-r", str(a.lora_r),
                         "--lr", str(a.lr)],
                        cwd=HERE, env=env)
    if r1.returncode != 0:
        print("[poc] FAIL: 训练崩(集成 bug 暴露·这正是 de-risk 目的)")
        return r1.returncode

    # 4) eval：held-out 上 base vs distilled vs doubao·真 judge delta → 证/杀
    print(f"[poc] === 真 judge eval(held={len(held)}·base/distilled/doubao) ===", flush=True)
    r2 = subprocess.run([py, os.path.join(HERE, "distill_eval.py"),
                         "--heldout", held_p, "--adapter", adapter_p,
                         "--base-model", a.base_model, "--out", result_p,
                         "--min-n", str(len(held))],
                        cwd=HERE, env=env)
    if r2.returncode != 0:
        print("[poc] FAIL: eval 崩(集成 bug 暴露)")
        return r2.returncode

    print("[poc] ✅ 整条蒸馏链端到端真跑通(ingest→split→train→真judge eval→verdict)")
    if os.path.exists(result_p):
        print("[poc] " + open(result_p, encoding="utf-8").read())
    return 0


if __name__ == "__main__":
    sys.exit(main())
