#!/usr/bin/env bash
# LongMemEval-S 检索三指标一键复算(P@1 / P@5 / MRR)
#
# 目标:独立复算 landing 页口径 0.890 / 0.978 / 0.929
#   = evidence docs/evidence/headhead_mem0_full500_20260826.json
#     节 S500_FINAL_v3_4type_dateanchor
#   = 4-type routing (ssu+ssp+ku+tr) + ZMM_DATE_ANCHOR=1 + hybrid, no reranker, GPU
#
# 前置:
#   1. 数据集 LongMemEval-S(500 题):默认 .cache/longmem_s.json(约 277MB,gitignored)。
#      无则从官方 repo 获取: https://github.com/xiaowu0162/LongMemEval
#      (国内镜像加速: export HF_ENDPOINT=https://hf-mirror.com)
#   2. 依赖: pip install sentence-transformers rank-bm25
#   3. bge-m3 模型首跑自动下载(约 2.2G,可设 HF_ENDPOINT 走镜像)。
#
# 用法:
#   bash scripts/reproduce_lmes_retrieval.sh            # 全量 500 题(GPU 推荐,CPU 慢)
#   SUBSET=12 bash scripts/reproduce_lmes_retrieval.sh  # 冒烟 12 题(验证管道通)
set -euo pipefail
cd "$(dirname "$0")/.."

DATASET="${ZMM_LONGMEMEVAL_PATH:-.cache/longmem_s.json}"
SUBSET="${SUBSET:-}"

echo "== [1/4] 依赖检查 =="
python - <<'PY'
import importlib
for m in ("sentence_transformers", "rank_bm25"):
    try:
        importlib.import_module(m)
        print(f"  ok  {m}")
    except ImportError:
        print(f"  MISSING {m}  ->  pip install {m}")
        raise SystemExit(1)
PY

echo "== [2/4] 数据集检查 =="
if [ ! -f "$DATASET" ]; then
    echo "  数据集不存在: $DATASET"
    echo "  获取方式(二选一):"
    echo "    a) git clone https://github.com/xiaowu0162/LongMemEval 后取 longmemeval_s.json"
    echo "    b) HF 镜像: HF_ENDPOINT=https://hf-mirror.com 下载 xiaowu0162/LongMemEval"
    echo "  然后放回 $DATASET 或 export ZMM_LONGMEMEVAL_PATH=<路径>"
    exit 1
fi
echo "  ok  $DATASET ($(du -h "$DATASET" | cut -f1))"

echo "== [3/4] 终裁配置评测(RETRIEVAL_ONLY + 4-type + date-anchor + hybrid, no reranker) =="
export ZMM_LONGMEMEVAL_PATH="$DATASET"
export ZMM_RETRIEVAL_ONLY=1
export ZMM_UTTERANCE_RETRIEVE=1
export ZMM_UTTERANCE_TYPES=ssu,ssp,ku,tr
export ZMM_HYBRID=1
export ZMM_DATE_ANCHOR=1

FULL_ARGS=(--pipeline m3-only --full)
if [ -n "$SUBSET" ]; then
    FULL_ARGS=(--pipeline m3-only --subset "$SUBSET")
fi

python tests/eval_longmemeval_accuracy.py "${FULL_ARGS[@]}"

# 输出落 zmd.CACHE_DIR(repo .cache 或插件 .cache,取决于安装形态);宽 glob 兼容 m3-only/m3_only 命名
JSONL=$( { ls -t .cache/longmemeval_acc_m3?only_*.jsonl \
               "$HOME/.claude/plugins/nautilus-compass/.cache"/longmemeval_acc_m3?only_*.jsonl \
          2>/dev/null || true; } | head -1 )
if [ -z "$JSONL" ]; then
    echo "[error] 未找到评测输出 jsonl"; exit 1
fi
echo "  输出: $JSONL"

echo "== [4/4] 三指标计算(vs official 0.890 / 0.978 / 0.929) =="
python scripts/lmes_metrics.py "$JSONL" --dataset "$DATASET"
