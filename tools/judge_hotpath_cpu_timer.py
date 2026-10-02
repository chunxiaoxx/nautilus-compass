#!/usr/bin/env python3
"""#9 判分器热路径 · CPU 推理一例计时(2026-10-02)。

对照口径:JUDGE_HOTPATH_INTEGRATION_PLAN S2(ingest P95 增量 <100ms 线);
GPU 读数已有(R4:A100 P50=30.1ms/P95=42.2ms),本件测 CPU 是否可行。
prompt 组装与 tools/train_judge_lora.py 逐字同款(无作弊通道版)。

运行位置:A100 同机 CPU(G1 只占 GPU;torch 限 8 线程=判分器独立进程部署口径,不抢训练)。
用法:python3 judge_hotpath_cpu_timer.py <anchor_v0.jsonl> [model_path]
输出:stdout 读数 + hotpath_cpu_report.json
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

LABELS = ["pass", "fail", "insufficient_evidence"]
MODEL_DEFAULT = "/root/.cache/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master"
THREADS = 8  # 独立进程配额核;全 16 核会抢 G1 dataloader

PROMPT_TMPL = """You are a verification judge. Given the criteria, the submitted
artifact, and the official reference, decide whether the response is correct.

{content}

Verdict (one word: pass / fail / insufficient_evidence):"""


def sample_text(s: dict) -> str:  # 与 train_judge_lora.py 同款
    a = s.get("artifact", {})
    parts = [f"criteria: {s.get('criteria_ref', '')[:120]}"]
    for k in ("question", "response", "model_answer", "official_truth",
              "answer_gold", "reason", "rationale"):
        if a.get(k) is not None:
            parts.append(f"{k}: {str(a[k])[:400]}")
    return "\n".join(parts)[:1500]


def pct(xs: list, p: float) -> float:
    xs = sorted(xs)
    i = min(int(round(p * (len(xs) - 1))), len(xs) - 1)
    return xs[i]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    corpus = Path(sys.argv[1] if len(sys.argv) > 1 else "anchor_v0.jsonl")
    model_path = sys.argv[2] if len(sys.argv) > 2 else MODEL_DEFAULT

    rows = [json.loads(l) for l in
            corpus.read_text(encoding="utf-8").splitlines() if l.strip()][:8]
    prompts = [PROMPT_TMPL.format(content=sample_text(r)) for r in rows]
    tok_lens = " / ".join(str(len(p)) for p in prompts[:4]) + " chars 前4条"
    print(f"[load] corpus={corpus.name} n={len(rows)} ({tok_lens})")

    import torch
    torch.set_num_threads(THREADS)
    from transformers import AutoModelForCausalLM, AutoTokenizer

    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(model_path)
    tok.pad_token = tok.pad_token or tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype=torch.float32, device_map="cpu")
    model.eval()
    t_load = time.perf_counter() - t0
    print(f"[load] model={model_path} fp32 cpu threads={THREADS} "
          f"cold_load={t_load:.1f}s(惰性加载首判口径)")

    label_ids = [tok.encode(w, add_special_tokens=False)[0] for w in LABELS]

    def forward_single(p: str) -> str:
        ids = tok(p, return_tensors="pt")
        with torch.no_grad():
            logits = model(**ids).logits[0, -1]
        return LABELS[max(range(3), key=lambda i: logits[label_ids[i]].item())]

    # 预热 2 + 单例 10 次
    forward_single(prompts[0]); forward_single(prompts[1])
    single, verdicts = [], []
    for p in prompts:  # 8 条各测 1 次 + 首条多测补足 10
        t0 = time.perf_counter()
        verdicts.append(forward_single(p))
        single.append((time.perf_counter() - t0) * 1000)
    for _ in range(2):
        t0 = time.perf_counter()
        forward_single(prompts[0])
        single.append((time.perf_counter() - t0) * 1000)

    # 批 8(padding 右侧,取每行末位 logits)×5 次
    enc = tok(prompts, return_tensors="pt", padding=True)
    batch = []
    for _ in range(5):
        t0 = time.perf_counter()
        with torch.no_grad():
            logits = model(**enc).logits
        last = (enc["attention_mask"].sum(dim=1) - 1)  # 每行最后非 pad 位
        for row, li in enumerate(last):
            lv = logits[row, li]
            verdicts[row] = LABELS[max(range(3),
                                       key=lambda i: lv[label_ids[i]].item())]
        batch.append((time.perf_counter() - t0) * 1000)

    report = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": "Qwen3-1.7B fp32 cpu", "threads": THREADS,
        "context": "G1 训练同机背景(load~0.7/16核);判分器 LoRA 不在机,底模单前向口径(LoRA 延迟增量<5% 不改量级)",
        "cold_load_s": round(t_load, 1),
        "single_ms": {"p50": round(pct(single, 0.5), 1),
                      "p95": round(pct(single, 0.95), 1),
                      "n": len(single)},
        "batch8_ms": {"p50": round(pct(batch, 0.5), 1),
                      "p95": round(pct(batch, 0.95), 1),
                      "n": len(batch)},
        "verdicts_sample": verdicts[:4],
        "gate_S2_100ms": bool(pct(single, 0.95) < 100),
    }
    out = Path("hotpath_cpu_report.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"[save] {out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
