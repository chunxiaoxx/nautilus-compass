#!/usr/bin/env python3
"""P3 实验通用 runner(engineering 票,不入岗)——exp2 系扫描用。

用法:exp_runner.py --tag exp2a --lr 5e-5 --epochs 3
口径:复用 train_judge_incremental_fixed 的 PROMPT_TMPL/sample_text;predict=完整
prompt 末位 logits;champion 基线复用 exp1 同机读数(reg=0.91/test=0.9128),
不重测(可比性:同机同 session 段同口径,刚测)。
预注册 exp2 判读规则:Δtest≥+1pt 且 flip≤1 记"配方候选";全部不过线=结论
"重训无增益坐实,首单增益等 delta"——先注册后跑,不事后挑读数。
"""
import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import torch

if not hasattr(torch, "float8_e8m0fnu"):
    torch.float8_e8m0fnu = torch.bfloat16  # noqa

import random

spec = importlib.util.spec_from_file_location("tji", "/root/tools/train_judge_incremental_fixed.py")
tji = importlib.util.module_from_spec(spec)
sys.modules["tji"] = tji
spec.loader.exec_module(tji)

from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "/root/.cache/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master"
CHAMP = "/root/runtime/judge_lora_p2v2/best_lora"
CORPUS = Path("/root/runtime/verdict_corpus")
EXP = Path("/root/runtime/judge_lora_p3/exp")
CHAMP_BASELINE = {"reg": 0.91, "test": 0.9128, "source": "exp1_champion_same_session"}

ap = argparse.ArgumentParser()
ap.add_argument("--tag", required=True)
ap.add_argument("--lr", type=float, required=True)
ap.add_argument("--epochs", type=int, required=True)
a = ap.parse_args()

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


def predict(rows):
    model.eval()
    preds = {}
    with torch.no_grad():
        for ids, att, _, rid in rows:
            lg = model(input_ids=ids.unsqueeze(0).cuda(),
                       attention_mask=att.unsqueeze(0).cuda()).logits[0, -1, :]
            pr = torch.softmax(lg[tids], dim=-1)
            preds[rid] = (tji.LABELS[int(pr.argmax())], round(float(pr.max()), 4))
    return preds


def acc(preds, rows):
    return sum(1 for r in rows if preds[r["id"]][0] == r["truth_label"]) / len(rows)


train_rows = tji.load_rows(CORPUS / "split_train.jsonl")
reg = tji.load_rows(CORPUS / "reg100.jsonl")
test = tji.load_rows(CORPUS / "split_test.jsonl")
train_data = encode(train_rows)
ev = encode(reg) + encode(test)

opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                        lr=a.lr, weight_decay=1e-4)
champ = predict(ev)  # champion 臂逐条必须在训练前(训练改 adapter 权重)
model.train()
losses = []
for ep in range(a.epochs):
    random.Random(20261004 + ep).shuffle(train_data)
    tot = 0.0
    for ids, att, lab, _ in train_data:
        ans = tok.encode(tji.LABELS[lab], add_special_tokens=False)[0]
        ans = ans[0] if isinstance(ans, list) else ans
        inp = torch.cat([ids, torch.tensor([ans])]).unsqueeze(0).cuda()
        attx = torch.cat([att, torch.tensor([1])]).unsqueeze(0).cuda()
        logits = model(input_ids=inp[:, :-1], attention_mask=attx[:, :-1]).logits[0, -1, :]
        loss = -torch.log_softmax(logits[tids], dim=-1)[lab]
        loss.backward()
        opt.step()
        opt.zero_grad()
        tot += float(loss)
    losses.append(round(tot / len(train_data), 4))
    print(f"[{a.tag} ep {ep}] loss={losses[-1]} t={time.time()-t0:.0f}s", flush=True)

chall = predict(ev)
champ_reg, chall_reg = acc(champ, reg), acc(chall, reg)
champ_test, chall_test = acc(champ, test), acc(chall, test)
summary = {
    "exp": a.tag, "ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
    "nature": "engineering_exp_not_for_promotion",
    "config": {"train_n": len(train_rows), "epochs": a.epochs, "lr": a.lr,
               "precision": "auto(bf16)", "init": "champion_hot_start"},
    "loss_per_ep": losses,
    "champion": {"reg_acc": round(champ_reg, 4), "test_acc": round(champ_test, 4)},
    "challenger": {"reg_acc": round(chall_reg, 4), "test_acc": round(chall_test, 4)},
    "delta_reg": round(chall_reg - champ_reg, 4),
    "delta_test": round(chall_test - champ_test, 4),
    "reg100_gold_flips": sum(1 for r in reg if champ[r["id"]][0] == r["truth_label"]
                             and chall[r["id"]][0] != r["truth_label"]),
}
EXP.mkdir(parents=True, exist_ok=True)
(EXP / f"{a.tag}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
(EXP / "adapters").mkdir(exist_ok=True)
model.save_pretrained(EXP / "adapters" / a.tag)
print(json.dumps({k: summary[k] for k in ("exp", "delta_reg", "delta_test", "reg100_gold_flips")}),
      flush=True)
print(f"[done:{a.tag}] t={time.time()-t0:.0f}s", flush=True)
