#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRECOR B/C 一致性回放 · compass bnb 版(R279)

与 v5@precor_replay.py 的三分歧修正(回函 B/C-SCRIPT-V2):
1) 一致率=判定 label 一致(pass/fail/insufficient_evidence 解析后比对),非输出逐字全等
   ——量化模型逐字全等几乎不可能,逐字口径会把 99% 门打全假红;
2) 配置集照 PRECOR 冻结:精度 {bf16,fp16,int8-bnb,int4-nf4} × 解码 {greedy,T=0.3};
3) prompt=现役训练模板族(train_judge_baseline v2 / train_judge14b_smoke 同款:
   PROMPT_TMPL+sample_text 剔除 judge_output 作弊通道),非通用 chat 模板。
模板自验证判据:bf16-greedy 在 split_test 的三态 acc 应≈0.885(生产评测值);
显著偏低=模板失配,实验作废并回函,不判门。

用法:A100 上 python precor_replay_bnb.py --out /root/vdd4/robust_exp/matrix.csv
"""
import argparse, csv, json, sys, time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE = "/root/vdd4/modelscope/models/Qwen--Qwen3-1.7B"
ADAPTER = "/root/vdd4/adapters/best_lora"  # sha16=dbcbab6fd1ff5821
CORPUS_DIR = "/root/vdd4/robust_exp/corpus"

PROMPT_TMPL = """You are a verification judge. Given the criteria, the submitted
artifact, and the official reference, decide whether the response is correct.

{content}

Verdict (one word: pass / fail / insufficient_evidence):"""

LABELS = ["pass", "fail", "insufficient_evidence"]


def sample_text(s: dict) -> str:
    """train_judge_baseline v2 口径:只含工件本体,剔除 judge_output(作弊通道)。"""
    a = s.get("artifact", {})
    parts = [f"criteria: {s.get('criteria_ref', '')[:120]}"]
    for k in ("question", "response", "model_answer", "official_truth",
              "answer_gold", "reason", "rationale"):
        if a.get(k) is not None:
            parts.append(f"{k}: {str(a[k])[:400]}")
    return "\n".join(parts)[:1500]


def parse_label(text: str):
    t = text.strip().lower()
    for lab in LABELS:
        if t.startswith(lab):
            return lab
    for lab in LABELS:  # 容错:首词含 label
        if lab in t.split()[:3]:
            return lab
    return None


def load_rows():
    rows = []
    for name in ("split_test_v1.jsonl", "split_dev_v1.jsonl"):
        for l in open(Path(CORPUS_DIR) / name, encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                rows.append({
                    "qid": (r.get("artifact") or {}).get("qid") or r.get("id"),
                    "truth": r.get("truth_label"),
                    "prompt": PROMPT_TMPL.format(content=sample_text(r)),
                })
    # qid 去重(防泄漏口径同 corpus_pipeline)
    seen, out = set(), []
    for r in rows:
        if r["qid"] not in seen:
            seen.add(r["qid"])
            out.append(r)
    return out


def load_model(dtype_cfg: str):
    kw = {"device_map": "cuda"}
    if dtype_cfg == "bf16":
        kw["torch_dtype"] = torch.bfloat16
    elif dtype_cfg == "fp16":
        kw["torch_dtype"] = torch.float16
    elif dtype_cfg == "int8":
        kw.update(load_in_8bit=True)
    elif dtype_cfg == "int4":
        kw.update(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                  bnb_4bit_compute_dtype=torch.bfloat16)
    else:
        raise ValueError(dtype_cfg)
    m = AutoModelForCausalLM.from_pretrained(BASE, **kw)
    m = PeftModel.from_pretrained(m, ADAPTER)
    m.eval()
    return m


def run_batch(model, tok, rows, do_sample, temperature, out_rows, cfg_name):
    right = 0
    for i, r in enumerate(rows):
        inputs = tok(r["prompt"], return_tensors="pt").to("cuda")
        kw = dict(max_new_tokens=6, pad_token_id=tok.eos_token_id)
        if do_sample:
            kw.update(do_sample=True, temperature=temperature, top_p=0.9)
        else:
            kw.update(do_sample=False)
        with torch.no_grad():
            out = model.generate(**inputs, **kw)
        text = tok.decode(out[0][inputs["input_ids"].shape[1]:],
                          skip_special_tokens=True)
        lab = parse_label(text)
        ok = (lab == r["truth"])
        right += int(ok)
        out_rows.append({"qid": r["qid"], "cfg": cfg_name, "label": lab,
                         "truth": r["truth"], "ok": int(ok)})
        if (i + 1) % 50 == 0:
            print(f"  [{cfg_name}] {i+1}/{len(rows)} acc={right/(i+1):.4f}",
                  flush=True)
    return right / len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/root/vdd4/robust_exp/matrix.csv")
    a = ap.parse_args()
    rows = load_rows()
    print(f"rows={len(rows)} (unique qid)", flush=True)
    tok = AutoTokenizer.from_pretrained(BASE)

    all_out = []
    accs = {}
    for dtype in ("bf16", "fp16", "int8", "int4"):
        print(f"== load {dtype}", flush=True)
        model = load_model(dtype)
        acc = run_batch(model, tok, rows, False, None, all_out, f"{dtype}-greedy")
        accs[f"{dtype}-greedy"] = acc
        print(f"== {dtype}-greedy 三态 acc={acc:.4f}", flush=True)
        del model
        torch.cuda.empty_cache()
        if dtype == "bf16":  # T 轨只在基线精度跑(PRECOR:T 读数披露不判门)
            model = load_model(dtype)
            acc = run_batch(model, tok, rows, True, 0.3, all_out, "bf16-T0.3")
            accs["bf16-T0.3"] = acc
            del model
            torch.cuda.empty_cache()

    # 一致率矩阵:各配置 vs bf16-greedy 的 label 一致率
    base = {o["qid"]: o["label"] for o in all_out if o["cfg"] == "bf16-greedy"}
    cfgs = [c for c in accs if c != "bf16-greedy"]
    print("\n== 一致率矩阵(vs bf16-greedy,判门线 0.99)", flush=True)
    for c in cfgs:
        pairs = [(o["label"], base[o["qid"]]) for o in all_out if o["cfg"] == c
                 and o["qid"] in base]
        agree = sum(1 for x, y in pairs if x == y) / len(pairs)
        verdict = "PASS" if agree >= 0.99 else "FAIL"
        print(f"  {c}: agree={agree:.4f} ({verdict})", flush=True)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["qid", "cfg", "label", "truth", "ok"])
        w.writeheader()
        w.writerows(all_out)
    print(f"rows_written={len(all_out)} -> {a.out}", flush=True)
    # 模板自验证门:bf16-greedy acc 显著偏低则实验作废
    if accs["bf16-greedy"] < 0.80:
        print("TEMPLATE-MISMATCH: bf16 acc 远低于生产评测 0.885,实验作废回函",
              flush=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
