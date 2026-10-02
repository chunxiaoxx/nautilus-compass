#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-full 表征提取(判据档 v2:docs/metering/P0_FULL_PREREG_V2_20261002.md,F1/F4)。

冻结主干倒数第二层 hidden states,mean pooling(attention mask 加权)。
运行:A100(GPU);前置守门=无计算进程才启动(G1 占用时 exit 1,绝不抢)。
用法:python3 p0_full_extract.py --model /root/vdd2/models/Qwen3-14B --tag q14
输出:runtime/p0_full/{effect,cause}_{tag}.npy + meta_{tag}.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

MAXLEN = 1024
BATCH = 8  # F4:批 ≤8


def gate_gpu_free() -> None:
    r = subprocess.run(["nvidia-smi", "--query-compute-apps=pid",
                        "--format=csv,noheader"], capture_output=True, text=True)
    procs = [l for l in (r.stdout or "").splitlines() if l.strip()]
    if procs:
        sys.exit(f"[gate] GPU 有计算进程({procs[:3]}),G1 空窗纪律:绝不抢,退出")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", required=True, help="q14 / turbo")
    ap.add_argument("--data", default="anchor_v01.jsonl")
    ap.add_argument("--out", default="p0_full_out")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    gate_gpu_free()
    rows = [json.loads(l) for l in
            Path(a.data).read_text(encoding="utf-8").splitlines() if l.strip()]
    eff = [r["effect_text"] for r in rows]
    cau = [r["cause_text"] for r in rows]
    ids = [r["anchor_id"] for r in rows]
    print(f"[load] {len(rows)} anchors ×2 侧 · model={a.model}")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)
    tok.pad_token = tok.pad_token or tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        a.model, dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    n_layers = model.config.num_hidden_layers

    def encode(texts: list[str]) -> "torch.Tensor":
        out = []
        t0 = time.time()
        for i in range(0, len(texts), BATCH):
            enc = tok(texts[i:i + BATCH], return_tensors="pt", padding=True,
                      truncation=True, max_length=MAXLEN).to("cuda")
            with torch.no_grad():
                hs = model(**enc, output_hidden_states=True).hidden_states
            h = hs[-2]  # 倒数第二层
            m = enc["attention_mask"].unsqueeze(-1).to(h.dtype)
            v = (h * m).sum(1) / m.sum(1)  # mean pooling(mask 加权)
            out.append(v.float().cpu())
            if (i // BATCH) % 40 == 0:
                print(f"  {i}/{len(texts)} ({time.time()-t0:.0f}s)", flush=True)
        return torch.cat(out)

    out_dir = Path(a.out)
    out_dir.mkdir(exist_ok=True)
    meta = {"model": a.model, "tag": a.tag, "n": len(rows),
            "layer": f"hidden_states[-2] of {n_layers}", "pooling": "mask-mean",
            "maxlen": MAXLEN, "batch": BATCH,
            "ids_sha16": hashlib.sha256(
                ("\n".join(ids)).encode()).hexdigest()[:16]}
    fails = 0
    for name, texts in (("effect", eff), ("cause", cau)):
        t0 = time.time()
        E = encode(texts)
        f = out_dir / f"{name}_{a.tag}.npy"
        import numpy as np
        arr = E.numpy()
        np.save(f, arr)
        fails += int((~np.isfinite(arr)).any())
        meta[name] = {"file": f.name, "shape": list(arr.shape),
                      "sec": round(time.time() - t0, 1)}
        print(f"[save] {f} {arr.shape} {meta[name]['sec']}s")
    meta["F1_zero_fail"] = fails == 0
    (out_dir / f"meta_{a.tag}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
