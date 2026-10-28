#!/usr/bin/env bash
# IRT 全池自动对表——每 30 分钟从 fuel_trajectories 提取最新 judge 数据→IRT 批量→参数表自动更新
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
DB="postgresql://nautilus_user:nautilus2024@127.0.0.1:15432/nautilus_production"
JEV_DIR="/tmp/irt_jev_auto"
OUT="/Users/chunxiao.wang/Projects/nautilus-core/docs/ALI_IRT_POOL_LIVE.json"

mkdir -p "$JEV_DIR"

# 1. 从 DB 提取全部 judge 轨迹→JEV 格式
python3 - <<'PYEOF'
import json, os
from sqlalchemy import create_engine, text
eng = create_engine("postgresql://nautilus_user:nautilus2024@127.0.0.1:15432/nautilus_production")
with eng.connect() as conn:
    rows = conn.execute(text(
        "SELECT qid, trajectory FROM fuel_trajectories WHERE traj_id LIKE 'judge-%' ORDER BY created_at")).fetchall()
pool = {}
for qid, traj in rows:
    d = traj if isinstance(traj, dict) else json.loads(traj)
    model = (d.get('model','') or '').strip().lower()
    score = d.get('score')
    if not model or score is None: continue
    # 规范化模型名
    for full, short in [('glm5.3','glm'),('glm-5.3','glm'),('kimi-k3','kimi'),('k3','kimi'),
                        ('kimi-k3-ark','kimi_ark'),('qwen3.8-max','qwen'),('qwen3.8max','qwen'),
                        ('claude-opus-5-5','opus'),('opus-5-5','opus'),('gpt-6-astra','gpt')]:
        if model == full or model.startswith(full): model = short; break
    binary = 1 if score and float(score) == 1.0 else 0
    pool.setdefault(qid, {}).setdefault(model, {'runs': []})['runs'].append(binary)
    json.dump(pool, open('/tmp/irt_jev_auto/pool.json','w'), ensure_ascii=False)
PYEOF

# 2. IRT 批量跑
python3 "$DIR/irt_estimate.py" batch "$JEV_DIR/pool.json" > "$OUT" 2>/dev/null || true

# 3. 通报（如果有变化）
PREV="/Users/chunxiao.wang/Projects/nautilus-core/docs/ALI_IRT_POOL_LIVE.json"
if [ -f "$PREV" ] && ! diff -q "$OUT" "$PREV" > /dev/null 2>&1; then
    echo "IRT 参数表有更新: $(date '+%H:%M')"
    cp "$OUT" "$PREV"
fi
