# -*- coding: utf-8 -*-
"""实例端:诊断缺失文件 → hf-mirror 下载(重试x5)→ 完整性验证 → 启动训练。"""
import os, sys, time, glob

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 必须在 import hub 前设
from huggingface_hub import snapshot_download

MODEL = "Qwen/Qwen3-1.7B"

def diag():
    snaps = glob.glob(os.path.expanduser(
        "~/.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots/*"))
    if snaps:
        print("[diag] snapshot files:", sorted(os.listdir(snaps[0])))
    inc = glob.glob(os.path.expanduser(
        "~/.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/blobs/*.incomplete"))
    print(f"[diag] incomplete blobs: {len(inc)}")

def main():
    diag()
    path = None
    for attempt in range(1, 6):
        try:
            path = snapshot_download(MODEL, max_workers=4)
            break
        except Exception as e:
            print(f"[dl] attempt {attempt} failed: {type(e).__name__}: {e}", flush=True)
            if attempt == 5:
                sys.exit(2)
            time.sleep(15 * attempt)
    print("[dl] model at:", path)
    # 完整性: safetensors 总分片应 >= 3GB
    total = sum(os.path.getsize(f) for f in glob.glob(path + "/*.safetensors"))
    print(f"[verify] safetensors total: {total/1e9:.2f} GB")
    if total < 3e9:
        print("[verify] FAIL: too small"); sys.exit(3)
    print("[verify] PASS")

if __name__ == "__main__":
    main()
