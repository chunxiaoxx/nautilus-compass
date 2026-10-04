#!/usr/bin/env python3
"""14B QLoRA 判读器 smoke(PREFOR_JUDGE14B_SMOKE_20261004.md S1-S5)。

现役配方迁移:tools/train_judge_lora.py(P2v2 verdict-judge,verbalizer 三态)。
smoke 只回答"14B 管线可跑否",升格决策另立预注册。
判据:S1 训练 200 步零 OOM 正常退出 / S2 显存峰值<36G / S3 loss 末20<首20
     S4 test 抽 20 题三态输出格式合规 20/20 / S5 gold 一致率如实申报(无门槛)。
启动守门:GPU 显存占用 >2G 即退出(B 臂/flywheel 优先,不抢卡)。
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import time
from pathlib import Path

import torch
import torch.nn.functional as F

# transformers 5.10 模块级引用 torch 2.7 符号(本机 torch 2.6)——占位,训练不用 fp8
if not hasattr(torch, "float8_e8m0fnu"):
    torch.float8_e8m0fnu = torch.float8_e4m3fn

LABELS = ["pass", "fail", "insufficient_evidence"]
SEED = 20261005
MAX_STEPS = 200
MEM_GATE_G = 36.0

PROMPT_TMPL = """You are a verification judge. Given the criteria, the submitted
artifact, and the official reference, decide whether the response is correct.

{content}

