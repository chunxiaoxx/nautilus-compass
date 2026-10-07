#!/usr/bin/env python3
"""A100 嵌入服务功能+延迟实测(在 A100 上运行)。"""
import json
import time
import urllib.request

# 功能:单条 → 维度
body = json.dumps({"texts": ["hello world", "判分器部署纪律"]}).encode()
r = json.loads(urllib.request.urlopen(urllib.request.Request(
    "http://127.0.0.1:8400/embed", body,
    {"Content-Type": "application/json"}), timeout=60).read())
v = r["embeddings"][0]
print("dim:", len(v), "first3:", [round(x, 3) for x in v[:3]])

# 延迟:批量 32
for n in (1, 32, 128):
    texts = [f"测试判例条目 {i}" for i in range(n)]
    body = json.dumps({"texts": texts}).encode()
    t0 = time.time()
    r = json.loads(urllib.request.urlopen(urllib.request.Request(
        "http://127.0.0.1:8400/embed", body,
        {"Content-Type": "application/json"}), timeout=120).read())
    print(f"batch{n}: {time.time()-t0:.2f}s ({len(r['embeddings'])} vecs)")
