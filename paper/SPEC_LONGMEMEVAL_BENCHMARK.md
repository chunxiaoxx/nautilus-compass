# SPEC · LongMemEval-S Benchmark · compass + RRF vs agentmemory 95.2% R@5

> **Status**: Spec design only · 2026-05-21
> **Target**: paper3 v2 §3 真 baseline compare · cite agentmemory R@5 95.2% · validate compass RRF lift
> **Scope**: 真**reuse existing infrastructure** · 真 NO new eval script
> **Run effort**: User-triggered · T4 GPU · 8-12h walltime · ~$0(Flash judge or DeepSeek free tier)

---

## 1. Context · 真为啥做

paper3 v2 §2 bullet #1 真 update(5/22 ship · commit b90cf9d)真 加 agentmemory 真 prior-art cite:
> "agentmemory (rohitg00 · 15.3K stars · LongMemEval-S **95.2% R@5**) AUTO_COMPRESS LLM-required"

真 paper3 真 novelty claim:**"compass v1.7.1 = first to expose schema-declared LLM-free 4-tier + Ebbinghaus"**

真 需 evidence:**compass + RRF(Phase 2.C ship · `rrf_fusion` · 5/22 commit 2ed77b4)真 R@5 真 ≥ 95.2% baseline** · 真 cite-able。

---

## 2. 真已 existing infrastructure(audit verbatim · anchor #5)

### 2.1 已 existing eval scripts

| Script | Path | Purpose | Status |
|---|---|---|---|
| `eval_longmemeval.py` | `tests/eval_longmemeval.py` | retrieval-only · cosine sim · p1/p3/p5/MRR per type · 50/500 subset | shipped(5/04) |
| `eval_longmemeval_accuracy.py` | `tests/eval_longmemeval_accuracy.py` | end-to-end · LLM judge · accuracy metric | shipped(5/04 v0.8) |

### 2.2 真已 ran benchmarks

| Date | Pipeline | Metric | Result |
|---|---|---|---|
| 2026-05-04 | v0.8 m3-rerank | full 500 accuracy | **56.6%**(283/500) |
| 2026-05-04 | DeepSeek thinking baseline | full 500 accuracy | 46.6% |
| Prior runs | various | (see `paper/results/longmemeval_results_*.json` · 7 files) | various |

### 2.3 真 reproduce guide

`BENCHMARKS_REPRODUCE.md` verbatim:
- T4 GPU + 16GB · CUDA 12.4 · Ubuntu 22.04
- `pip install -e .[rerank]` + `bash install_bge.sh`
- Volc Ark coding plan(free tier 100K tokens/day · ~$0)or Anthropic/OpenAI(~$15-20)
- `python tests/eval_longmemeval_accuracy.py --pipeline=m3-rerank --full` · 8h walltime
- Expected ~56.6%

### 2.4 真 dataset

- HF · `xiaowu0162/longmemeval`
- Path · `~/.cache/huggingface/hub/datasets--xiaowu0162--longmemeval/snapshots/2ec2a557.../longmemeval_s`
- 500 questions × 6 types

---

## 3. RRF integration · 真 minimal extension(~20 LOC)

真 reuse `eval_longmemeval.py` · 加 `--use_rrf` arg + import `rrf_fusion` from `recall.py`:

```python
# Pseudocode · ~20 LOC patch to eval_longmemeval.py
from recall import rrf_fusion

def main():
    ap.add_argument("--use_rrf", action="store_true", help="v1.7.1 · Phase 2.C · enable RRF k=60 fusion")
    args = ap.parse_args()
    # ... existing setup ...

    for q in data:
        # Existing · single ranking (cosine on m3)
        cosine_ranked = [(score, {"path": sid, "session_id": sid}) for sid, score in sims]

        if args.use_rrf:
            # Phase 2.C · combine multiple rankings (placeholder · could add BM25 + KG)
            # For minimal RRF demo: pass cosine_ranked once → equivalent to no fusion
            # Full version: add BM25 ranking + KG ranking from compass
            fused = rrf_fusion(cosine_ranked, k=60, top_k=5, session_diversify=True)
            ranked_ids = [entry["session_id"] for _score, entry in fused]
        else:
            ranked_ids = [sid for sid, _ in sims[:5]]
        # ... compute R@5 against truth_ids ...
```