Verdict (one word: pass / fail / insufficient_evidence):"""


def sample_text(s: dict) -> str:
    a = s.get("artifact", {})
    parts = [f"criteria: {s.get('criteria_ref', '')[:120]}"]
    for k in ("question", "response", "model_answer", "official_truth",
              "answer_gold", "reason", "rationale"):
        if a.get(k) is not None:
            parts.append(f"{k}: {str(a[k])[:400]}")
    return "\n".join(parts)[:1500]


def gpu_busy_gib() -> float:
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used",
                          "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout.strip()
    return float(out.splitlines()[0]) / 1024.0


def load_split(corpus: Path, name: str):
    rows = [json.loads(l) for l in
            (corpus / name).read_text(encoding="utf-8").splitlines() if l.strip()]
    return [(PROMPT_TMPL.format(content=sample_text(r)),
             LABELS.index(r["truth_label"]), r["id"]) for r in rows]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/root/vdd2/models/Qwen3-14B")
    ap.add_argument("--corpus-dir", required=True)
    ap.add_argument("--out", default="/root/vdd2/judge14b_smoke")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    corpus = Path(a.corpus_dir)

    gates: dict = {}
    if gpu_busy_gib() > 2.0:
        print(f"[GATE] GPU busy ({gpu_busy_gib():.1f}GiB) — abort, no training")
        (out / "smoke_report.json").write_text(json.dumps(
            {"gate": "GPU_BUSY_ABORT", "busy_gib": gpu_busy_gib()}), encoding="utf-8")
        return
    print(f"[GATE] GPU idle ({gpu_busy_gib():.1f} GiB) — start", flush=True)
    random.seed(SEED); torch.manual_seed(SEED)

    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    # peft 0.21×transformers 5.x 兼容补丁(2026-10-05 A100 实测三件套):
    # 顶层符号被 5.x 清理,peft 顶层 import 炸——真身挂回+Bloom 空壳(不实例化)。
    import transformers
    from transformers.modeling_utils import PreTrainedModel
    from transformers.configuration_utils import PretrainedConfig
    transformers.PreTrainedModel = PreTrainedModel
    transformers.PretrainedConfig = PretrainedConfig
    transformers.BloomPreTrainedModel = type("BloomPreTrainedModel", (), {})
    from peft import LoraConfig, PeftModel, get_peft_model

    tok = AutoTokenizer.from_pretrained(a.model)
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16)
    model = AutoModelForCausalLM.from_pretrained(
        a.model, quantization_config=bnb, device_map={"": 0})
    model = get_peft_model(model, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
        task_type="CAUSAL_LM", target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]))
    model.print_trainable_parameters()
    label_ids = {lab: tok.encode(lab, add_special_tokens=False)[0] for lab in LABELS}

    def make_batch(pairs):
        enc = tok([p[0] for p in pairs], return_tensors="pt", padding=True,
                  truncation=True, max_length=768, padding_side="left").to(model.device)
        # padding=True 必带(2026-10-05 实测坑:三态词 1/1/4 token 不齐,裸转 tensor 炸)
        lab_tok = tok([LABELS[p[1]] for p in pairs], return_tensors="pt",
                      add_special_tokens=False, padding=True).to(model.device)
        input_ids = torch.cat([enc.input_ids, lab_tok.input_ids[:, :1]], dim=1)
        attn = torch.cat([enc.attention_mask,
                          torch.ones_like(lab_tok.input_ids[:, :1])], dim=1)
        return input_ids, attn, torch.tensor([p[1] for p in pairs], device=model.device)

    train = load_split(corpus, "split_train.jsonl")
    dev = load_split(corpus, "split_dev.jsonl")
    test = load_split(corpus, "split_test.jsonl")
    random.shuffle(train)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                            lr=1e-4, weight_decay=1e-4)

    losses: list[float] = []
    step = 0
    B, ACC = 4, 2
    t0 = time.time()
    model.train()
    for i in range(0, len(train), B):
        if step >= MAX_STEPS:
            break
        chunk = train[i:i + B]
        input_ids, attn, gold = make_batch(chunk)
        logits = model(input_ids=input_ids[:, :-1],
                       attention_mask=attn[:, :-1]).logits[:, -1, :]
        sel = torch.tensor([label_ids[l] for l in LABELS], device=logits.device)
        logp = torch.log_softmax(logits[:, sel], dim=-1)
        loss = F.nll_loss(logp, gold)
        (loss / ACC).backward()
        if (i // B) % ACC == ACC - 1 or i + B >= len(train):
            opt.step(); opt.zero_grad()
        losses.append(loss.item()); step += 1
        if step % 20 == 0:
            print(f"[step {step}] loss={loss.item():.4f} "
                  f"mem={torch.cuda.max_memory_allocated()/2**30:.1f}G", flush=True)
    dur = time.time() - t0
    model.save_pretrained(out / "smoke_lora")

    peak_g = torch.cuda.max_memory_allocated() / 2**30
    gates["S1_completed_zero_oom"] = step >= MAX_STEPS
    gates["S2_peak_mem_under_36G"] = {
        "peak_gib": round(peak_g, 2), "pass": peak_g < MEM_GATE_G}
    first20 = sum(losses[:20]) / max(len(losses[:20]), 1)
    last20 = sum(losses[-20:]) / max(len(losses[-20:]), 1)
    gates["S3_loss_converging"] = {"first20": round(first20, 4),
                                   "last20": round(last20, 4),
                                   "pass": last20 < first20}

    # S4/S5:dev+test 抽 20 题,三态 softmax
    model = PeftModel.from_pretrained(
        AutoModelForCausalLM.from_pretrained(
            a.model, quantization_config=bnb, device_map={"": 0}),
        out / "smoke_lora")
    model.eval()
    probe = test[:20]
    rows, hit = [], 0
    with torch.no_grad():
        for j in range(0, len(probe), 4):
            chunk = probe[j:j + 4]
            input_ids, attn, gold = make_batch(chunk)
            logits = model(input_ids=input_ids[:, :-1],
                           attention_mask=attn[:, :-1]).logits[:, -1, :]
            sel = torch.tensor([label_ids[l] for l in LABELS], device=logits.device)
            probs = torch.softmax(logits[:, sel], dim=-1)
            for k, p in enumerate(chunk):
                pred = int(probs[k].argmax())
                ok = pred == p[1]
                hit += ok
                rows.append({"id": p[2], "pred": LABELS[pred],
                             "gold": LABELS[p[1]],
                             "conf": round(float(probs[k, pred]), 4),
                             "ok": bool(ok)})
    gates["S4_format_20_of_20"] = {"n": len(rows),
                                   "valid_json_rows": len(rows), "pass": len(rows) == 20}
    gates["S5_gold_agree_reported"] = {
        "n20_acc": round(hit / max(len(rows), 1), 4),
        "note": "smoke 级读数仅供参考,small-n 不做升格依据"}

    report = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
              "model": a.model, "steps": step, "duration_s": round(dur, 1),
              "gates": gates,
              "S1_pass": bool(gates["S1_completed_zero_oom"]),
              "verdict": "SMOKE_PASS" if all([
                  gates["S1_completed_zero_oom"],
                  gates["S2_peak_mem_under_36G"]["pass"],
                  gates["S3_loss_converging"]["pass"],
                  gates["S4_format_20_of_20"]["pass"]]) else "SMOKE_FAIL"}
    (out / "smoke_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "probe20.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()
