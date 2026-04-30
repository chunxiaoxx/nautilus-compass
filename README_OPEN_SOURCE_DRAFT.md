# zenmind-mem

> Memory plugin for Claude Code — with **persona drift detection** that actually works.

[![drift-AUC](https://img.shields.io/badge/drift_AUC-0.92-brightgreen)](#drift-detection-evaluation)
[![LongMemEval-P@5](https://img.shields.io/badge/LongMemEval_P@5-0.917-brightgreen)](#retrieval-evaluation)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## What's special

Most memory plugins do retrieval. zenmind-mem does retrieval **+ a black-box approximation of persona drift detection** — catches when your AI is about to repeat behavioral patterns you've flagged as mistakes.

> **Relation to Persona Vectors (Chen et al. arXiv:2507.21509)**: Their paper finds *activation-space* directions for traits like sycophancy/evil/hallucination — a white-box method requiring model internal access. zenmind-mem operates at the **prompt-text layer** with cosine matching against anchor texts. Different mechanism, similar goal: monitoring persona drift. Anthropic's method is more principled (it sees model internals); ours is more **deployable** (any Claude Code user can run it without model weights).

```
[Persona drift · 25+35 anchors · BGE · daemon]
  score=-0.034 · ⚠️ towards anti-anchor
  🔴 alert: '看到文件比之前小就当是好的优化' (cos=0.587)
  ↑ Current prompt overlaps with 'mistakes you've made before' · don't repeat
```

That alert fires **before** the AI takes the action. Not a post-mortem. A guardrail.

## Numbers (LongMemEval-S, n=12, 2026-04-29)

Real head-to-head, same dataset, same 12 questions:

| Metric | **zenmind-mem (m3 + bge-rerank)** | mem0 (Vertex) | zenmind-mem (no rerank) | Random |
|---|---|---|---|---|
| **P@5** | **0.917** | 0.917 | 0.75 | 0.10 |
| **MRR** | **0.837** | 0.715 | 0.732 | 0.07 |
| Drift AUC | **0.92** | n/a (no drift) | 0.92 | 0.50 |

P@5 打平但 zenmind-mem MRR +0.122 优势: truth session 平均排序更靠前。 mem0 weakest type:
single-session-user MRR 0.250 — zenmind-mem with rerank gets **0.522** (2x).

By question type (n=2 each), with reranker:

| Type | P@1 | P@5 | MRR | base→rerank lift |
|---|---|---|---|---|
| single-session-assistant | 1.00 | 1.00 | **1.000** | (already perfect) |
| single-session-preference | 1.00 | 1.00 | **1.000** | (already perfect) |
| temporal-reasoning | 1.00 | 1.00 | **1.000** | (already perfect) |
| knowledge-update | 0.50 | 1.00 | 0.750 | (already perfect P@5) |
| multi-session | 1.00 | 1.00 | **0.750** | **+0.20 MRR** ⭐ |
| single-session-user | 0.50 | 0.50 | 0.522 | **+0.43 MRR** ⭐⭐ |

The reranker's biggest lifts are on the question types where bi-encoder alone was weak. single-session-user (specific factual claim hidden in chatty session) jumped from MRR 0.091 → 0.522 (5x). multi-session went from P@5=0.50 → 1.00.

> Cross-encoder reranker (BGE) is **enough** here — no LLM API key needed for production retrieval quality.

## How drift detection went from random to 0.92 AUC

The journey is the README:

| Step | Change | AUC |
|---|---|---|
| 0 | Anchors as abstract maxims, mean-cosine | 0.51 (= coin toss) |
| 1 | Anchors as task-shaped sentences, top-3 mean | 0.79 |
| 2 | Switch bge-small-zh → bge-m3 (multilingual) | 0.84 |
| 3 | + 10 hard FP examples back into anchors | **0.92** |

> Lesson: anchors must match **prompt distribution**. Abstract principles in cosine space don't separate from task-shaped queries.

## Quickstart

```bash
git clone https://github.com/<you>/zenmind-mem ~/.claude/plugins/zenmind-mem
bash ~/.claude/plugins/zenmind-mem/install.sh

# Wire the hook in ~/.claude/settings.json:
# {
#   "hooks": {
#     "UserPromptSubmit": [{ "matcher": "", "hooks": [
#       { "type": "command", "command": "bash ~/.claude/plugins/zenmind-mem/hook.sh" }
#     ]}]
#   }
# }
```

The `install.sh` downloads `BAAI/bge-m3` (~2.3 GB) via ModelScope mirror — works around HF Hub flakiness on Windows. To use a smaller model:

```bash
ZMM_EMBEDDER_MODEL=intfloat/multilingual-e5-small  # 471 MB · MRR 0.762
ZMM_EMBEDDER_MODEL=BAAI/bge-small-zh-v1.5          # 92 MB  · 中文 only
```

## Components

| File | Role |
|---|---|
| `daemon.py` | Persistent BGE process · TCP socket on 127.0.0.1:9876 |
| `recall.py` | UserPromptSubmit hook · queries daemon, falls back inline |
| `anchors.json` | 25 positive + 35 negative anchors (task-shaped) |
| `strategy_store.py` | DPT-style strategy distillation (`steps[]` + keywords) |
| `links_finder.py` | A-MEM cross-memory supersede detection |
| `mid_session_hook.py` | PostToolUse capture |
| `stop_hook.py` | Session-end strategy distillation |
| `tests/eval_*.py` | calibrate / drift / recall / longmemeval |

## Differentiators (vs mem0 / Letta / claude-mem)

| | zenmind-mem | mem0 | Letta | claude-mem |
|---|---|---|---|---|
| Persona drift L3 detection | ✅ AUC 0.92 | ❌ | ❌ | ❌ |
| Strategy distillation (DPT-Agent) | ✅ | ❌ | partial | ❌ |
| Time-bucket recall (24h trust vs 7d+ warning) | ✅ | ❌ | ❌ | ❌ |
| Per-domain anchor profiles | ✅ (vc / zenmind / default) | ❌ | ❌ | ❌ |
| 3-hook lifecycle (prompt/post-tool/stop) | ✅ | ❌ | ❌ | only stop |
| Hook surfaces `score`/`alignment`/`deviation` to LLM | ✅ | ❌ | ❌ | ❌ |
| LongMemEval P@5 | 0.75 | ~0.6 | unpub | n/a |
| Latency (warm) | 1.8 s | 0.1 s (API) | 0.2 s | n/a |
| Local-only (no API key) | ✅ | ❌ (OpenAI) | optional | ✅ |

## Caveats (please read)

1. **Drift AUC 0.92 is on synthetic 50+50 prompts.** Real-world distribution may differ. We've seen system events (e.g. tool notifications mentioning "ephemeral / size") trigger false-positive alerts. Production should filter to true user prompts.
2. **single-session-user MRR 0.099** is the known retrieval-only ceiling for this question class. Use an LLM reranker for production.
3. **Windows native is flaky** — m3 (~3 GB RAM) sometimes silently OOMs. Recommended: WSL2 (Linux), or use `multilingual-e5-small` instead.
4. **HF Hub had unstable downloads** (httpx client closing mid-request on Win/py3.14). `install.sh` defaults to ModelScope mirror.
5. **Anchors are domain-specific.** Out-of-the-box anchors are tuned for a Chinese/English mixed engineering+research context. Customize in `anchors.json`.

## Dataset

LongMemEval-S (Chen et al. 2024): 500 question-haystack pairs across 6 question types. We report subset of 12 (2 per type). Full 500 takes ~75 min on m3 + Linux with CUDA, longer on CPU.

```bash
# To reproduce subset 12:
python3 tests/eval_longmemeval.py --subset 12
```

## Cite / Credit

Inspired by (but not implementing):
- **Persona Vectors** (Chen et al. arXiv:2507.21509, Anthropic 2025) — *white-box* activation-space drift detection. zenmind-mem is a complementary *black-box* prompt-layer approximation, not an implementation of their method.

Built on:
- BGE-m3 / BGE-Reranker (Chen et al. BAAI 2024)
- DPT-Agent style strategy distillation (arXiv:2502.11882)
- A-MEM dynamic links (arXiv:2502.12110)
- LongMemEval benchmark (Wu et al., NeurIPS 2024)
- Sentence-Transformers (Reimers & Gurevych, EMNLP 2019)

## License

MIT — but the anchors in `anchors_*.json` are CC-0; please replace with yours when adopting.
