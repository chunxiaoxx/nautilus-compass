"""One-shot: verify torch+CUDA on T4 and pre-download bge-m3 + bge-reranker-v2-m3
into the HF cache so the compass daemon loads them locally. Run on T4."""
import time

import torch

print("torch", torch.__version__, "cuda_available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))

t0 = time.time()
print("downloading bge-m3 ...", flush=True)
from sentence_transformers import SentenceTransformer, CrossEncoder

m = SentenceTransformer("BAAI/bge-m3", device="cuda" if torch.cuda.is_available() else "cpu")
v = m.encode(["smoke test 中文"], normalize_embeddings=True)
print("bge-m3 OK dim", len(v[0]), f"{time.time() - t0:.0f}s", flush=True)

t1 = time.time()
print("downloading bge-reranker-v2-m3 ...", flush=True)
ce = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cuda" if torch.cuda.is_available() else "cpu")
s = ce.predict([("q", "doc 中文")])
print("reranker OK score", float(s[0]), f"{time.time() - t1:.0f}s", flush=True)
print("ALL MODELS READY", flush=True)
