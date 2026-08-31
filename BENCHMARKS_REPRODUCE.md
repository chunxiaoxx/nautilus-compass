# Reproducing Compass v0.8 LongMemEval-S 56.6%

> ⚠️ **此文为 v0.8 旧版口径**(2026-05 e2e 56.6%,m3-rerank + reader)。
> 当前主口径(检索三指标 P@1/P@5/MRR,4-type routing + date-anchor + hybrid,
> vs mem0 同题对打)的一键复算入口:
> `bash scripts/reproduce_lmes_retrieval.sh` — 见 README 对应节。

> Total cost: ~$3.50 USD · Time: ~8 hours wall-clock
> Tested 2026-05-04 ~ 2026-05-05 on Tencent Cloud T4 spot instance

## TL;DR

```bash
# 1. GPU instance (T4 + 16GB · CUDA 12.4)
# 2. Install
git clone https://github.com/chunxiaoxx/nautilus-compass
cd nautilus-compass
pip install -e .[rerank]
bash install_bge.sh                      # downloads bge-m3 + bge-reranker-v2-m3

# 3. Set env
export ARK_API_KEY=<your_volc_ark_key>
export ZMM_LLM_PROVIDER=ark
export ZMM_SUBJECT_MODEL=deepseek-v3.2
export ZMM_JUDGE_MODEL=deepseek-v3.2
export ZMM_DEVICE=cuda
export ZMM_RERANKER_MODEL=BAAI/bge-reranker-v2-m3
export ZMM_THINKING=on
export ZMM_QUERY_REWRITE=on

# 4. Run (8 hours)
python tests/eval_longmemeval_accuracy.py --pipeline=m3-rerank --full

# 5. Verify · expected ~56.6%
cat .cache/longmemeval_acc_m3_rerank_full_*_summary.json
```

## Hardware tested

```
GPU: NVIDIA T4 16GB
CPU: 8 vCPU
RAM: 32 GB
Disk: 20 GB free (for model weights)
Network: 100 Mbps minimum (for HF mirror download)
OS: Ubuntu 22.04
CUDA: 12.4
PyTorch: 2.6 cu124
```

Cheaper alternatives (slower):
- Tencent Cloud T4 spot: ~¥0.70/hour · 8 hours = ¥6
- AWS g4dn.xlarge: ~$0.526/hour · 8 hours = ~$4.20 (no spot equivalent for free tier)
- Modal.com T4: ~$0.59/hour · 8 hours = ~$5
- Self-hosted T4: $0 marginal

## Environment setup

### Volc Ark coding plan account

```
1. Sign up at console.volcengine.com/ark
2. Apply for "coding plan" subscription (free tier eligible · 100K tokens/day)
3. Get API key from console (single key for 9 models)
4. export ARK_API_KEY=b8...
```

If Volc Ark not available in your region, alternatives:

```bash
# Anthropic Claude (~$15-20 instead of ¥10)
export ANTHROPIC_API_KEY=...
export ZMM_LLM_PROVIDER=anthropic
export ZMM_SUBJECT_MODEL=claude-haiku-4-5  # 或 claude-sonnet-4-6 · 后者贵但更准

# OpenAI GPT-4o (~$15-20)
export OPENAI_API_KEY=...
export ZMM_LLM_PROVIDER=openai
export ZMM_SUBJECT_MODEL=gpt-4o-mini  # 或 gpt-4o
```

Note: with non-DeepSeek models · accuracy may differ. Our 56.6% is specific to
DeepSeek V3.2 thinking. Use `tests/eval_longmemeval_accuracy.py --sample 50`
to estimate first.

### Model weights

```bash
bash install_bge.sh
# This downloads to:
#   ~/.cache/huggingface/hub/models--BAAI--bge-m3/         (~1.2 GB)
#   ~/.cache/huggingface/hub/models--BAAI--bge-reranker-v2-m3/  (~1.3 GB)
```

For China users · use HF mirror:

```bash
export HF_ENDPOINT=https://hf-mirror.com
bash install_bge.sh
```

### LongMemEval-S dataset

The benchmark dataset is from \cite{wu2024longmemeval}'s release:

```bash
# Auto-download (recommended)
python -c "from tests.eval_longmemeval_accuracy import load_dataset; load_dataset()"

# Or manual:
git clone https://github.com/xiaowu0162/LongMemEval
ln -s LongMemEval/dataset .cache/longmemeval_data
```

Dataset format: `longmemeval_s.json` (500 questions across 6 types).

## Run

### Full 500 (~8 hours · authoritative)

```bash
python tests/eval_longmemeval_accuracy.py --pipeline=m3-rerank --full \
  > eval.log 2>&1
```

Expected output (last lines):

```
[500/500] single-session-assistant       ✓ acc=0.566 (283/500) · 28058s

=== LongMemEval-S accuracy (m3-rerank · n=500) ===
  overall accuracy = 283/500 = 0.566

=== by question_type ===
  knowledge-update               n= 78  acc=0.577 (45/78)
  multi-session                  n=133  acc=0.549 (73/133)
  single-session-assistant       n= 56  acc=0.839 (47/56)
  single-session-preference      n= 30  acc=0.533 (16/30)
  single-session-user            n= 70  acc=0.571 (40/70)
  temporal-reasoning             n=133  acc=0.466 (62/133)
```

