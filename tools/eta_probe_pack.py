# -*- coding: utf-8 -*-
"""η 首检供给包:P2v1/v2 同 split 对照数据(两系统×八量),按操作性定义格式整理。
诚实缺口如实标注(v1 时延未实测等)。"""
import json
import time
from pathlib import Path

OUT = Path("runtime/eta_probe_pack_p2v1v2.json")

PACK = {
    "_meta": {
        "name": "eta_probe_pack_p2v1v2",
        "produced": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "purpose": ("eta=C/V first-pass probe data: two verifier systems on the SAME frozen split, "
                    "differing in architecture only. Per operational definitions in paper3-v1.1 "
                    "sec:operational (C = utility-per-bit; V = path-coverage x accuracy x truth-grade)."),
        "split_commitment": {
            "train": "35683198dd3c4992 (1162 rows)",
            "dev": "942e4daeaedca2fb (143 rows)",
            "test": "4bcaf1c9b551f336 (149 rows)",
            "frozen": True, "qid_grouped": True,
        },
        "probe_usage": ("v1 vs v2 are two points on the (C, V, latency, FLOPs) plane; "
                        "utility gain (+22.3pt) vs description-length and compute cost is the "
                        "existence question for eta's explanatory power."),
    },
    "systems": [
        {
            "id": "P2v1",
            "architecture": "frozen bge-m3 embeddings + linear head (isomorphic baseline)",
            "params_total": "560M embedder (frozen, shared infra) + 0.6M head (trainable)",
            "bits_estimate": {
                "embedder_fp32": "560e6 x 32 = 1.792e10 bits (pre-existing infra)",
                "head_fp32": "0.6e6 x 32 = 1.92e7 bits (task-specific)",
                "note": "task-specific bits vs pre-existing infra bits reported separately; "
                        "C computed both ways (marginal and total).",
            },
            "utility": {"test_binary_acc": 0.6622, "ece_10bin": 0.045,
                        "note": "66.22% floor = architectural ceiling (semantic-match regime)"},
            "latency": {
                "head_only_ms": "not measured (linear head, sub-ms by construction)",
                "end_to_end_ms": "not measured -- HONEST GAP; embedder pass dominates; "
                                 "same input pipeline as v2's tokenizer",
            },
            "flops_per_item_estimate": "embedder (560M x 2 x seq_len) + head (~1.2M); "
                                       "seq_len=768 token cap",
            "training_cost": "CPU-minutes (head only)",
        },
        {
            "id": "P2v2",
            "architecture": "Qwen3-1.7B 4-bit QLoRA (r16/alpha32) + three-state verbalizer",
            "params_total": "1.7B base (4-bit, pre-existing open weights) + 6.42M LoRA trainable",
            "bits_estimate": {
                "base_4bit": "1.7e9 x 4 = 6.8e9 bits (pre-existing infra)",
                "adapter": "6.42e6 x 16 (bf16) = 1.03e8 bits = 25.7 MB (task-specific)",
                "note": "task-specific adapter = 25.7MB; utility 88.51% sustained by it.",
            },
            "utility": {"test_binary_acc": 0.8851, "ece_10bin": 0.072,
                        "delta_vs_v1_pt": 22.3,
                        "u_states": "2/27 voluntary abstention on keyed rows (external protocol)"},
            "latency": {
                "single_p50_ms": 30.1, "single_p95_ms": 42.2, "batch_throughput_per_s": 118.33,
                "vram_gb": 5.92, "load_s": 8.7,
                "note": "MEASURED on A100-40G, bf16, seq<=768; per tools/hotpath eval 2026-10-01.",
            },
            "flops_per_item_estimate": "~1.7e9 x 2 x n_tokens forward; n_tokens~600 typical",
            "training_cost": "~35 min on 4090-48G (3 epochs to best-dev, early-stopped ep5 of 8)",
        },
    ],
    "derived_points": {
        "C_marginal_ratio": "v2/v1 = (0.8851/0.6622) / (1.03e8/1.92e7) = 1.337 / 5.365 = 0.249",
        "C_total_ratio": "v2/v1 = 1.337 / (6.9e9 / 1.79e10) = 1.337 / 0.385 = 3.47",
        "interpretation": ("Marginal (task-specific bits) view: v2 spends 5.4x the task bits for "
                           "1.34x utility -> C_marginal DROPS. Total-infra view: v2 uses 0.385x "
                           "the infra bits for 1.34x utility -> C_total RISES 3.5x. WHICH view "
                           "is correct is a REAL question for eta's definition, not a bug: "
                           "pre-existing open weights are effectively free infrastructure, "
                           "same as bge-m3 is for v1."),
        "latency_note": "v1 latency unmeasured blocks a strict latency-normalized comparison; "
                        "linear-head-only is sub-ms but embedder pass is shared. Flagged HONEST.",
    },
    "honest_gaps": [
        "v1 end-to-end latency unmeasured (only head is trivially fast)",
        "FLOPs are parameter-count estimates, not profiler-verified",
        "n=1 seed per system (split frozen; seed effect unquantified)",
        "utility is single-metric (binary acc); ECE given as secondary",
    ],
    "recompute": {
        "splits": "data/paper3_snapshot/split_*.jsonl (anonymized, sha-committed)",
        "v2_training_script": "tools/train_judge_lora.py (prereg docs/metering/P2_JUDGE_TRAINING_PREREG_20260930.md)",
        "v2_artifacts": "runtime/judge_lora_p2v2/ (adapter 25.7MB + eval_report.json + run.log)",
        "v1_report": "eval_report_v1_failing (in-repo, 66.22% as-reported ceiling)",
    },
}

OUT.write_text(json.dumps(PACK, ensure_ascii=False, indent=1), encoding="utf-8")
print("pack written:", OUT, len(json.dumps(PACK)), "bytes")
# 快速自检:derived 数字复算
c_m = (0.8851 / 0.6622) / (1.03e8 / 1.92e7)
c_t = (0.8851 / 0.6622) / (6.9e9 / 1.79e10)
print(f"recheck C_marginal={c_m:.3f} C_total={c_t:.2f}")
