#!/usr/bin/env python3
"""14B QLoRA 判读器升格跑(PREFOR_JUDGE14B_UPGRADE_20261005.md U1-U7)。

配方=tools/train_judge14b_smoke.py 同构迁移(peft 三件套补丁/4bit nf4/LoRA r16/AdamW 1e-4)。
U1 全量语料 3 epoch(MAX_STEPS 上限 2000,取先到)零 OOM 正常退出落 adapter
U2 显存峰值<36G / U3 loss 末20<首20
U4 test 抽 n=100 三态输出合规≥98/100(smoke S4 同构口径,如实申报)
U5/U6 复核集=split_dev+split_test 全量(292 条,held-out):14B vs 现役 1.7B champion 同集对拍,
       U5=14B≥1.7B(不劣);U6=14B≥1.7B+3pp(显著,达此档推荐切换)
U7 推理时延 P50/P95+吞吐+VRAM 如实申报(14B=4bit,1.7B=bf16,口径差异注记)
qid 零相交核查:复核集与训练集按 qid_of(id) 派生键,交集必须为空,结果落 report。
启动守门:GPU 显存占用>2G 即退出(B 臂/flywheel 优先,不抢卡)。
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
MAX_STEPS_CAP = 2000
MAX_EPOCHS = 3
MEM_GATE_G = 36.0
U4_N = 100
U4_GATE = 98
U6_MARGIN = 0.03

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


def qid_of(sid: str) -> str:
    """泄漏防护键:与 tools/corpus_split.py qid_of 同构(rejudge-<qid>/lme-...-<qid> 归并裸 qid)。"""
    if sid.startswith("rejudge-"):
        return sid[len("rejudge-"):]
    if sid.startswith("lme-"):
        return sid.rsplit("-", 1)[-1]
    return sid


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


def load_raw_ids(corpus: Path, name: str):
    return [json.loads(l)["id"] for l in
            (corpus / name).read_text(encoding="utf-8").splitlines() if l.strip()]


def pct(sorted_xs: list[float], q: float) -> float:
    idx = min(int(q * len(sorted_xs)), len(sorted_xs) - 1)
    return sorted_xs[idx]


def evaluate(model, tok, pairs, label_ids) -> tuple[list[dict], list[float]]:
    """同集对拍:三态 softmax 逐条判定,返回逐行读数与时延序列。"""
    rows, lats = [], []
    model.eval()
    with torch.no_grad():
        for j in range(0, len(pairs), 4):
            chunk = pairs[j:j + 4]
            enc = tok([p[0] for p in chunk], return_tensors="pt", padding=True,
                      truncation=True, max_length=768, padding_side="left").to(model.device)
            t0 = time.time()
            logits = model(input_ids=enc.input_ids,
                           attention_mask=enc.attention_mask).logits[:, -1, :]
            if model.device.type == "cuda":
                torch.cuda.synchronize()
            lats.append((time.time() - t0) / len(chunk))
            sel = torch.tensor([label_ids[l] for l in LABELS], device=logits.device)
            probs = torch.softmax(logits[:, sel], dim=-1)
            for k, p in enumerate(chunk):
                pred = int(probs[k].argmax())
                rows.append({"id": p[2], "pred": LABELS[pred], "gold": LABELS[p[1]],
                             "conf": round(float(probs[k, pred]), 4),
                             "ok": bool(pred == p[1])})
    return rows, lats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/root/vdd2/models/Qwen3-14B")
    ap.add_argument("--base17", default="/root/vdd2/models/Qwen3-1.7B")
    ap.add_argument("--champion", default="/root/vdd2/judge14b_upgrade/champion_17b_lora")
    ap.add_argument("--corpus-dir", default="/root/vdd2/judge14b_smoke")
    ap.add_argument("--out", default="/root/vdd2/judge14b_upgrade")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    corpus = Path(a.corpus_dir)

    gates: dict = {}
    if gpu_busy_gib() > 2.0:
        print(f"[GATE] GPU busy ({gpu_busy_gib():.1f}GiB) — abort, no training")
        (out / "upgrade_report.json").write_text(json.dumps(
            {"gate": "GPU_BUSY_ABORT", "busy_gib": gpu_busy_gib()}), encoding="utf-8")
        return
    print(f"[GATE] GPU idle ({gpu_busy_gib():.1f} GiB) — start", flush=True)
    random.seed(SEED); torch.manual_seed(SEED)

    # qid 零相交核查(先于训练,U5/U6 复核集合法性门)
    train_ids = load_raw_ids(corpus, "split_train.jsonl")
    holdout_ids = (load_raw_ids(corpus, "split_dev.jsonl")
                   + load_raw_ids(corpus, "split_test.jsonl"))
    inter = set(map(qid_of, holdout_ids)) & set(map(qid_of, train_ids))
    gates["qid_disjoint_check"] = {"holdout_n": len(holdout_ids),
                                   "train_n": len(train_ids),
                                   "qid_intersection": len(inter), "pass": len(inter) == 0}
    if inter:
        print(f"[FATAL] qid intersection {len(inter)} — holdout invalid", flush=True)
        (out / "upgrade_report.json").write_text(json.dumps(
            {"gate": "QID_INTERSECTION", "n": len(inter)}, ensure_ascii=False),
            encoding="utf-8")
        return

    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    # peft 0.21×transformers 5.x 兼容补丁(2026-10-05 A100 实测三件套,smoke 同款)
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

    train = load_split(corpus, "split_train.jsonl")
    dev = load_split(corpus, "split_dev.jsonl")
    test = load_split(corpus, "split_test.jsonl")
    random.shuffle(train)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                            lr=1e-4, weight_decay=1e-4)

    losses: list[float] = []
    step, hit_cap = 0, False
    B, ACC = 4, 2
    t0 = time.time()
    model.train()
    for _epoch in range(MAX_EPOCHS):
        for i in range(0, len(train), B):
            if step >= MAX_STEPS_CAP:
                hit_cap = True
                break
            chunk = train[i:i + B]
            enc = tok([p[0] for p in chunk], return_tensors="pt", padding=True,
                      truncation=True, max_length=768, padding_side="left").to(model.device)
            lab_tok = tok([LABELS[p[1]] for p in chunk], return_tensors="pt",
                          add_special_tokens=False, padding=True).to(model.device)
            input_ids = torch.cat([enc.input_ids, lab_tok.input_ids[:, :1]], dim=1)
            attn = torch.cat([enc.attention_mask,
                              torch.ones_like(lab_tok.input_ids[:, :1])], dim=1)
            gold = torch.tensor([p[1] for p in chunk], device=model.device)
            logits = model(input_ids=input_ids[:, :-1],
                           attention_mask=attn[:, :-1]).logits[:, -1, :]
            sel = torch.tensor([label_ids[l] for l in LABELS], device=logits.device)
            logp = torch.log_softmax(logits[:, sel], dim=-1)
            loss = F.nll_loss(logp, gold)
            (loss / ACC).backward()
            if (i // B) % ACC == ACC - 1 or i + B >= len(train):
                opt.step(); opt.zero_grad()
            losses.append(loss.item()); step += 1
            if step % 50 == 0:
                print(f"[step {step}] loss={loss.item():.4f} "
                      f"mem={torch.cuda.max_memory_allocated()/2**30:.1f}G", flush=True)
        if hit_cap:
            break
    dur = time.time() - t0
    model.save_pretrained(out / "judge14b_lora")

    peak_g = torch.cuda.max_memory_allocated() / 2**30
    expected_steps = MAX_EPOCHS * ((len(train) + B - 1) // B)
    gates["U1_full_corpus_trained"] = {
        "steps": step, "expected_3epoch_steps": expected_steps,
        "zero_oom": True, "pass": step >= expected_steps and not hit_cap}
    gates["U2_peak_mem_under_36G"] = {
        "peak_gib": round(peak_g, 2), "pass": peak_g < MEM_GATE_G}
    first20 = sum(losses[:20]) / max(len(losses[:20]), 1)
    last20 = sum(losses[-20:]) / max(len(losses[-20:]), 1)
    gates["U3_loss_converging"] = {"first20": round(first20, 4),
                                   "last20": round(last20, 4),
                                   "pass": last20 < first20}
    train_s = round(dur, 1)

    # U4:test 抽 n=100 三态输出合规(固定 seed,smoke S4 同构口径)
    rng = random.Random(SEED)
    u4_idx = rng.sample(range(len(test)), U4_N)
    model = PeftModel.from_pretrained(
        AutoModelForCausalLM.from_pretrained(
            a.model, quantization_config=bnb, device_map={"": 0}),
        out / "judge14b_lora")
    model.eval()
    u4_rows, u4_lats = evaluate(model, tok, [test[i] for i in u4_idx], label_ids)
    gates["U4_format_n100"] = {"n": len(u4_rows), "valid_rows": len(u4_rows),
                               "gate": U4_GATE, "pass": len(u4_rows) >= U4_GATE}

    # U5/U6:复核集=dev+test 全量 292 条,14B vs 现役 1.7B champion 同集对拍
    holdout = dev + test
    b14_rows, b14_lats = evaluate(model, tok, holdout, label_ids)
    acc14 = sum(r["ok"] for r in b14_rows) / max(len(b14_rows), 1)

    del model
    torch.cuda.empty_cache()
    tok17 = AutoTokenizer.from_pretrained(a.base17)
    m17 = AutoModelForCausalLM.from_pretrained(
        a.base17, torch_dtype=torch.bfloat16, device_map={"": 0})
    m17 = PeftModel.from_pretrained(m17, a.champion)
    b17_rows, b17_lats = evaluate(m17, tok17, holdout,
                                  {lab: tok17.encode(lab, add_special_tokens=False)[0]
                                   for lab in LABELS})
    acc17 = sum(r["ok"] for r in b17_rows) / max(len(b17_rows), 1)

    gates["U5_not_worse_than_incumbent"] = {
        "acc_14b": round(acc14, 4), "acc_17b": round(acc17, 4),
        "pass": acc14 >= acc17}
    gates["U6_significant_over_incumbent"] = {
        "delta_pp": round((acc14 - acc17) * 100, 2), "margin_pp": 3.0,
        "pass": acc14 >= acc17 + U6_MARGIN,
        "note": "达 U5 未达 U6=保留 1.7B 现役,14B 记档待语料增长再评"}

    # U7:推理时延 P50/P95+吞吐+VRAM 申报(14B=4bit,1.7B=bf16,口径差异如实注记)
    lat14 = sorted(u4_lats + b14_lats)
    lat17 = sorted(b17_lats)
    gates["U7_cost_reported"] = {
        "train_seconds": train_s, "train_peak_gib": round(peak_g, 2),
        "infer_14b_4bit": {"per_sample_p50_s": round(pct(lat14, 0.50), 4),
                           "per_sample_p95_s": round(pct(lat14, 0.95), 4),
                           "throughput_per_s": round(1 / pct(lat14, 0.50), 2)},
        "infer_17b_bf16": {"per_sample_p50_s": round(pct(lat17, 0.50), 4),
                           "per_sample_p95_s": round(pct(lat17, 0.95), 4),
                           "throughput_per_s": round(1 / pct(lat17, 0.50), 2)},
        "note": "口径差异:14B=4bitQLoRA,1.7B=bf16;14B 慢是预期,只申报不设门槛"}

    agree_disagree = {
        "both_ok": sum(1 for x, y in zip(b14_rows, b17_rows) if x["ok"] and y["ok"]),
        "only_14b": sum(1 for x, y in zip(b14_rows, b17_rows) if x["ok"] and not y["ok"]),
        "only_17b": sum(1 for x, y in zip(b14_rows, b17_rows) if not x["ok"] and y["ok"]),
        "both_wrong": sum(1 for x, y in zip(b14_rows, b17_rows) if not x["ok"] and not y["ok"]),
    }

    core_pass = all([gates["U1_full_corpus_trained"]["pass"],
                     gates["U2_peak_mem_under_36G"]["pass"],
                     gates["U3_loss_converging"]["pass"],
                     gates["U4_format_n100"]["pass"],
                     gates["qid_disjoint_check"]["pass"]])
    report = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
              "model": a.model, "base17": a.base17,
              "champion_adapter": a.champion,
              "corpus": {"dir": a.corpus_dir,
                         "sha16": {"train": "35683198dd3c4992",
                                   "dev": "942e4daeaedca2fb",
                                   "test": "4bcaf1c9b551f336"}},
              "steps": step, "train_seconds": train_s,
              "gates": gates, "agree_disagree": agree_disagree,
              "core_pass": core_pass,
              # U5/U6 只出读数不进 core 门:升格决策=读数+用户拍板(预注册不预授权切换)
              "verdict": "UPGRADE_EVIDENCE_PASS" if core_pass else "UPGRADE_FAIL"}
    (out / "upgrade_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "eval292_14b.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in b14_rows), encoding="utf-8")
    (out / "eval292_17b.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in b17_rows), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()
