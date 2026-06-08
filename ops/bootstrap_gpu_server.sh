#!/bin/bash
# Bootstrap a fresh GPU server as a compass benchmark-env + daemon host.
# Idempotent-ish: re-running re-checks each step. Run AS the app user (not root)
# except the CUDA-toolkit apt step (needs sudo).
#
# VERIFICATION STATUS (honest):
#   [VERIFIED 2026-06-07 on Tesla T4 43.163.80.46]  steps 1,3,4,5 ran clean
#   [UNVERIFIED · awaits new GPU server]            step 2 (CUDA toolkit/nvcc) +
#                                                   step 6 (A-cluster compile)
# The dying T4 had no nvcc, so the nvcc/A-cluster path was never exercised.
#
# Usage:
#   bash bootstrap_gpu_server.sh            # daemon + models + corpus (no A-cluster)
#   WITH_CUDA_TOOLKIT=1 bash bootstrap_gpu_server.sh   # also install nvcc for A-cluster
set -uo pipefail
LOG(){ echo "[$(date '+%H:%M:%S')] $*"; }

APP_DIR="${COMPASS_APP_DIR:-$HOME/compass}"
CORPUS_PROJECT="${COMPASS_CORPUS_PROJECT:-compass-t4-demo}"
MEM_REMOTE="$HOME/.claude/projects/$CORPUS_PROJECT/memory"

# ── 1. python deps [VERIFIED] ──────────────────────────────────────────────
LOG "1/6 pip deps (torch + sentence-transformers)"
pip install --user --quiet --upgrade pip
pip install --user --quiet sentence-transformers
python3 -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(),
 (torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO-GPU'))" || {
  LOG "torch import/cuda check FAILED"; exit 1; }

# ── 2. CUDA toolkit for A-cluster nvcc [UNVERIFIED · only if WITH_CUDA_TOOLKIT=1] ──
# A-cluster samples (kernelbench_attention, autolab_radixsort) compile .cu with nvcc.
# torch ships its own CUDA runtime so the daemon/reranker do NOT need this; only
# raw-kernel compilation does. Match the toolkit major to the driver's CUDA.
if [ "${WITH_CUDA_TOOLKIT:-0}" = "1" ]; then
  LOG "2/6 CUDA toolkit (nvcc) — UNVERIFIED path"
  if command -v nvcc >/dev/null 2>&1; then
    LOG "  nvcc already present: $(nvcc --version | tail -1)"
  else
    LOG "  installing via apt (Ubuntu). For exact CUDA-version match prefer the"
    LOG "  NVIDIA cuda-toolkit-12-x package matching 'nvidia-smi' CUDA Version."
    sudo apt-get update -y && sudo apt-get install -y nvidia-cuda-toolkit || \
      LOG "  apt nvcc install FAILED — install toolkit matching driver manually"
    command -v nvcc >/dev/null 2>&1 && LOG "  nvcc: $(nvcc --version | tail -1)" || LOG "  nvcc STILL missing"
  fi
else
  LOG "2/6 CUDA toolkit SKIPPED (set WITH_CUDA_TOOLKIT=1 to enable A-cluster compile)"
fi

# ── 3. download embedding + reranker models [VERIFIED] ─────────────────────
LOG "3/6 pre-download bge-m3 + bge-reranker-v2-m3 (HF cache)"
FETCH="$(dirname "$0")/_t4_fetch_models.py"
if [ -f "$FETCH" ]; then python3 "$FETCH"; else
  python3 - <<'PY'
from sentence_transformers import SentenceTransformer, CrossEncoder
SentenceTransformer("BAAI/bge-m3"); CrossEncoder("BAAI/bge-reranker-v2-m3")
print("models ready")
PY
fi

# ── 4. start daemon (GPU + reranker) [VERIFIED] ────────────────────────────
# NOTE: daemon.py:96-99 reranker path lacks an HF-fallback → MUST pass
# ZMM_RERANKER_MODEL on HF-cache hosts or it silently falls back to dense.
LOG "4/6 start compass daemon (GPU + reranker)"
mkdir -p "$APP_DIR"
[ -f "$APP_DIR/daemon.py" ] || LOG "  WARN: $APP_DIR/daemon.py missing — scp it first"
pkill -f "python3 daemon.py" 2>/dev/null; sleep 2
( cd "$APP_DIR" && PATH="$HOME/.local/bin:$PATH" \
  ZMM_DEVICE=cuda COMPASS_PROD_RERANK=1 ZMM_RERANKER_MODEL=BAAI/bge-reranker-v2-m3 \
  COMPASS_USE_INOTIFY=0 \
  setsid python3 daemon.py > "$HOME/compass_daemon.log" 2>&1 < /dev/null & )
for i in $(seq 1 18); do
  if ss -tln 2>/dev/null | grep -q 9876; then LOG "  daemon listening 127.0.0.1:9876 (~$((i*5))s)"; break; fi
  sleep 5
done

# ── 5. corpus [VERIFIED via tar; prod uses ops/corpus_sync.py rsync] ───────
LOG "5/6 corpus dir: $MEM_REMOTE  (push .md from a dev/CPU host with corpus_sync.py)"
mkdir -p "$MEM_REMOTE"
LOG "  count: $(ls "$MEM_REMOTE"/*.md 2>/dev/null | wc -l) .md present"

# ── 6. A-cluster deps [UNVERIFIED] ─────────────────────────────────────────
LOG "6/6 A-cluster: requires nvcc (step 2) + per-sample run.py/harness.py — verify on this GPU"

LOG "bootstrap done. Verify: ssh in, run a recall query; for A-cluster compile a sample .cu."
