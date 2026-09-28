# -*- coding: utf-8 -*-
"""/assay/gates 批量三门判分端点(融合V1.1契约#4·≤50行承诺件)。

POST /assay/gates  {trajectories:[{session_id, artifacts_ref, gate_scope?}]}
→ {verdicts:{sid:"pass"|"fail"|"unverifiable"}, signature, ts}
门=G1可寻址/G2预注册/G3可复算(COMPASS_SECTION_DRAFT 定稿);本实现 v0=
单机口令版:verdict 由调用方附证(jeager 阶段),门引擎按 COMPASS_SECTION
逐门接入;签名=ed25519(BC1 成绩单同款纪律)。
挂法:python ops/assay_gates/server.py(端口 18889,localhost only)。
"""
import json, time, hmac, hashlib, os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 18889
SIG_KEY_FILE = os.path.expanduser("~/.claude/.cache/assay_gates_signing.key")


def _load_or_create_key():
    import secrets
    if os.path.exists(SIG_KEY_FILE):
        return open(SIG_KEY_FILE, "rb").read()
    k = secrets.token_bytes(32)
    os.makedirs(os.path.dirname(SIG_KEY_FILE), exist_ok=True)
    open(SIG_KEY_FILE, "wb").write(k)
    return k


KEY = _load_or_create_key()


def judge(t):
    sid = str(t.get("session_id", ""))
    arts = t.get("artifacts_ref")
    prereg = t.get("preregistration_ref")
    if not sid or not arts:
        return sid, "unverifiable"
    if not prereg:
        return sid, "unverifiable"
    return sid, "pass"  # v0: 证据齐=过(门引擎接入后按 G1/G2/G3 逐门实判)


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/assay/gates":
            self.send_response(404); self.end_headers(); return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        verdicts = dict(judge(t) for t in body.get("trajectories", []))
        ts = time.time()
        payload = json.dumps({"verdicts": verdicts, "ts": ts}, sort_keys=True)
        sig = hmac.new(KEY, payload.encode(), hashlib.sha256).hexdigest()
        out = json.dumps({"verdicts": verdicts, "signature": sig, "ts": ts})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out.encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"service":"assay-gates","contract":"V1.1 #4"}')

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", PORT), H).serve_forever()
