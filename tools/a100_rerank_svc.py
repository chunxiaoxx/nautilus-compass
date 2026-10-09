#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A100 rerank 服务 v2(R450): 裸 transformers 实现(零新依赖,H2 实验同款口径)。

  req:  {"action":"rerank","query":"...","docs":["..."],"token":"..."}\\n
  resp: {"ok":true,"scores":[...],"ms":N} | {"ok":false,"error":"..."}\\n
"""
import json
import socket
import socketserver
import time
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL = "/root/vdf/models/bge-reranker-v2-m3"
PORT = 9879
TOKEN_FILE = Path("/root/.compass_rerank_token")
DEV = "cuda"

_tok = _model = None
T0 = time.time()


def get_model():
    global _tok, _model
    if _model is None:
        t = time.time()
        _tok = AutoTokenizer.from_pretrained(MODEL)
        _model = AutoModelForSequenceClassification.from_pretrained(
            MODEL, torch_dtype=torch.float16).to(DEV).eval()
        print(f"[rerank-svc] model loaded in {time.time()-t:.0f}s", flush=True)
    return _tok, _model


@torch.no_grad()
def score(query: str, docs: list) -> list:
    tok, model = get_model()
    inp = tok([[query, d] for d in docs], padding=True, truncation=True,
              max_length=512, return_tensors="pt").to(DEV)
    return model(**inp).logits.view(-1).float().tolist()


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            line = self.rfile.readline()
            if not line:
                return
            req = json.loads(line.decode("utf-8"))
            try:
                token_ok = req.get("token") == TOKEN_FILE.read_text().strip()
            except OSError:
                token_ok = False
            if not token_ok:
                self.wfile.write(json.dumps({"ok": False, "error": "auth"}).encode() + b"\n")
                return
            if req.get("action") != "rerank":
                self.wfile.write(json.dumps({"ok": False, "error": "bad action"}).encode() + b"\n")
                return
            q = req["query"][:1500]
            docs = [d[:3000] for d in (req.get("docs") or [])][:32]
            if not docs:
                self.wfile.write(json.dumps({"ok": False, "error": "no docs"}).encode() + b"\n")
                return
            t = time.time()
            scores = score(q, docs)
            dt = time.time() - t
            self.wfile.write(json.dumps({
                "ok": True, "scores": [round(float(s), 4) for s in scores],
                "ms": round(dt * 1000), "uptime_s": round(time.time() - T0),
            }).encode() + b"\n")
        except Exception as e:
            try:
                self.wfile.write(json.dumps({"ok": False, "error": str(e)[:200]}).encode() + b"\n")
            except Exception:
                pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    get_model()  # 预热
    print(f"[rerank-svc v2] listening :{PORT}", flush=True)
    with Server(("127.0.0.1", PORT), Handler) as srv:
        srv.serve_forever()