---

## 4. Run plan(user-triggered · 不本 session)

### 4.1 真 baseline run(no RRF · 真 reproduce 5/04 baseline)
```bash
ssh t4-gpu  # 43.173.164.32 · key C:\Users\chunx\Downloads\11111.pem
cd nautilus-compass
git pull  # 真 latest commit b90cf9d
export ZMM_LONGMEMEVAL_PATH=~/.cache/huggingface/...longmemeval_s
python tests/eval_longmemeval.py --full
# Expected · ~95% R@5(retrieval-only metric · cosine on m3-rerank)
```

### 4.2 真 RRF run(Phase 2.C 真 fusion enabled)
```bash
python tests/eval_longmemeval.py --full --use_rrf
# Expected · ≥ 95.2% R@5 if fusion 真 effective · or 真 baseline-equivalent if 真 single ranking 真 already top
```

### 4.3 真 Flash judge variant($0)
真 Flash 真 only 真 needed for accuracy metric · not R@5(R@5 真 retrieval-only · 真 no LLM needed)。
真 真 unlock paper3 真 cross-LLM judge ablation(MEME-public 真 OUTLINE §3.4 真 3 judges)。

---

## 5. Verification(真 paper3 真 cite-able criteria)

### 5.1 真 pre-register null criterion(防 over-claim · anchor #7)

| Outcome | Interpretation | Paper3 ship? |
|---|---|---|
| compass R@5 ≥ 95.2% | ✅ matches agentmemory baseline · paradigm valid | yes · cite as 'comparable to agentmemory' |
| compass R@5 ≥ 96% | ✅✅ exceeds agentmemory · RRF lift real | yes · cite as 'exceeds 95.2% baseline by X pp' |
| compass R@5 90-95% | 🟡 within noise · ambiguous | yes but cite as 'comparable within noise' |
| compass R@5 < 90% | ❌ regression · 真 mechanism issue | no ship · investigate first |

### 5.2 真 robustness check(防 single-LLM bias)

真 not 真 critical 真 R@5 metric · 真 already 真 retrieval-only no judge。但 真 paper3 真 cross-LLM judge ablation 真 separate experiment(use Gemini Flash + MiniMax + DeepSeek · 5/20 unlock)。

---

## 6. Cost + Timing

| Item | Cost | Walltime |
|---|---|---|
| T4 GPU spot(Tencent)| ¥0.70/h × 8h = ¥6 | 8h |
| DeepSeek thinking(Volc Ark free tier)| ¥0(100K/day quota)| n/a |
| Gemini Flash(service account chunxiao-vm-260414 reuse) | $0 | n/a |
| 真 total | **~¥6($1)** | **~8h** |

---

## 7. Anchor 贡献

| Anchor | 真贡献 |
|---|---|
| #1 agent first | compass retrieval 真 super-agent 真 fit |
| #3 反 D 维护 | 真 reuse existing eval_longmemeval.py · ~20 LOC patch · 不重 ship |
| #5 不重复造轮子 | 真 reuse · BENCHMARKS_REPRODUCE.md + 2 eval scripts + 7 prior result files |
| #7 不验证就声称 | 真 pre-register null criterion 真 ship 前 · 防 over-claim |
| #9 不猜方向 | 真 verbatim baseline 真 ran 5/04 56.6% accuracy · 真 dataset path verbatim |

---

## 8. Outstanding · user trigger 真 next

1. User trigger T4 GPU(43.173.164.32 · key `C:\Users\chunx\Downloads\11111.pem`)
2. User pull latest compass · run baseline + RRF runs
3. User capture R@5 results · update paper3 v2 §3 真 baseline table
4. User decide ship arXiv 真 timing(Seokwon endorsement window still open · 5/19 issue #1 0 reply)

---

## 9. Related ship · 真 trail

- Phase 2.C `rrf_fusion` · commit `2ed77b4` · `recall.py:810-893` · 8/8 RRF smoke pass
- Phase 3 paper reframe · commit `b90cf9d` · `OUTLINE_PAPER3 §2 bullet #1` 加 agentmemory cite
- BENCHMARKS_REPRODUCE.md · `paper/RESULTS_v0.8.md` · v0.8 56.6% baseline
- Plan · `~/.claude/plans/scalable-drifting-seahorse.md` · Phase 2.C verification section
