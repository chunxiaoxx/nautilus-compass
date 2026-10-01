# -*- coding: utf-8 -*-
"""v1 时延补测:bge-m3 嵌入器在 CPU(与 9876 daemon 同生产环境)对同 split_test 149 条计时。
协议镜像 v2 的 A100 测(单条×60 P50/P95+批吞吐);头延迟亚毫秒如实注明忽略。"""
import json
import statistics
import time
from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer

MODEL = "BAAI/bge-m3"  # 本地 HF 缓存(daemon 同款)
SPLIT = Path("runtime/verdict_corpus/split_test.jsonl")
OUT = Path("runtime/v1_latency_probe.json")


def main():
    import sys
    sys.path.insert(0, "tools")
    from train_judge_lora import PROMPT_TMPL, sample_text  # 同输入管道

    rows = [json.loads(l) for l in SPLIT.read_text(encoding="utf-8").splitlines() if l.strip()]
    texts = [PROMPT_TMPL.format(content=sample_text(r)) for r in rows]

    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModel.from_pretrained(MODEL)
    model.eval()
    load_s = time.time() - t0
    print("loaded in", round(load_s, 1), "s | device: cpu (与 9876 daemon 生产环境一致)")

    def embed_one(txt):
        enc = tok(txt, return_tensors="pt", truncation=True, max_length=768)
        with torch.no_grad():
            out = model(**enc).last_hidden_state[:, 0, :]
        return out

    # warmup 3
    for t in texts[:3]:
        embed_one(t)

    lat = []
    for txt in texts[:60]:
        t1 = time.time()
        embed_one(txt)
        lat.append(time.time() - t1)
    lat.sort()
    p50 = statistics.median(lat) * 1000
    p95 = lat[int(len(lat) * 0.95) - 1] * 1000
    mean = statistics.mean(lat) * 1000

    t2 = time.time()
    n = 0
    with torch.no_grad():
        for i in range(0, len(texts), 8):
            batch = texts[i:i + 8]
            enc = tok(batch, return_tensors="pt", padding=True, truncation=True, max_length=768)
            model(**enc)
            n += len(batch)
    batch_s = time.time() - t2

    report = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "system": "P2v1 embedder pass (bge-m3, CPU)",
        "environment": "local CPU (same class as 9876 daemon production)",
        "note_v2_parity": "v2 measured on A100 bf16; v1's PRODUCTION environment is the CPU "
                          "daemon, so CPU is the deployment-faithful measurement. "
                          "Cross-hardware comparison flagged; head latency (<1ms) excluded.",
        "load_seconds": round(load_s, 1),
        "single_n": 60,
        "single_p50_ms": round(p50, 1),
        "single_p95_ms": round(p95, 1),
        "single_mean_ms": round(mean, 1),
        "batch_total": n, "batch_seconds": round(batch_s, 2),
        "throughput_per_s": round(n / batch_s, 2),
        "seq_cap": 768,
        "hardware": torch.get_num_threads(),
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
