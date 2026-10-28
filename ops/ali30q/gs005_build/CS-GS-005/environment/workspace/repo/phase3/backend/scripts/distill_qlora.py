#!/usr/bin/env python3
"""齿轮⑦ 蒸馏训练:QLoRA SFT Qwen2.5-Coder-7B on A 类燃料(2026-06-22)。

中心环终点(从没跑过的硬事)。把 A 类燃料(强模型 verified 高分解)蒸进开源小模型 →
held-out 上验是否破能力墙(`distill_eval.py`)。

🔴 GPU-gated:torch/transformers/peft/bitsandbytes lazy import·on A 簇 T4(43.166.8.20)。
纯逻辑(SFT 格式化)在 services.distill_train(已 TDD green)·本脚本是 effect 层。

用法:
  python scripts/distill_qlora.py --fuel /path/fuel.jsonl --out /path/adapter \
     --base-model Qwen/Qwen2.5-Coder-7B-Instruct --epochs 3
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# 纯逻辑(无 torch)·已 TDD
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.distill_train import build_sft_texts  # noqa: E402

# 🔴 prompt/completion 拆分(completion-only 训练·2026-06-22 修):
# distill_train._SFT_TEMPLATE = "### Instruction:\n{instruction}\n\n### Problem:\n{input}\n\n### Solution:\n{output}"。
# 拆成 prompt(到 "### Solution:\n" 含) + completion(=output 解)。trl 1.6.0 对 prompt-completion
# 数据集 + completion_only_loss=True 自动 mask 掉 prompt token(0 for prompt·1 for completion)→
# 梯度只落在解 token 上(不再被长 problem 文本稀释·根因#1·最高杠杆)。
# trl 1.6.0 已移除 DataCollatorForCompletionOnlyLM·原生 completion_only_loss 取代。
_PROMPT_TMPL = (
    "### Instruction:\n{instruction}\n\n"
    "### Problem:\n{input}\n\n"
    "### Solution:\n"
)


def build_prompt_completion(rows: list[dict]) -> list[dict]:
    """A 类燃料 rows → prompt-completion 样本(completion=解·只在解上算 loss)。"""
    out = []
    for r in rows:
        prompt = _PROMPT_TMPL.format(
            instruction=(r.get("instruction") or "").strip(),
            input=(r.get("input") or "").strip(),
        )
        completion = (r.get("output") or "").strip()
        out.append({"prompt": prompt, "completion": completion})
    return out


def load_fuel(path: str) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="QLoRA SFT 蒸馏(A 类燃料 → Qwen2.5-Coder-7B)")
    ap.add_argument("--fuel", required=True, help="A 类燃料 jsonl(distill_fuel.accumulate_sample 产)")
    ap.add_argument("--out", required=True, help="adapter 输出目录")
    ap.add_argument("--base-model", default="Qwen/Qwen2.5-Coder-7B-Instruct")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=3e-4)        # 2e-4→3e-4(constant·避 cosine 早衰·根因#3)
    ap.add_argument("--max-seq", type=int, default=4096)
    ap.add_argument("--lora-r", type=int, default=64)        # 16→64(记 ~1.3k token 代码解·根因#2)
    ap.add_argument("--dtype", default="auto", choices=["auto", "fp16", "bf16"],
                    help="auto=按 GPU 能力(T4 Turing 原生无 bf16·emulated 慢→可强制 fp16)")
    a = ap.parse_args(argv)

    rows = load_fuel(a.fuel)
    pc = build_prompt_completion(rows)   # prompt-completion(completion-only 训练)
    print(f"[distill] 燃料 {len(rows)} 条 → prompt-completion {len(pc)} · base={a.base_model}")
    min_n = int(os.environ.get("DISTILL_MIN_N", "12"))   # 首证阈值(20→12·ALE+qwen A类产率低)
    if len(pc) < min_n:
        print(f"[distill] ⚠️ 燃料仅 {len(pc)} 条 · < {min_n} 信号下限 · 先补燃料(别硬训)。")

    # 🔴 GPU effect(lazy import·本地无 torch 不导入)
    import torch  # noqa
    from datasets import Dataset
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              BitsAndBytesConfig)
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTConfig, SFTTrainer  # trl>=1.x:SFTConfig 取代 TrainingArguments

    # dtype 自适应:T4(Turing·SM7.5)原生无 bf16·emulated 慢 → 默认强制 fp16。
    if a.dtype == "bf16":
        use_bf16 = True
    elif a.dtype == "fp16":
        use_bf16 = False
    else:  # auto:用 is_bf16_supported()。T4(Turing)返 True(emulated)→走 bf16。
           # 🔴 实测:fp16+bitsandbytes 在 grad unscale 抛 "not implemented for BFloat16"·
           # bf16 训练无 GradScaler 绕开。A100 原生 bf16 同走此路(快)。
        use_bf16 = torch.cuda.is_bf16_supported()
    compute_dtype = torch.bfloat16 if use_bf16 else torch.float16
    print(f"[distill] GPU={torch.cuda.get_device_name(0)} dtype={'bf16' if use_bf16 else 'fp16'}")

    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=compute_dtype,
                             bnb_4bit_use_double_quant=True)
    tok = AutoTokenizer.from_pretrained(a.base_model)
    tok.pad_token = tok.pad_token or tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        a.base_model, quantization_config=bnb, device_map="auto", torch_dtype=compute_dtype)
    # 🔴 T4 16GB:7B 4bit + 长 ALE 解(~5k tok)→ logits.float() 全词表 upcast 是 OOM 尖峰。
    # gradient_checkpointing 省 transformer-block 激活内存(use_reentrant=False 配 PEFT)。
    model = prepare_model_for_kbit_training(
        model, use_gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False})
    # 🔴 LoRA 强化(根因#2):r=64·alpha=128·+MLP(gate/up/down)·记 ~1.3k token 代码解。
    #    r16 只 attn-proj(q/k/v/o)记不住长解·加 MLP + 高 r → 容量够。
    lora = LoraConfig(r=a.lora_r, lora_alpha=a.lora_r * 2, lora_dropout=0.05,
                      task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                      "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    # 🔴 prompt-completion 数据集(根因#1·最高杠杆):completion_only_loss=True →
    #    trl 自动 mask prompt token·loss 只在解上算(不再被长 problem 稀释)。
    ds = Dataset.from_list(pc)   # 每项 {"prompt":..., "completion":...}
    # trl>=1.x:max_length 移入 SFTConfig·SFTTrainer 用 processing_class。
    # lr_scheduler=constant_with_warmup(根因#3·避 cosine 早衰·warmup 后平台学到底)。
    targs = SFTConfig(output_dir=a.out, num_train_epochs=a.epochs,
                      per_device_train_batch_size=1, gradient_accumulation_steps=8,
                      learning_rate=a.lr, bf16=use_bf16, fp16=not use_bf16,
                      lr_scheduler_type="constant_with_warmup", warmup_ratio=0.1,
                      gradient_checkpointing=True,
                      gradient_checkpointing_kwargs={"use_reentrant": False},
                      logging_steps=1, save_strategy="epoch", report_to=[],
                      max_length=a.max_seq, completion_only_loss=True)
    trainer = SFTTrainer(model=model, train_dataset=ds, args=targs, processing_class=tok)
    trainer.train()
    # 🔴 用 trainer.save_model(非 model.save_pretrained):后者在 accelerate-wrap 后
    # 只落 README 不落 adapter 权重 → eval 从顶层加载到空 adapter → distilled 退化成 base
    # (over-fit sanity 靠 distilled_len==base_len 抓出此 bug·2026-06-22)。
    trainer.save_model(a.out)
    # 双保险:确认顶层有 adapter_model·缺则从 peft model 直接补存。
    import os as _os
    if not _os.path.exists(_os.path.join(a.out, "adapter_model.safetensors")):
        trainer.model.save_pretrained(a.out)
    print(f"[distill] ✅ adapter 存 {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
