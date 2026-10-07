#!/usr/bin/env python3
"""A100 bge-m3 GPU 嵌入服务(零新依赖:http.server+transformers)。
POST /embed {"texts":[...]} → {"embeddings":[[...]]};GET /health。
治 cloud daemon CPU 嵌入吞吐瓶颈(R301 方案:嵌入计算 GPU 化,×10-20 吞吐)。
"""
import json
import glob
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

BASES = (glob.glob('/root/vdd4/modelscope/models*/BAAI--bge-m3/snapshots/*')
         or glob.glob('/root/vdd4/modelscope/models/BAAI--bge-m3/snapshots/*')
         or ['/root/vdd4/modelscope/models/models/BAAI--bge-m3/snapshots/master'])
MODEL = BASES[0]
PORT = 8400

print(f'loading {MODEL} ...', flush=True)
t0 = time.time()
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModel.from_pretrained(MODEL, torch_dtype=torch.float16).cuda().eval()
print(f'loaded {time.time()-t0:.1f}s', flush=True)


@torch.no_grad()
def encode(texts):
    out = []
    for i in range(0, len(texts), 32):
        batch = tok(texts[i:i + 32], padding=True, truncation=True,
                    max_length=512, return_tensors='pt').to('cuda')
        h = model(**batch).last_hidden_state[:, 0]      # CLS
        h = torch.nn.functional.normalize(h, dim=-1)    # bge-m3 normalized
        out.extend(h.float().cpu().tolist())
    return out


class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._send(200, {'ok': True, 'model': MODEL})

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        try:
            req = json.loads(self.rfile.read(n))
            vecs = encode(req['texts'])
            self._send(200, {'embeddings': vecs})
        except Exception as e:
            self._send(500, {'error': str(e)})

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    print(f'serving on :{PORT}', flush=True)
    ThreadingHTTPServer(('0.0.0.0', PORT), H).serve_forever()
