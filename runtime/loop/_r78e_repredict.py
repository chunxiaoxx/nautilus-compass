"""R78e(远端执行):修正口径后重跑双臂预测(不重训,adapter 已有效)。"""
import json

import torch

if not hasattr(torch, "float8_e8m0fnu"):
    torch.float8_e8m0fnu = torch.bfloat16  # noqa: transformers5.x/torch2.6 补丁

import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("tji", "/root/tools/train_judge_incremental_fixed.py")
tji = importlib.util.module_from_spec(spec)
sys.modules["tji"] = tji
spec.loader.exec_module(tji)
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

MODEL = "/root/.cache/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master"
CORPUS = Path("/root/runtime/verdict_corpus")
tok = AutoTokenizer.from_pretrained(MODEL)
reg = tji.load_rows(CORPUS / "reg100.jsonl")
test = tji.load_rows(CORPUS / "split_test.jsonl")


def encode(rows):
    out = []
    for r in rows:
        ids = tok(tji.PROMPT_TMPL.format(content=tji.sample_text(r)), return_tensors="pt")
        out.append((ids.input_ids[0], ids.attention_mask[0],
                    tji.LABELS.index(r["truth_label"]), r["id"]))
    return out


ev = encode(reg) + encode(test)
tids = torch.tensor([tok.encode(l, add_special_tokens=False)[0] for l in tji.LABELS]).cuda()


def arm(adapter_path, out_f):
    m = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype="auto", device_map="cuda")
    m = PeftModel.from_pretrained(m, adapter_path)
    m.eval()
    rows = []
    with torch.no_grad():
        for ids, att, _, rid in ev:
            lg = m(input_ids=ids.unsqueeze(0).cuda(),
                   attention_mask=att.unsqueeze(0).cuda()).logits[0, -1, :]
            pr = torch.softmax(lg[tids], dim=-1)
            p = int(pr.argmax())
            rows.append({"id": rid, "pred": tji.LABELS[p],
                         "conf": round(float(pr[p]), 4)})
    Path(out_f).write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    del m
    torch.cuda.empty_cache()
    print("[done]", out_f, len(rows))


arm("/root/runtime/judge_lora_p2v2/best_lora",
    "/root/runtime/judge_lora_p3/evals/ticket_s3test_champion_preds.jsonl")
arm("/root/runtime/judge_lora_p3/out/ticket_s3test_challenger",
    "/root/runtime/judge_lora_p3/evals/ticket_s3test_challenger_preds.jsonl")
print("[all arms rewritten]")
