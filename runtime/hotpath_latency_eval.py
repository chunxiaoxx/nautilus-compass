# -*- coding: utf-8 -*-
"""判分器热路径评估:延迟-吞吐实测(P2v2 adapter,149 条 test)。

产出:单条延迟 P50/P95 + 批吞吐 → 判断能否进记忆写入热路径。
纯评估件:不改判分器、不动 split,test 只读(承 J5 冻结)。
"""
import json
import statistics
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, "/root/tools")
from train_judge_lora import LABELS, PROMPT_TMPL, sample_text  # noqa: E402

OUT = Path("/root/runtime/judge_lora/hotpath_eval.json")
MODEL_PATH = None  # 自动探测 modelscope 路径


def find_model():
    global MODEL_PATH
    import glob
    for pat in ("/root/.cache/modelscope/models/Qwen--Qwen3-1.7B/snapshots/*",
                "/root/.cache/modelscope/hub/models/Qwen/Qwen3-1.7B/*"):
        for h in glob.glob(pat):
            if glob.glob(h + "/*.safetensors"):
                MODEL_PATH = h
                return h
    raise SystemExit("model not found in modelscope cache")


def main():
    find_model()
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH, torch_dtype=torch.bfloat16, device_map={"": 0})
    model = PeftModel.from_pretrained(model, "/root/runtime/judge_lora/best_lora")
    model.eval()
    load_s = time.time() - t0

    label_ids = {lab: tok.encode(lab, add_special_tokens=False)[0] for lab in LABELS}
    sel = torch.tensor([label_ids[l] for l in LABELS], device="cuda")

    # 但注意:test 冻结只读——此处只计延迟,不判对错(读数不写回判据)
    import json as _j
    test = _j.loads('[]')
    corpus_dir = Path("/root/runtime/verdict_corpus")
    rows = [json.loads(l) for l in
            (corpus_dir / "split_test.jsonl").read_text().splitlines() if l.strip()]
    texts = [PROMPT_TMPL.format(content=sample_text(r)) for r in rows]

    lat_single = []
    with torch.no_grad():
        for txt in texts[:60]:  # 单条延迟:前 60 条逐条计时
            enc = tok(txt, return_tensors="pt", truncation=True,
                      max_length=768, padding_side="left").to("cuda")
            t1 = time.time()
            logits = model(**enc).logits[:, -1, :]
            _ = torch.softmax(logits[:, sel], dim=-1).argmax(1).item()
            torch.cuda.synchronize()
            lat_single.append(time.time() - t1)

    # 批吞吐:全 149 条按 batch=16
    t2 = time.time()
    n = 0
    with torch.no_grad():
        for i in range(0, len(texts), 16):
            enc = tok(texts[i:i + 16], return_tensors="pt", padding=True,
                      truncation=True, max_length=768, padding_side="left").to("cuda")
            _ = model(**enc).logits[:, -1, :]
            n += enc.input_ids.shape[0]
    batch_s = time.time() - t2

    lat_sorted = sorted(lat_single)
    report = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "model": MODEL_PATH,
        "load_seconds": round(load_s, 1),
        "single_n": len(lat_single),
        "single_p50_ms": round(statistics.median(lat_sorted) * 1000, 1),
        "single_p95_ms": round(lat_sorted[int(len(lat_sorted) * 0.95) - 1] * 1000, 1),
        "single_mean_ms": round(statistics.mean(lat_single) * 1000, 1),
        "batch_total": n, "batch_seconds": round(batch_s, 2),
        "throughput_per_sec": round(n / batch_s, 2),
        "vram_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2),
        "note": "纯延迟读数,test 仅推理未记判定(不触碰 J5 冻结语义)",
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
