# LongMemEval-S on Colab T4 · step-by-step

Run the LongMemEval-S 500-question accuracy benchmark for `nautilus-compass v2.0.0` on Google Colab's free T4 GPU. Walltime ~6-10h for full 500, ~30min for SUBSET=30 validation run.

## What this is testing

- Retrieval: BGE-m3 dense → bge-reranker-v2-m3 cross-encoder rerank → top-5
- Subject LLM: Gemini 2.5 Flash (answers from retrieved context)
- Judge LLM: Gemini 2.5 Flash (scores answer correctness vs reference)

This matches the compass v0.8 pipeline that scored 56.6% on 5/04. v2.0.0 adds RRF fusion + lifecycle hooks but for a single-shot benchmark with no accumulated lifecycle history the retrieval performance should be ≥ baseline.

## Setup steps (one-time, ~5min)

### 1. Open the notebook in Colab

- Browser: https://colab.research.google.com/
- File → Upload notebook → select `bench/colab_longmemeval.ipynb` from this repo
- (or) File → Open notebook → GitHub tab → paste `chunxiaoxx/nautilus-compass` → pick `bench/colab_longmemeval.ipynb`

### 2. Enable T4 GPU

- Runtime → Change runtime type
- Hardware accelerator: **T4 GPU**
- Save

### 3. Upload Gemini service account JSON

Your service account JSON is at `C:\Users\chunx\Downloads\chunxiao-vm-260414-de9e73f4697d.json`.

- Click the **Files** icon in the left sidebar (folder icon)
- Click the **upload** button (file with arrow)
- Select that JSON file
- Rename it to **`gemini-sa.json`** so cell 4 finds it

### 4. Verify project + region match

The judge module defaults to:
- Project: `chunxiao-vm-260414`
- Location: `us-central1`

If your service account is for a different project/region, edit cell 4 to override:
```python
from nautilus_compass.judges.gemini_flash import GeminiFlashJudge
judge = GeminiFlashJudge(project='your-project', location='your-region')
```

## Run

### Validation pass (SUBSET=30, ~30min)

Run cells 1-7 top-to-bottom. Cell 6 has `SUBSET = 30` by default — finishes in ~30min. This validates the full pipeline end-to-end before committing to 8h.

Expected output of cell 7:
```
qtype                             acc     n
---------------------------------------------
multi-session                    ~50%     ~10
single-session-preference        ~60%     ~5
single-session-user              ~30%     ~8
temporal-reasoning               ~40%     ~5
OVERALL                          ~45%     30
```

The 30-question subset is noisy — overall should be in the 40-60% range. If it's 0-10% something is wrong (likely Gemini Flash returning empty or judge JSON parse failures).

### Full pass (500 questions, ~6-10h)

After validation passes:
1. Open cell 6
2. Change `SUBSET = 30` to `SUBSET = None`
3. Re-run cell 6 (it resumes from where the 30-question run left off — won't redo them)

**Colab idle disconnect**: free Colab disconnects after ~90min idle. Keep the browser tab open and periodically click on the notebook. The runner checkpoints every 5 questions to `/content/longmemeval_compass_v2_results.json`, so a disconnect costs at most 5 questions of re-work on the next reconnect.

Free Colab T4 has a ~12h session cap. If the run doesn't finish in one session, reconnect after the cooldown and re-run cell 6 — it picks up from the checkpoint.

## After it finishes

### Download the result

In the Files panel, right-click `longmemeval_compass_v2_results.json` → Download. Send the file back here and I'll commit it to `paper/results/`.

### Expected numbers

Reference points:
- 2026-05-04 baseline (compass v0.8 m3-rerank, GPT-4o judge): **56.6%** (283/500)
- Gemini Flash judge is more strict than GPT-4o on some types — expect compass v2.0.0 to land **52-58%** range
- Per-type breakdown should match the paper's published profile (single-session-user is hardest at ~30%, multi-session ~70%)

## Costs

- Compute: free (Colab T4)
- Gemini Flash API: ~$1-2 for 500 questions × 2 calls (subject + judge). Service account uses Vertex AI billing on the `chunxiao-vm-260414` project.

## Troubleshooting

### "Upload gemini-sa.json to /content/ first" assertion fails

You haven't uploaded the JSON yet, or it's named differently. Make sure the file is exactly `gemini-sa.json` in `/content/` (the Colab working dir).

### Gemini Flash returns empty / errors

- Check the project/region match (see Setup step 4)
- Check the service account has `roles/aiplatform.user` IAM role
- Test manually: `judge.generate('hello')` should return text

### Rerank step is slow (>30s per question)

bge-reranker on T4 should process 50 pairs in ~5-10s. If much slower, check that `device='cuda'` in cell 5 and re-run that cell.

### Results file empty after disconnect

The runner saves every 5 questions. If you disconnected within the first 5, those are lost — restart cell 6, it'll redo them.
