#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E-NACRE-1:registry 条件化技能片路由实验(判据:PRECOR_ENACRE1_20261007.md v1.2)

三域片(rejudge/lme-d14/lme-d12)各训 QLoRA(200 步,锚回放 12%),评测双臂:
  A=现役单一大 LoRA(best_lora) · B=域片路由
读数:全域加权 acc(A/B)+各域 acc(A/B)+B 对 A 的 label 一致率。行级写 CSV。
判门:全域 B≥A+1.5pp;各域 B≥A;一致率≥99%。负结果照报。
"""
import argparse, csv, json, random, re, time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

BASE = "/root/vdd4/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master"
CHAMPION = "/root/vdd4/adapters/best_lora"          # A 臂(现役)
CORPUS = Path("/root/vdd4/robust_exp/corpus")
OUT = Path("/root/vdd4/robust_exp/enacre1")
PROMPT_TMPL = """You are a verification judge. Given the criteria, the submitted
artifact, and the official reference, decide whether the response is correct.

{content}

Verdict (one word: pass / fail / insufficient_evidence):"""
LABELS = ["pass", "fail", "insufficient_evidence"]
SEED, MAX_STEPS, BATCH = 20261007, 200, 4
ANCHOR_RATIO = 0.12


def domain_of(qid: str) -> str:
    parts = re.split(r"[-_]", qid)
    if parts[0] == "lme" and len(parts) > 1:
        return "lme-" + parts[1]
    return parts[0] if parts else "unknown"


def load_rows():
    rows = []
    for name in ("split_train_v1.jsonl", "split_dev_v1.jsonl", "split_test_v1.jsonl"):
        for l in open(CORPUS / name, encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                qid = (r.get("artifact") or {}).get("qid") or r.get("id", "")
                rows.append({"split": name.split("_")[1], "qid": qid,
                             "domain": domain_of(qid),
                             "truth": r.get("truth_label"),
                             "prompt": PROMPT_TMPL.format(content=sample_text(r))})
    return rows


def sample_text(s: dict) -> str:
    a = s.get("artifact", {})
    parts = [f"criteria: {s.get('criteria_ref', '')[:120]}"]
    for k in ("question", "response", "model_answer", "official_truth",
              "answer_gold", "reason", "rationale"):
        if a.get(k) is not None:
            parts.append(f"{k}: {str(a[k])[:400]}")
    return "\n".join(parts)[:1500]


def train_domain(base_model, tok, train_rows, out_dir):
    from peft import LoraConfig, get_peft_model
    model = PeftWrap(base_model, out_dir)
    label_ids = {lab: tok.encode(lab, add_special_tokens=False)[0] for lab in LABELS}
    pairs = [(r["prompt"], LABELS.index(r["truth"])) for r in train_rows
             if r["truth"] in LABELS]
    random.shuffle(pairs)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                            lr=1e-4, weight_decay=1e-4)
    model.train()
    step = 0
    for i in range(0, len(pairs), BATCH):
        if step >= MAX_STEPS:
            break
        chunk = pairs[i:i + BATCH]
        enc = tok([c[0] for c in chunk], return_tensors="pt", padding=True,
                  truncation=True, max_length=768, padding_side="left").to(model.device)
        lab_tok = tok([LABELS[c[1]] for c in chunk], return_tensors="pt",
                      add_special_tokens=False, padding=True).to(model.device)
        input_ids = torch.cat([enc.input_ids, lab_tok.input_ids[:, :1]], dim=1)
        attn = torch.cat([enc.attention_mask, torch.ones_like(lab_tok.input_ids[:, :1])], dim=1)
        gold = torch.tensor([c[1] for c in chunk], device=model.device)
        logits = model(input_ids, attention_mask=attn).logits[:, -1, :]
        lid = torch.tensor([label_ids[lab] for lab in (LABELS[c[1]] for c in chunk)],
                           device=model.device)
        loss = torch.nn.functional.cross_entropy(logits, lid)
        loss.backward(); opt.step(); opt.zero_grad()
        step += 1
        if step % 50 == 0:
            print(f"  [{out_dir.name}] step {step}/{MAX_STEPS} loss={loss.item():.4f}", flush=True)
    model.save_pretrained(str(out_dir))
    del model
    torch.cuda.empty_cache()


class PeftWrap(torch.nn.Module):
    def __init__(self, base, out_dir):
        super().__init__()
        from peft import LoraConfig, get_peft_model
        self.out_dir = out_dir
        self.model = get_peft_model(base, LoraConfig(
            r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
            task_type="CAUSAL_LM", target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]))

    def forward(self, *a, **kw):
        return self.model(*a, **kw)

    def parameters(self):
        return self.model.parameters()

    def train(self, mode=True):
        self.model.train(mode)
        return self

    def save_pretrained(self, d):
        self.model.save_pretrained(d)

    @property
    def device(self):
        return self.model.device


def gen_label(model, tok, prompt):
    enc = tok(prompt, return_tensors="pt", truncation=True, max_length=768).to(model.device)
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=6, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    text = tok.decode(out[0][enc.input_ids.shape[1]:], skip_special_tokens=True)
    t = text.strip().lower()
    for lab in LABELS:
        if t.startswith(lab):
            return lab
    for lab in LABELS:
        if lab in t.split()[:3]:
            return lab
    return None


def evaluate(model, tok, rows, arm, csv_w):
    by_dom = {}
    right = 0
    for i, r in enumerate(rows):
        lab = gen_label(model, tok, r["prompt"])
        ok = int(lab == r["truth"])
        right += ok
        csv_w.writerow([r["qid"], arm, r["domain"], lab, r["truth"], ok])
        d = by_dom.setdefault(r["domain"], [0, 0])
        d[0] += ok; d[1] += 1
        if (i + 1) % 50 == 0:
            print(f"  [{arm}] {i+1}/{len(rows)} acc={right/(i+1):.4f}", flush=True)
    return right / len(rows), by_dom


def main():
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    random.seed(SEED); torch.manual_seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    eval_rows = [r for r in rows if r["split"] in ("dev", "test")]
    print(f"eval rows={len(eval_rows)}", flush=True)

    from peft import PeftModel
    tok = AutoTokenizer.from_pretrained(BASE)

    csv_f = open(OUT / "enacre1_results.csv", "w", newline="", encoding="utf-8")
    csv_w = csv.writer(csv_f)
    csv_w.writerow(["qid", "arm", "domain", "label", "truth", "ok"])

    # A 臂:现役
    print("== A arm: champion best_lora", flush=True)
    m = AutoModelForCausalLM.from_pretrained(
        BASE, torch_dtype=torch.bfloat16, device_map={"": 0})
    m = PeftModel.from_pretrained(m, CHAMPION); m.eval()
    accA, domA = evaluate(m, tok, eval_rows, "A-champion", csv_w)
    print(f"== A 全域 acc={accA:.4f} 域级={domA}", flush=True)
    del m; torch.cuda.empty_cache()

    # B 臂:三域片训练+路由评测
    train_rows = [r for r in rows if r["split"] == "train"]
    anchor = [r for r in train_rows]
    random.shuffle(anchor)
    anchor = anchor[:max(1, int(len(anchor) * ANCHOR_RATIO))]
    adapters = {}
    for dom in ("rejudge", "lme-d14", "lme-d12"):
        print(f"== train domain片 {dom}", flush=True)
        dom_train = [r for r in train_rows if r["domain"] == dom] + anchor
        base = AutoModelForCausalLM.from_pretrained(
            BASE, torch_dtype=torch.bfloat16, device_map={"": 0})
        dom_dir = OUT / f"adapter_{dom}"
        train_domain(base, tok, dom_train, dom_dir)
        adapters[dom] = str(dom_dir)

    # B 臂评测:逐域独立加载(避 peft 热切换)
    print("== B arm: domain routing", flush=True)
    accB, domB = 0, {}
    for dom in ("rejudge", "lme-d14", "lme-d12"):
        mm = AutoModelForCausalLM.from_pretrained(
            BASE, torch_dtype=torch.bfloat16, device_map={"": 0})
        mm = PeftModel.from_pretrained(mm, adapters[dom]); mm.eval()
        dom_rows = [r for r in eval_rows if
                    (r["domain"] if r["domain"] in adapters else "lme-d12") == dom]
        ok_n = 0
        for i, r in enumerate(dom_rows):
            lab = gen_label(mm, tok, r["prompt"])
            ok = int(lab == r["truth"]); ok_n += ok; accB += ok
            d = domB.setdefault(dom, [0, 0]); d[0] += ok; d[1] += 1
            csv_w.writerow([r["qid"], f"B-route({dom})", r["domain"], lab, r["truth"], ok])
            if (i + 1) % 50 == 0:
                print(f"  [B:{dom}] {i+1}/{len(dom_rows)} acc={ok_n/(i+1):.4f}", flush=True)
        del mm; torch.cuda.empty_cache()
    csv_f.close()

    n = len(eval_rows)
    print("== 判门(PRECOR_ENACRE1 v1.2)==", flush=True)
    print(f"A acc={accA:.4f} | B acc={accB/n:.4f} | Δ={accB/n-accA:+.4f} (主门≥+0.015)", flush=True)
    for dom, (ok, tot) in sorted(domB.items()):
        a_ok = domA.get(dom, (0, 1))
        print(f"  {dom}: B={ok/tot:.4f} A={a_ok[0]/a_ok[1]:.4f} (不回退门 B≥A)", flush=True)
    print("label 一致率(逐题)由 CSV 离线计算", flush=True)


if __name__ == "__main__":
    main()
