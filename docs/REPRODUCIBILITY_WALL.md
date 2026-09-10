# Reproducibility Wall

> Independent reproduction beats self-report. Everything below was produced by
> someone who ran the head-to-head themselves. Numbers go on the wall
> **as reported — favorable or not.**

## Cryptographically verifiable claims (VerifyPack)

Numbers on this wall also ship as sealed packs: `pack.json` + sha256 manifest +
claims recomputable from payload bytes + an ed25519-signed receipt. Verify
without trusting us (stdlib only, no third-party deps):

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass && cd nautilus-compass
# full recompute (zero external inputs — every claim recomputes from bytes).
# --out keeps your run from touching the signed receipt in the repo:
python -m tools.verifypack verify runtime/verifypack/arma_summary/pack \
  --out /tmp/my_receipt.json
# signature + digest check (works for packs that declare external inputs):
python -m tools.verifypack check runtime/verifypack/arma_summary/pack \
  --receipt runtime/verifypack/arma_summary/pack/receipts/receipt.json \
  --pubkey f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be
```

| Pack | What it seals | Result |
|---|---|---|
| `arma-summary-e2e-v1` | Summary-layer e2e verdict, LongMemEval-S full 500 — 0.754 all-judged (377/500) + 0.700 conservative + per-type breakdown (8 claims) | 8/8 agree · sig verified |
| `verify_batch001` | Third-party data-utility claims (flywheel batch001, 7 claims) | 5 agree · 1 degraded · 1 **disagree** |

Verifier pubkey (ed25519): `f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be`

The one `disagree` in batch001 is kept visible on purpose: a log file kept
being appended after sealing, so its claimed hash no longer matched bytes on
disk. The protocol caught it — that's what it's for. (The 81.6% dual-accounting
figure from the same run is deliberately **not** a claim: it can't be
recomputed from pack-internal bytes alone, and unverifiable numbers don't get
sealed.)

Want your verdict on the wall with a receipt under **your** key instead of
ours? `python -m tools.verifypack keygen --out-dir .verifypack --name you`,
re-run `verify`, sign, and send us the receipt — that's a stronger entry than
any self-report.

## How to get on the wall

1. Run the head-to-head protocol — ours lives in [`docs/evidence/`](evidence/)
   (scripts, run logs, judge outputs). The full 500-question LongMemEval-S
   retrieval comparison costs **~$3.50** in API calls.
2. Open a PR or issue titled `Wall entry: <your-handle>` with:
   - your numbers (any of: P@1 / P@5 / MRR / e2e)
   - scope — full 500 or an explicitly labeled subset
   - environment (OS, embedder + versions, mem0 version, judge)
   - a link to your logs (repo, gist, anything public)
3. We publish it unedited (formatting only).

## The wall

| Date | Who | Scope | compass P@1 | mem0 P@1 | Environment | Logs |
|---|---|---|---|---|---|---|
| 2026-09-08 | @chunxiaoxx (self-reported — which is exactly why this wall exists) | LongMemEval-S · full 500 | **0.890** | 0.774 (mem0 2.0.19) | BGE-m3 vs text-embedding-005, each on defaults, our harness | [docs/evidence/](evidence/) |
| — | *row 2 is yours* | | | | | |

## Rules

- No cherry-picking from us: entries that **contradict** our numbers are
  published with the same prominence.
- Subsets are welcome but must be labeled as subsets.
- Found a protocol flaw? It gets fixed and re-run, not buried.

*Related: the judge-hygiene paper (LLM-as-judge failure taxonomy + protocol,
arXiv in submission) and the dual-accounting e2e report in the README.*
