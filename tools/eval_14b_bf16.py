#!/usr/bin/env python3
"""实验 A(U5 归因翻案检验):14B **bf16** 推理对拍。
首跑口径不对称:14B=4bit(nf4) vs 1.7B=bf16——本脚本唯一变量=14B 加载精度(bf16,无量化),
复用 train_judge14b_upgrade 的 LABELS/PROMPT/evaluate/load_split(零逻辑改动)。
判据不变:同 292 held-out 同 gold;与首跑 4bit、1.7B 三方对账,含逐条 pred 翻转计数。
启动守门同原档(GPU>2G 退出)。读数正反照报(勘误文化)。"""
import json
import subprocess
import sys
from pathlib import Path

import torch

sys.path.insert(0, "/root/vdd2/judge14b_upgrade")
from train_judge14b_upgrade import LABELS, evaluate, load_split  # noqa: E402

BASE = Path("/root/vdd2/judge14b_upgrade")
CORPUS = Path("/root/vdd2/judge14b_smoke")
MODEL14 = "/root/vdd2/models/Qwen3-14B"
ADAPTER = BASE / "judge14b_lora"


def gpu_busy_gib() -> float:
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used",
                          "--format=csv,noheader,nounits"], capture_output=True, text=True)
    return int(out.stdout.strip().splitlines()[0]) / 1024


def acc_of(name: str):
    rs = [json.loads(l) for l in (BASE / name).read_text(encoding="utf-8").splitlines() if l.strip()]
    return sum(r["ok"] for r in rs) / len(rs), rs


def main() -> int:
    if gpu_busy_gib() > 2.0:
        print(f"[GATE] GPU busy ({gpu_busy_gib():.1f}GiB) — abort")
        return 1
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import transformers
    from transformers.modeling_utils import PreTrainedModel
    from transformers.configuration_utils import PretrainedConfig
    transformers.PreTrainedModel = PreTrainedModel
    transformers.PretrainedConfig = PretrainedConfig
    transformers.BloomPreTrainedModel = type("BloomPreTrainedModel", (), {})
    from peft import PeftModel

    print(f"[GATE] GPU idle ({gpu_busy_gib():.1f} GiB) — start", flush=True)
    tok = AutoTokenizer.from_pretrained(MODEL14)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL14, torch_dtype=torch.bfloat16, device_map={"": 0})
    model = PeftModel.from_pretrained(model, ADAPTER)
    label_ids = {lab: tok.encode(lab, add_special_tokens=False)[0] for lab in LABELS}

    holdout = load_split(CORPUS, "split_dev.jsonl") + load_split(CORPUS, "split_test.jsonl")
    rows, lats = evaluate(model, tok, holdout, label_ids)
    acc = sum(r["ok"] for r in rows) / len(rows)
    (BASE / "eval292_14b_bf16.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")

    acc4, rs4 = acc_of("eval292_14b.jsonl")
    acc17, _ = acc_of("eval292_17b.jsonl")
    flips = sum(1 for x, y in zip(rows, rs4) if x["pred"] != y["pred"])
    summary = {
        "acc_14b_bf16": round(acc, 4),
        "acc_14b_4bit_first_run": round(acc4, 4),
        "acc_17b_bf16_incumbent": round(acc17, 4),
        "bf16_vs_4bit_pred_flips": flips,
        "bf16_vs_4bit_delta_pp": round((acc - acc4) * 100, 2),
        "bf16_vs_17b_delta_pp": round((acc - acc17) * 100, 2),
        "quantization_attribution": ("翻案成立(量化为主要归因)" if acc >= acc17
                                     else ("部分成立(bf16 显著回升,未及现役)" if acc > acc4 + 0.005
                                           else "不成立(bf16 无回升,归因转向 LoRA 配置/语料量)")),
        "p50_s": round(sorted(lats)[len(lats) // 2], 4),
        "note": "U5/U6 判据口径不变;本实验只做归因,切换决策仍走预注册语义+用户拍板"}
    (BASE / "bf16_recheck_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
