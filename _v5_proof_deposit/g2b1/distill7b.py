# -*- coding: utf-8 -*-
"""蒸馏 PoC 7B · QLoRA SFT + pass@5 评测 一体化脚本(2026-08-24)。

阶段:
  eval_base   : base 7B 对 train6 + holdout8 pass@5
  train       : QLoRA 4bit (r32) on 轨迹 jsonl(多文件合并)
  eval_distill: distilled pass@5
用法: python3 distill7b.py eval_base|train|eval_distill [traces.jsonl...]
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MODEL_DIR_ENV = "QWEN7B_DIR"
OUT_DIR = "/root/distill7b_out"


def model_dir():
    d = os.environ.get(MODEL_DIR_ENV) or _find_model()
    assert d, "model dir not found"
    return d


def _find_model():
    base = Path.home() / ".cache" / "modelscope" / "hub" / "models"
    for p in base.rglob("config.json"):
        if "Qwen2.5-Coder-7B" in str(p):
            return str(p.parent)
    return None


def load_tasks():
    tr = json.load(open("/root/train_eval.json"))
    ho = json.load(open("/root/holdout.json"))
    return tr, ho


def solve_prompt(spec):
    return (spec["任务概括"] + "\n\n以下是 buggy 起点文件,请输出修正后的完整文件"
            "(仅标准库,不要解释,单个 ```python 代码块):\n```python\n"
            + spec["starter_inline"] + "\n```")


def gen_once(model, tok, prompt, temperature=0.7):
    msgs = [{"role": "user", "content": prompt}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    import torch
    ids = tok(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=1024, do_sample=temperature > 0,
                             temperature=max(temperature, 0.01), top_p=0.95)
    return tok.decode(out[0][ids["input_ids"].shape[1]:],
                      skip_special_tokens=True)


def verify(spec, text):
    m = re.search(r"```[a-zA-Z0-9]*\s*\n(.*?)```", text, re.DOTALL)
    fixed = m.group(1) if m else (text or "")
    with tempfile.TemporaryDirectory() as d:
        vp, cp = Path(d)/"v.py", Path(d)/"c.py"
        vp.write_text(spec["verifier_inline"], encoding="utf-8")
        cp.write_text(fixed, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(vp), str(cp)],
                               capture_output=True, timeout=120,
                               env={**os.environ, "PYTHONUTF8": "1"})
        except subprocess.TimeoutExpired:
            return False
    try:
        return bool(json.loads(r.stdout.decode("utf-8", "replace")).get("passed"))
    except Exception:
        return False


def do_eval(adapter=None, k=5, which="both"):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    md = model_dir()
    tok = AutoTokenizer.from_pretrained(md)
    model = AutoModelForCausalLM.from_pretrained(
        md, torch_dtype=torch.bfloat16, device_map="auto")
    if adapter:
        model = PeftModel.from_pretrained(model, adapter)
    model.eval()
    tr, ho = load_tasks()
    results = {}
    for name, tasks in (("train", tr), ("holdout", ho)):
        if which != "both" and which != name:
            continue
        passed_tasks = 0
        per = {}
        for t in tasks:
            ok = sum(1 for _ in range(k)
                     if verify(t["spec"], gen_once(model, tok, solve_prompt(t["spec"]))))
            per[t["uid"]] = ok
            passed_tasks += (ok > 0)
            print(f"[{name}] {t['uid']}: {ok}/{k}", flush=True)
        results[name] = {"pass_at_least_1": passed_tasks, "total": len(tasks), "per": per}
        print(f">>> {name}: pass@{k} 至少1次通过 {passed_tasks}/{len(tasks)}", flush=True)
    json.dump(results, open(f"{OUT_DIR}/eval_{adapter or 'base'}.json".replace('/', '_')[-60:], "w"))
    Path(OUT_DIR).mkdir(exist_ok=True)
    json.dump(results, open(Path(OUT_DIR) / f"eval_{(adapter or 'base').split('/')[-1]}.json", "w"),
              ensure_ascii=False, indent=1)
    return results


def do_train(trace_files):
    import torch
    from torch.utils.data import Dataset
    from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer,
                              TrainingArguments, BitsAndBytesConfig)
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    rows = []
    for f in trace_files:
        rows += [json.loads(l) for l in open(f)]
    print(f"traces: {len(rows)}", flush=True)
    md = model_dir()
    tok = AutoTokenizer.from_pretrained(md)
    tok.pad_token = tok.pad_token or tok.eos_token
    bnb = BitsAndBytesConfig(load_in_4bit=True,
                             bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16)
    model = AutoModelForCausalLM.from_pretrained(
        md, quantization_config=bnb, device_map="auto")
    model = prepare_model_for_kbit_training(model)
    lcfg = LoraConfig(r=32, lora_alpha=64, lora_dropout=0.05,
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                      "gate_proj", "up_proj", "down_proj"],
                      task_type="CAUSAL_LM")
    model = get_peft_model(model, lcfg)

    class DS(Dataset):
        def __init__(self):
            self.items = []
            for r in rows:
                p = tok(r["prompt"], add_special_tokens=False)["input_ids"]
                c = tok(r["completion"] + tok.eos_token,
                        add_special_tokens=False)["input_ids"]
                ids = (p + c)[:2048]
                labels = ([-100] * len(p) + c)[:2048]
                self.items.append((ids, labels))
        def __len__(self): return len(self.items)
        def __getitem__(self, i):
            ids, labels = self.items[i]
            return {"input_ids": ids, "labels": labels,
                    "attention_mask": [1] * len(ids)}
    ds = DS()
    pad_id = tok.pad_token_id
    from transformers import DataCollatorForSeq2Seq
    coll = DataCollatorForSeq2Seq(tok, model=model, padding=True,
                                  label_pad_token_id=-100, pad_to_multiple_of=8)
    args = TrainingArguments(
        output_dir=OUT_DIR, num_train_epochs=3, per_device_train_batch_size=1,
        gradient_accumulation_steps=8, learning_rate=2e-4, warmup_ratio=0.05,
        logging_steps=5, save_strategy="no", bf16=True, report_to=[])
    Trainer(model=model, args=args, train_dataset=ds, data_collator=coll).train()
    Path(OUT_DIR).mkdir(exist_ok=True)
    model.save_pretrained(f"{OUT_DIR}/adapter")
    print("TRAIN DONE ->", f"{OUT_DIR}/adapter", flush=True)


def _do_cross_eval(adapter=None, k=5):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    md = model_dir()
    tok = AutoTokenizer.from_pretrained(md)
    model = AutoModelForCausalLM.from_pretrained(md, torch_dtype=torch.bfloat16, device_map="auto")
    if adapter:
        model = PeftModel.from_pretrained(model, adapter)
    model.eval()
    tasks = json.load(open("/root/crossfam.json"))
    per = {}
    passed = 0
    for t in tasks:
        ok = sum(1 for _ in range(k)
                 if verify(t["spec"], gen_once(model, tok, solve_prompt(t["spec"]))))
        per[t["uid"]] = ok
        passed += (ok > 0)
        print(f"[cross] {t['uid'][:44]}: {ok}/{k}", flush=True)
    res = {"pass_at_least_1": passed, "total": len(tasks), "per": per}
    print(f">>> cross-family: pass@{k} 至少1次通过 {passed}/{len(tasks)}", flush=True)
    Path(OUT_DIR).mkdir(exist_ok=True)
    tag = (adapter or "base").split("/")[-1] or "base"
    json.dump(res, open(Path(OUT_DIR)/f"eval_cross_{tag}.json","w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    cmd = sys.argv[1]
    Path(OUT_DIR).mkdir(exist_ok=True)
    if cmd == "eval_base":
        do_eval()
    elif cmd == "train":
        do_train(sys.argv[2:])
    elif cmd == "eval_distill":
        do_eval(adapter=f"{OUT_DIR}/adapter")
    elif cmd == "eval_cross_base":
        _do_cross_eval(adapter=None)
    elif cmd == "eval_cross_distill":
        _do_cross_eval(adapter=f"{OUT_DIR}/adapter")
