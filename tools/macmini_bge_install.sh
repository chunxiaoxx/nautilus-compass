#!/bin/bash
# BGE-m3 嵌入服务 · Mac mini M6 (Apple Silicon) 一键安装 · 2026-10-14
# 用法: 在 Mac mini 终端粘贴运行(curl 拉本脚本或直接粘贴全部内容)
# 端点契约与 A100 embed_server_v2 完全同构(GET /health, POST /embed {texts:[...]})
set -e
echo "== BGE embed server · Mac mini 安装开始 =="

# 1. Python 环境(uv 最快,若已有 uv/python3.10+ 跳过)
if ! command -v uv &>/dev/null; then
    echo "-- 安装 uv ..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# 2. 服务目录+虚拟环境
mkdir -p ~/bge-embed && cd ~/bge-embed
if [ ! -d ".venv" ]; then
    uv venv .venv --python 3.11
fi
source .venv/bin/activate

# 3. 依赖(torch MPS 版+fastapi+sentence-transformers)
echo "-- 安装依赖(torch MPS + sentence-transformers,约 3-5 分钟)..."
uv pip install --quiet torch torchvision sentence-transformers fastapi "uvicorn[standard]" hf_transfer

# 4. 模型下载(bge-m3 ~2GB,hf-mirror 国内加速)
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=1
echo "-- 下载 BGE-m3 模型(~2GB,一次性的)..."
python -c "
from sentence_transformers import SentenceTransformer
m = SentenceTransformer('BAAI/bge-m3', device='mps')
print('model loaded on', m.device)
"

# 5. 服务脚本(embed_server_v2 同构端点)
cat > server.py <<'EOF'
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import torch, time

app = FastAPI()
model = SentenceTransformer("BAAI/bge-m3", device="mps")

class Req(BaseModel):
    texts: list

@app.get("/health")
def health():
    return {"ok": True, "model": "bge-m3-macmini-mps", "version": "1.0.0"}

@app.post("/embed")
def embed(req: Req):
    t0 = time.time()
    vecs = model.encode(req.texts, normalize_embeddings=True)
    ms = int((time.time() - t0) * 1000)
    return {"ok": True, "embeddings": [v.tolist() for v in vecs], "ms": ms}
EOF

# 6. LaunchD 常驻(开机自启+崩溃自拉)
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/com.nautilus.bge-embed.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.nautilus.bge-embed</string>
  <key>ProgramArguments</key><array>
    <string>$HOME/bge-embed/.venv/bin/python</string>
    <string>-m</string><string>uvicorn</string>
    <string>server:app</string><string>--host</string><string>0.0.0.0</string>
    <string>--port</string><string>8400</string>
  </array>
  <key>WorkingDirectory</key><string>$HOME/bge-embed</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict></plist>
EOF
launchctl unload ~/Library/LaunchAgents/com.nautilus.bge-embed.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.nautilus.bge-embed.plist

# 7. 验证
sleep 6
echo "-- 验证 --"
curl -s http://127.0.0.1:8400/health || echo "(服务启动中,稍候 30s 再试)"
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "<Mac-mini-IP>")
echo ""
echo "== 安装完成 =="
echo "服务地址: http://${IP}:8400  (局域网)"
echo "请把上面的 IP 告知 compass(Windows 主力机)完成路由切换"