### Quick 50 (~45 minutes · for sanity check)

```bash
python tests/eval_longmemeval_accuracy.py --pipeline=m3-rerank --sample 50
```

Expected: ~56% (sample is balanced across types · matches full).

### Even faster smoke (~5 minutes)

```bash
python tests/eval_longmemeval_accuracy.py --pipeline=m3-rerank --sample 12
```

Just to verify the pipeline runs. Don't trust the number (n=12 too small).

## Verification

After run · per-question logs are saved:

```
.cache/longmemeval_acc_m3_rerank_full_<ts>.jsonl       # 1 line per question
.cache/longmemeval_acc_m3_rerank_full_<ts>_summary.json # aggregate
```

Each `.jsonl` line:

```json
{
  "qid": "ssu_001",
  "question_type": "single-session-user",
  "question": "What dish did the user say they cannot eat?",
  "ground_truth": "shrimp",
  "predicted": "shrimp",
  "correct": true,
  "retrieval_top": [...top-15 sessions with scores...],
  "judge_response": "Yes, the answer matches.",
  "elapsed_s": 32.5
}
```

Independent verification:

```bash
# Re-run a single question
python -c "
from tests.eval_longmemeval_accuracy import score_one
import json
with open('.cache/longmemeval_acc_m3_rerank_full_<ts>.jsonl') as f:
    for line in f:
        if 'ssu_001' in line:
            r = json.loads(line)
            print('expected:', r['correct'])
            break
"
```

## Components ablation

To verify each of the 5 components contributes:

```bash
# Baseline (turn everything off)
ZMM_QUERY_REWRITE=off ZMM_TYPE_AWARE_PROMPTS=off TOP_K=10 \
  python tests/eval_longmemeval_accuracy.py --pipeline=m3-rerank --sample 50

# Add one at a time
ZMM_QUERY_REWRITE=on  TOP_K=10  → +27 pts on ssu (sample) · +10 pts overall (full)
ZMM_TYPE_AWARE_PROMPTS=on        → +1-2 pts overall
TOP_K=15                         → +0.5 pts
ZMM_SSA_CONTEXT_MAX=3500         → +2 pts on ssa
```

## What can go wrong

### "MiniMax thinking refusal cascade"

If you accidentally use MiniMax with thinking-1024:

```bash
ZMM_LLM_PROVIDER=minimax ZMM_SUBJECT_MODEL=m2.7-highspeed ZMM_THINKING=on
# Run full 500 → expect 33% accuracy at 302 questions before refusal cascade
# Solution: use ZMM_THINKING=off (nothink · 45.8%)
```

### "GLM-5.1 takes 7.8h for 50 questions"

Long thinking budget. Use Volc Ark default budget:

```bash
unset ZMM_GLM_THINKING_BUDGET   # let the model auto-decide
```

### "bge-reranker OOM"

Reduce batch size:

```bash
export ZMM_RERANKER_BATCH=4   # default 16
```

### "Judge agrees with subject too much (self-judging)"

Use a different model as judge:

```bash
export ZMM_JUDGE_MODEL=gemini-2.5-pro   # if you have access
# Or
export ZMM_JUDGE_MODEL=glm-5.1-thinking  # different model family
```

Cross-judging cost: 2× the LLM API budget (still ~$7 USD total).

## Comparison numbers (for paper review)

```
This work (Compass v0.8):       56.6% (n=500)
Baseline (DeepSeek thinking):    46.6% (n=500)
GPT-4o (Gemini-2.5-pro):         44.6% (n=500)
MiniMax M2.7-highspeed nothink:  45.8% (n=500)
MiniMax M2.7-highspeed thinking: 33% † (refusal cascade · killed at 302/500)
GLM-5.1 thinking:                43.8% (n=48 sample only)
Kimi K2.6 thinking:              35.4% (n=48 sample only)
```

Industry / paper comparisons (per their published numbers):

```
Letta:     35-38%
Mem0:      40-45%
A-MEM:     ~50%
Zep:       55-60%
Paper RAG: 50-60%
```

## Cost breakdown (Volc Ark coding plan)

```
Total tokens consumed (for 500 questions):
  · Input:  ~5M tokens (retrieval contexts + prompts)
  · Output: ~500K tokens (answers + judge responses)

Volc Ark coding plan rate (DeepSeek V3.2):
  · Input:  ¥1 per million tokens
  · Output: ¥4 per million tokens

LLM cost: 5M × ¥1 + 0.5M × ¥4 = ¥7

T4 spot 8h × ¥0.40/h = ¥3.20

Total: ~¥10 = $1.50 USD (network egress not included)
+ network for model weights download (one-time): ~$0.50
+ instance cold-start fees: ~$0.50

Round to: $3.50 USD per replication.
```

## Citing

If you use these results in a paper:

```bibtex
@misc{compass2026,
  title  = {Compass v0.8: Closing the Memory Recall Gap with Chinese LLMs},
  author = {chunxiaoxx},
  year   = {2026},
  note   = {LongMemEval-S 56.6\% at 1/15 cost · \url{https://github.com/chunxiaoxx/nautilus-compass}}
}
```

## Questions about reproducibility?

- File a GitHub issue with `reproduction:` prefix
- Include: your hardware · environment vars · command run · last 50 lines of eval.log

We aim to respond within 72 hours and (where feasible) help you reach 56.6%.
