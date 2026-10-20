#!/bin/bash
# bge-reranker-v2-m3 服务 · Mac mini M6 一键安装 · 2026-10-20(R561 用户拍板: rerank 迁 Mac mini)
# 用法: Mac mini 终端先  export MAC_RERANK_TOKEN=<compass 侧给的值>  再粘贴本脚本全部内容回车
# 协议与 A100 a100_rerank_svc.py 同构(9879 JSON-line, action=rerank), 端口 8401;复用 ~/bge-embed venv
set -e
TOKEN="${MAC_RERANK_TOKEN:-}"
[ -z "$TOKEN" ] && { echo "❌ 先 export MAC_RERANK_TOKEN=<compass 侧给的值>,再重新粘贴"; exit 1; }
echo "== rerank server · Mac mini 安装开始 =="

# 0. 前置: BGE 嵌入服务装过的 venv(torch MPS + transformers 全在)
cd ~/bge-embed 2>/dev/null || { echo "❌ ~/bge-embed 不在——先装 BGE 嵌入服务(macmini_bge_install.sh)"; exit 1; }
source .venv/bin/activate

# 1. 模型下载(一次,~2.3GB,hf-mirror 加速)
export HF_ENDPOINT=https://hf-mirror.com
python - <<'PY'
from huggingface_hub import snapshot_download
p = snapshot_download("BAAI/bge-reranker-v2-m3")
print("model at", p)
PY

# 2. token 落盘(服务端校验用;与 compass 侧 ~/.claude/.cache/a100_rerank_token 同值)
printf '%s' "$TOKEN" > "$HOME/bge-embed/rerank_token"
chmod 600 "$HOME/bge-embed/rerank_token"

# 3. 服务脚本(裸 transformers;MPS fp32——fp16 对 XLM-R 分类头在 MPS 上不稳)
cat > "$HOME/bge-embed/rerank_server.py" <<'EOF'
import json, socketserver, time
from pathlib import Path
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL = "BAAI/bge-reranker-v2-m3"
PORT = 8401
TOKEN_FILE = Path.home() / "bge-embed" / "rerank_token"
DEV = "mps" if torch.backends.mps.is_available() else "cpu"
_tok = _model = None
T0 = time.time()

def get_model():
    global _tok, _model
    if _model is None:
        t = time.time()
        _tok = AutoTokenizer.from_pretrained(MODEL)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL).to(DEV).eval()
        print(f"[rerank-svc] model loaded on {DEV} in {time.time()-t:.0f}s", flush=True)
    return _tok, _model

@torch.no_grad()
def score(query, docs):
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
            self.wfile.write(json.dumps({"ok": True,
                "scores": [round(float(s), 4) for s in scores],
                "ms": round((time.time() - t) * 1000),
                "uptime_s": round(time.time() - T0)}).encode() + b"\n")
        except Exception as e:
            try:
                self.wfile.write(json.dumps({"ok": False, "error": str(e)[:200]}).encode() + b"\n")
            except Exception:
                pass

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == "__main__":
    get_model()  # 预热后再 listen
    print(f"[rerank-svc] listening 0.0.0.0:{PORT}", flush=True)
    with Server(("0.0.0.0", PORT), Handler) as srv:
        srv.serve_forever()
EOF

# 4. LaunchD 常驻(开机自启+崩溃自拉)
mkdir -p ~/Library/LaunchAgents
cat > "$HOME/Library/LaunchAgents/com.nautilus.bge-rerank.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.nautilus.bge-rerank</string>
  <key>ProgramArguments</key><array>
    <string>$HOME/bge-embed/.venv/bin/python</string>
    <string>$HOME/bge-embed/rerank_server.py</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict></plist>
EOF
launchctl unload "$HOME/Library/LaunchAgents/com.nautilus.bge-rerank.plist" 2>/dev/null || true
launchctl load "$HOME/Library/LaunchAgents/com.nautilus.bge-rerank.plist"

# 5. 自验(等预热,最多 60s)
echo "-- 等模型预热(首次 10-30s)..."
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  sleep 5
  R=$(python - <<PY
import socket, json
try:
    s = socket.create_connection(("127.0.0.1", 8401), timeout=4)
    s.sendall((json.dumps({"action": "rerank", "query": "测试查询",
                           "docs": ["相关文档内容", "无关的别的内容"],
                           "token": "$TOKEN"}) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        buf += s.recv(4096)
    print(buf.decode())
except Exception as e:
    print("WAIT", e)
PY
)
  case "$R" in
    *'"ok": true'*|*'"ok":true'*) echo "✅ 自验通过: $R"; break;;
    *) echo "  (${i}/12) $R";;
  esac
done

IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "<Mac-mini-IP>")
echo "== 安装完成 =="
echo "服务地址: ${IP}:8401 · 请回告 compass 侧做跨机联调(Windows→8401 实弹)"
