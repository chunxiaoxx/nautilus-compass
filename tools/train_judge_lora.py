#!/usr/bin/env python3
"""P2 v2 · verdict-judge LoRA 训练(Qwen3-1.7B QLoRA + verbalizer 三态)。

预注册:docs/metering/P2_JUDGE_TRAINING_PREREG_20260930.md(J1-J6)
       + docs/plans/P2V2_LORA_PLAN_20260930.md(J7 v1/v2 对照≥+10pt)
运行环境:GPU 实例(4090 48G);输入=split 三折(sha 冻结)。
设计:verbalizer 下一 token 训练("pass"/"fail"/"insufficient_evidence"),
推理取三词 softmax=天然校准概率(ECE 直接可算)。
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "runtime" / "verdict_corpus"
OUT = ROOT / "runtime" / "judge_lora"
OUT.mkdir(parents=True, exist_ok=True)
MODEL_ID = "Qwen/Qwen3-1.7B"
LABELS = ["pass", "fail", "insufficient_evidence"]
SEED = 20260930
SHA_EXPECTED = {"split_train.jsonl": "35683198dd3c4992",
                "split_dev.jsonl": "942e4daeaedca2fb",
                "split_test.jsonl": "4bcaf1c9b551f336"}

PROMPT_TMPL = """You are a verification judge. Given the criteria, the submitted
artifact, and the official reference, decide whether the response is correct.

{content}

Verdict (one word: pass / fail / insufficient_evidence):"""


def sample_text(s: dict) -> str:  # 与 P2 v1 相同(v2 无作弊通道版)
    a = s.get("artifact", {})
    parts = [f"criteria: {s.get('criteria_ref', '')[:120]}"]
    for k in ("question", "response", "model_answer", "official_truth",
              "answer_gold", "reason", "rationale"):
        if a.get(k) is not None:
            parts.append(f"{k}: {str(a[k])[:400]}")
    return "\n".join(parts)[:1500]


def load(name):
    rows = [json.loads(l) for l in
            (CORPUS / name).read_text(encoding="utf-8").splitlines() if l.strip()]
    return [(PROMPT_TMPL.format(content=sample_text(r)), LABELS.index(r["truth_label"]),
             r["id"]) for r in rows]


def main():
    for name, want in SHA_EXPECTED.items():  # J5
        got = hashlib.sha256((CORPUS / name).read_bytes()).hexdigest()[:16]
        assert got == want, f"J5 FAIL {name}: {got} != {want}"
    print("[J5] split sha PASS")
    random.seed(SEED); torch.manual_seed(SEED)

    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model

    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, quantization_config=bnb, device_map={"": 0})
    model = get_peft_model(model, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]))
    model.print_trainable_parameters()

    label_ids = {lab: tok.encode(lab, add_special_tokens=False)[0] for lab in LABELS}
    print("[labels] first-token ids:", label_ids)

    def make_batch(pairs, train=True):
        texts, labs = [p[0] for p in pairs], [p[1] for p in pairs]
        enc = tok(texts, return_tensors="pt", padding=True, truncation=True,
                  max_length=768, padding_side="left").to(model.device)
        lab_tok = tok([LABELS[l] + tok.eos_token for l in labs], return_tensors="pt",
                      padding=True).to(model.device)
        input_ids = torch.cat([enc.input_ids, lab_tok.input_ids[:, :1]], dim=1)
        attn = torch.cat([enc.attention_mask, torch.ones_like(lab_tok.input_ids[:, :1])], dim=1)
        return input_ids, attn, lab_tok.input_ids[:, 0]

    train = load("split_train.jsonl")
    dev = load("split_dev.jsonl")
    test = load("split_test.jsonl")
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                            lr=1e-4, weight_decay=1e-4)

    def evaluate(data, batch=8):
        model.eval(); hit = n = 0
        confs, corrects = [], []
        with torch.no_grad():
            for i in range(0, len(data), batch):
                chunk = data[i:i + batch]
                input_ids, attn, gold = make_batch(chunk, train=False)
                logits = model(input_ids=input_ids[:, :-1], attention_mask=attn[:, :-1]).logits[:, -1, :]
                sel = torch.tensor([label_ids[l] for l in LABELS], device=logits.device)
                probs = torch.softmax(logits[:, sel], dim=-1)
                pred = probs.argmax(1)
                gold_bin = [0 if g == 0 else (1 if g == 1 else 2) for g in chunk and [p[1] for p in chunk]]
                for j, p in enumerate(pred.tolist()):
                    conf, ok = probs[j, p].item(), (p == chunk[j][1])
                    hit += ok; n += 1
                    confs.append(conf); corrects.append(1.0 if ok else 0.0)
        # ECE 10 桶
        ece = 0.0
        for b in range(10):
            lo, hi = b / 10, (b + 1) / 10
            m = [k for k, c in enumerate(confs) if lo <= c < hi + (1e-9 if b == 9 else 0)]
            if m:
                acc = sum(corrects[k] for k in m) / len(m)
                ece += len(m) / n * abs(acc - sum(confs[k] for k in m) / len(m))
        return hit / n, ece

    best_dev, best_state, best_ep = -1, None, 0
    B = 4
    for ep in range(8):
        model.train(); random.shuffle(train)
        for i in range(0, len(train), B):
            chunk = train[i:i + B]
            input_ids, attn, gold = make_batch(chunk)
            logits = model(input_ids=input_ids[:, :-1], attention_mask=attn[:, :-1]).logits[:, -1, :]
            sel = torch.tensor([label_ids[l] for l in LABELS], device=logits.device)
            logp = torch.log_softmax(logits[:, sel], dim=-1)
            off = torch.arange(len(chunk), device=logits.device)
            gold_sel = torch.tensor([ [0,1,2].index(p[1]) for p in chunk], device=logits.device)
            loss = F.nll_loss(logp, gold_sel)
            (loss / 2).backward()  # grad_accum 2
            if (i // B) % 2 == 1 or i + B >= len(train):
                opt.step(); opt.zero_grad()
        dv, ece_d = evaluate(dev)
        print(f"[ep {ep}] dev_acc={dv:.4f} dev_ece={ece_d:.4f}", flush=True)
        if dv > best_dev:
            best_dev, best_ep = dv, ep
            model.save_pretrained(OUT / "best_lora")
    # test 最终一次(J1/J2/J3/J7)
    from peft import PeftModel
    base = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, quantization_config=bnb, device_map={"": 0})
    model = PeftModel.from_pretrained(base, OUT / "best_lora")
    te, ece_t = evaluate(test)
    binary = [p for p in test if p[1] != 2]
    tb, _ = evaluate(binary)
    v1_floor = 0.6622
    report = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
              "best_dev_acc": round(best_dev, 4), "best_ep": best_ep,
              "J1_test_binary_acc": round(tb, 4), "J1_pass": tb >= 0.85,
              "J2_test_ece_10bin": round(ece_t, 4), "J2_pass": ece_t <= 0.10,
              "J3_U_test": sum(1 for p in test if p[1] == 2),
              "J7_v1_vs_v2": {"v1_floor": v1_floor, "v2": round(tb, 4),
                              "delta_pt": round((tb - v1_floor) * 100, 1),
                              "J7_pass": tb >= v1_floor + 0.10}}
    (OUT / "eval_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
