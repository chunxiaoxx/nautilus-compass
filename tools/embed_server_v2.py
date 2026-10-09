#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""embed_server v2(FastAPI/uvicorn 栈 · 8400)——替换 R303 简易 http.server
(经 ssh 隧道链路 reset 的协议坑)。协议不变:POST /embed {"texts":[...]} →
{"embeddings":[[...]]};GET /health。bge-m3 fp16 cuda,归一化输出。
"""
import glob
import os

os.environ.setdefault("MODELSCOPE_CACHE", "/root/vdd4/modelscope")
import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModel, AutoTokenizer

MODEL_GLOB = "/root/vdd4/modelscope/models/models/BAAI--bge-m3/snapshots/master"
DEV = "cuda"
MAXLEN = 512

app = FastAPI(title="embed_server v2", version="2.0.0")
_state = {"model": None, "tok": None}


def get_model():
    if _state["model"] is None:
        path = MODEL_GLOB if os.path.isdir(MODEL_GLOB) else sorted(glob.glob(
            "/root/vdd4/modelscope/models/models/BAAI--bge-m3/snapshots/*"))[0]
        tok = AutoTokenizer.from_pretrained(path)
        model = AutoModel.from_pretrained(path, torch_dtype=torch.float16).to(DEV).eval()
        _state["model"], _state["tok"] = model, tok
    return _state["model"], _state["tok"]


class EmbedIn(BaseModel):
    texts: list


@torch.no_grad()
def _embed(texts: list) -> list:
    model, tok = get_model()
    enc = tok(texts, padding=True, truncation=True, max_length=MAXLEN,
              return_tensors="pt").to(DEV)
    out = model(**enc)
    vecs = out.last_hidden_state[:, 0]
    vecs = torch.nn.functional.normalize(vecs, dim=-1)
    return vecs.to(torch.float32).cpu().tolist()


@app.get("/health")
def health():
    return {"ok": True, "model": MODEL_GLOB if os.path.isdir(MODEL_GLOB)
            else "bge-m3", "version": "2.0.0-fastapi"}


@app.post("/embed")
def embed(inp: EmbedIn):
    return {"embeddings": _embed(inp.texts)}
