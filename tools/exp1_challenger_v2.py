#!/usr/bin/env python3
"""exp1 · challenger v2 全量重训实验(engineering 票,不入岗)。

目的:P3 首训练单(delta≥200)触发前的配方实验——全量 split_train(1162 条)+
champion 热启动+全精度 3 epochs,读数对比 champion 基线(reg100+test149)。
判据(实验级,预注册):challenger acc 相对 champion Δ;REG-100 零翻转计数;
只记录不 promote,产物落 /root/runtime/judge_lora_p3/exp/,不触 delta 账本。
口径:复用 train_judge_incremental_fixed(R78 修复版)的 PROMPT_TMPL/sample_text,
predict=完整 prompt 末位 logits(截尾=40pt 错位教训)。
"""
import importlib.util
import json
import sys
import time
from pathlib import Path

import torch

if not hasattr(torch, "float8_e8m0fnu"):
    torch.float8_e8m0fnu = torch.bfloat16  # noqa: torch2.6 补丁(peft/transformers import 期)

import random

import importlib.util as _ilu
spec = _ilu.spec_from_file_location("tji", "/root/tools/train_judge_incremental_fixed.py")
tji = _ilu.module_from_spec(spec)
sys.modules["tji"] = tji
spec.loader.exec_module(tji)

from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "/root/.cache/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master"
CHAMP = "/root/runtime/judge_lora_p2v2/best_lora"
CORPUS = Path("/root/runtime/verdict_corpus")
EXP = Path("/root/runtime/judge_lora_p3/exp")
EPOCHS = 3
LR = 1e-4

t0 = time.time()
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype="auto", device_map="cuda")
model = PeftModel.from_pretrained(model, CHAMP, is_trainable=True)
label_ids = [tok.encode(l, add_special_tokens=False)[0] for l in tji.LABELS]
label_ids = [l[0] if isinstance(l, list) else l for l in label_ids]
tids = torch.tensor(label_ids).cuda()


def encode(rows):
    out = []
    for r in rows:
        ids = tok(tji.PROMPT_TMPL.format(content=tji.sample_text(r)), return_tensors="pt")
        out.append((ids.input_ids[0], ids.attention_mask[0],
                    tji.LABELS.index(r["truth_label"]), r["id"]))
    return out


def predict(rows, tag):
    model.eval()
    preds = {}
    with torch.no_grad():
        for ids, att, _, rid in rows:
            lg = model(input_ids=ids.unsqueeze(0).cuda(),
                       attention_mask=att.unsqueeze(0).cuda()).logits[0, -1, :]
            pr = torch.softmax(lg[tids], dim=-1)
            p = int(pr.argmax())
            preds[rid] = (tji.LABELS[p], round(float(pr[p]), 4))
    print(f"[preds:{tag}] n={len(preds)} t={time.time()-t0:.0f}s", flush=True)
    return preds


def acc(preds, rows):
    ok = sum(1 for r in rows if preds[r["id"]][0] == r["truth_label"])
    return ok / len(rows)


train_rows = tji.load_rows(CORPUS / "split_train.jsonl")
reg = tji.load_rows(CORPUS / "reg100.jsonl")
test = tji.load_rows(CORPUS / "split_test.jsonl")
print(f"[data] train={len(train_rows)} reg={len(reg)} test={len(test)}", flush=True)

ev = encode(reg) + encode(test)
champ_preds = predict(ev, "champion")
(champ_acc_reg, champ_acc_test) = (acc(champ_preds, reg), acc(champ_preds, test))
print(f"[champion] reg={champ_acc_reg:.4f} test={champ_acc_test:.4f}", flush=True)

train_data = encode(train_rows)
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                        lr=LR, weight_decay=1e-4)
model.train()
losses = []
for ep in range(EPOCHS):
    random.Random(20261004 + ep).shuffle(train_data)
    tot = 0.0
    for ids, att, lab, _ in train_data:
        ans = tok.encode(tji.LABELS[lab], add_special_tokens=False)[0]
        ans = ans[0] if isinstance(ans, list) else ans
        inp = torch.cat([ids, torch.tensor([ans])]).unsqueeze(0).cuda()
        attx = torch.cat([att, torch.tensor([1])]).unsqueeze(0).cuda()
        logits = model(input_ids=inp[:, :-1], attention_mask=attx[:, :-1]).logits[0, -1, :]
        probs = torch.log_softmax(logits[tids], dim=-1)
        loss = -probs[lab]
        loss.backward()
        opt.step()
        opt.zero_grad()
        tot += float(loss)
    losses.append(round(tot / len(train_data), 4))
    print(f"[ep {ep}] train_loss={losses[-1]} t={time.time()-t0:.0f}s", flush=True)

chall_preds = predict(ev, "challenger")
chal_acc_reg, chal_acc_test = acc(chall_preds, reg), acc(chall_preds, test)

flip = sum(1 for r in reg if champ_preds[r["id"]][0] == r["truth_label"]
           and chall_preds[r["id"]][0] != r["truth_label"])

summary = {
    "exp": "exp1_challenger_v2_fulltrain",
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
    "nature": "engineering_exp_not_for_promotion",
    "config": {"train_n": len(train_rows), "epochs": EPOCHS, "lr": LR,
               "precision": "auto(bf16)", "init": "champion_hot_start"},
    "loss_per_ep": losses,
    "champion": {"reg_acc": round(champ_acc_reg, 4), "test_acc": round(champ_acc_test, 4)},
    "challenger": {"reg_acc": round(chal_acc_reg, 4), "test_acc": round(chal_acc_test, 4)},
    "delta_reg": round(chal_acc_reg - champ_acc_reg, 4),
    "delta_test": round(chal_acc_test - champ_acc_test, 4),
    "reg100_gold_flips": flip,
    "verdict_rule": "记录不 promote;若 Δtest≥+1pt 且 flip=0 记首单热启动候选",
}
EXP.mkdir(parents=True, exist_ok=True)
(EXP / "exp1_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
model.save_pretrained(EXP / "exp1_challenger_v2")
print(json.dumps(summary, ensure_ascii=False, indent=1), flush=True)
print(f"[done] t={time.time()-t0:.0f}s", flush=True)
