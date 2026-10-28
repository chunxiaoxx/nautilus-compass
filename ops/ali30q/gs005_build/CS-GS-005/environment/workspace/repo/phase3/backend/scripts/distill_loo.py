#!/usr/bin/env python3
"""LOO/k-fold held-out 首证 driver(2026-06-23·方向 B)：稀缺 A 类燃料榨干泛化信号。

单 split 在 N=3-7 料下 held=1-2、噪声大;CV 让每道题都当过 held-out,N 折聚合=信号强 N 倍。
每折:train QLoRA(其余道) → eval 留出折(训练未见) → 收 per_task → 跨折聚合 → 证/杀。

🔴 成本:每折一次完整重训。LOO N=6 ≈ 6 次重训(~2hr T4)。首证可 --k 3 折中,确认方向后 LOO 加精度。
🔴 真 judge(judge_version 锁同版·见 _distill_runtime)·不设 ALE_MOCK_SCORE。

用法(GPU 盒·训练 venv):
  /mnt/datadisk0/distill-venv/bin/python distill_loo.py \
    --records /mnt/datadisk0/distill-code/ale_fuel_noahc008.jsonl \
    --workdir /mnt/datadisk0/distill-code/loo_run \
    --base-model Qwen/Qwen2.5-Coder-1.5B-Instruct --k 3 --epochs 3
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

# 🩹 expandable_segments:T4 与 compass daemon(~4.4G)共享下·3B@4096 backward 因显存碎片差 ~50MB OOM
# (2026-06-25 实测:加此 env 从 OOM → free 7G)。子进程 distill_qlora 继承 os.environ → 生效。
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)
from services.distill_mint_runner import ingest_fuel_records           # noqa: E402
from services.distill_train import (                                   # noqa: E402
    cv_folds, aggregate_cv_results, held_out_eval_record,
    prove_or_kill_verdict)
from services.verdict_gate import gate_verdict                        # noqa: E402


def _tids(xs):
    return [s.get("meta", {}).get("task_id") for s in xs]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="LOO/k-fold held-out 首证 driver")
    ap.add_argument("--records", required=True, help="A 类燃料 records jsonl(producer 输出)")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--base-model", default="Qwen/Qwen2.5-Coder-1.5B-Instruct")
    ap.add_argument("--k", type=int, default=0, help="k-fold 折数(0=LOO·每折留 1)")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--max-seq", type=int, default=4096)
    ap.add_argument("--lora-r", type=int, default=64)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--ale-margin", type=float, default=0.2)
    a = ap.parse_args(argv)

    if os.environ.get("ALE_MOCK_SCORE"):
        print("[loo] REFUSE: ALE_MOCK_SCORE set — 首证要真 judge·unset it")
        return 3

    # 🔴 workdir/records 转绝对路径:子进程(distill_qlora/eval)cwd=HERE(scripts/)≠ 本 cwd,
    # 相对路径会找不到 fuel/heldout 文件(2026-06-23 实测 bug)。
    a.workdir = os.path.abspath(a.workdir)
    a.records = os.path.abspath(a.records)
    os.makedirs(a.workdir, exist_ok=True)
    records = [json.loads(ln) for ln in open(a.records, encoding="utf-8") if ln.strip()]

    # 1) ingest → A 类样本
    samples: list[dict] = []
    res = ingest_fuel_records(records, kind="ale", sink=samples.append,
                              ale_rel_margin=a.ale_margin)
    print(f"[loo] ingest: A={len(res['a_bucket'])} {res['a_bucket']} "
          f"reject={len(res['rejected'])} err={len(res['errored'])}")
    if len(samples) < 2:
        print("[loo] FAIL: <2 A 类样本·无法 CV(先补燃料)")
        return 2

    # 2) CV 折(LOO 或 k-fold)
    folds = cv_folds(samples, k=(a.k or None))
    print(f"[loo] {'LOO' if not a.k else f'{a.k}-fold'}: {len(folds)} 折 · "
          f"每折 train≈{len(folds[0][0])} held≈{len(folds[0][1])}")

    py = sys.executable
    fold_results: list[list[dict]] = []
    for fi, (train, held) in enumerate(folds):
        fdir = os.path.join(a.workdir, f"fold{fi}")
        os.makedirs(fdir, exist_ok=True)
        fuel_p = os.path.join(fdir, "fuel_train.jsonl")
        held_p = os.path.join(fdir, "heldout.jsonl")
        adapter_p = os.path.join(fdir, "adapter")
        result_p = os.path.join(fdir, "eval_result.json")
        with open(fuel_p, "w", encoding="utf-8") as fh:
            for s in train:
                fh.write(json.dumps(s, ensure_ascii=False) + "\n")
        with open(held_p, "w", encoding="utf-8") as fh:
            for s in held:
                fh.write(json.dumps(held_out_eval_record(s), ensure_ascii=False) + "\n")
        print(f"[loo] === fold {fi}/{len(folds)-1}: train={_tids(train)} "
              f"held={_tids(held)} ===", flush=True)

        env = dict(os.environ)
        env["DISTILL_MIN_N"] = str(len(train))
        r1 = subprocess.run([py, os.path.join(HERE, "distill_qlora.py"),
                             "--fuel", fuel_p, "--out", adapter_p,
                             "--base-model", a.base_model, "--epochs", str(a.epochs),
                             "--max-seq", str(a.max_seq), "--lora-r", str(a.lora_r),
                             "--lr", str(a.lr)], cwd=HERE, env=env)
        if r1.returncode != 0:
            print(f"[loo] fold {fi} 训练崩·跳过此折"); continue
        r2 = subprocess.run([py, os.path.join(HERE, "distill_eval.py"),
                             "--heldout", held_p, "--adapter", adapter_p,
                             "--base-model", a.base_model, "--out", result_p,
                             "--min-n", str(len(held))], cwd=HERE, env=env)
        if r2.returncode != 0 or not os.path.exists(result_p):
            print(f"[loo] fold {fi} eval 崩·跳过此折"); continue
        # distill_eval 写 {verdict,delta,n} 但不存 per_task → 重算需 per_task。
        # 约定:distill_eval 同时 dump per_task 到 <result>.pertask.json(见下补丁)。
        pt_p = result_p.replace(".json", ".pertask.json")
        if os.path.exists(pt_p):
            fold_results.append(json.loads(open(pt_p, encoding="utf-8").read()))
        else:
            print(f"[loo] ⚠️ fold {fi} 缺 per_task dump(distill_eval 需补 .pertask.json)")
        # 🧹 eval 完即清本折 adapter(先抢救 trainer_state 的 loss·防 fold adapters 堆满)。
        # 续19 + 6/26 两次 LOO adapters 堆满 datadisk0(28G·99%)阻塞 V5 = 教训不机制化复发·
        # 此处机制化治本:峰值磁盘从 12 折(~28G)降到 ~1 折(~2.3G)·不靠"记得跑完清"。
        _ts = glob.glob(os.path.join(adapter_p, "checkpoint-*", "trainer_state.json"))
        if _ts:
            shutil.copy(sorted(_ts)[-1], os.path.join(fdir, "trainer_state.json"))
        shutil.rmtree(adapter_p, ignore_errors=True)

    # 3) 聚合 N 折 held-out 评测 → 证/杀
    delta = aggregate_cv_results(fold_results)
    raw_verdict = prove_or_kill_verdict(delta, min_n=len(samples))   # CV 下 n=总样本数
    # 🦷 verdict-gate 硬门(2026-06-25·治鬼打墙):强结论(KILLED/PROVEN)发出前必须过门——
    # 缺 confound-check / n 太小 / PROVEN 没异框验证 → BLOCK 或降级 INCONCLUSIVE。
    # 不靠"我提醒自己"(anchor #6)·靠代码。flag 经 env 显式声明(调用方须真核过才设)。
    gate = gate_verdict(
        raw_verdict,
        confound_checked=os.environ.get("DISTILL_CONFOUND_CHECKED") == "1",
        n_samples=len(samples),
        min_n=int(os.environ.get("DISTILL_GATE_MIN_N", "12")),
        cross_frame_verified=os.environ.get("DISTILL_CROSS_FRAME_VERIFIED") == "1",
    )
    verdict = gate["verdict"]
    if not gate["allowed"]:
        print(f"[loo] 🚧 verdict-gate BLOCKED raw={raw_verdict}: {gate['reason']}")
    elif verdict != raw_verdict:
        print(f"[loo] 🚧 verdict-gate 降级 {raw_verdict}→{verdict}: {gate['reason']}")
    out = {"verdict": verdict, "raw_verdict": raw_verdict, "gate": gate,
           "delta": delta, "folds": len(fold_results),
           "n_samples": len(samples), "a_bucket": res["a_bucket"]}
    with open(os.path.join(a.workdir, "loo_result.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"[loo] 🎯 CV verdict={verdict} · win_rate_vs_base={delta['win_rate_vs_base']} "
          f"· uplift={delta['mean_rel_uplift_vs_base']} · n={delta['n']}({len(fold_results)} 折)")
    print("[loo] PROVEN=泛化破墙(中心环真闭合) / KILLED=小样本蒸馏不迁移 / INCONCLUSIVE=补料")
    return 0


if __name__ == "__main__":
    sys.exit(main())
