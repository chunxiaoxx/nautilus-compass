# Nautilus Assay — Monthly Trust Report #1 (2026-09)

> First public issue. English-first (industry layer); Chinese summaries follow on our
> own channels. Every number below is either machine-recomputed or signed-verifiable;
> where we could not verify, we say so. **This report is itself signed** (footer).

## 1. Who we are

Nautilus Assay is an independent verification service for AI-agent performance claims —
"the assay office for agent benchmarks". We recompute published claims from public
artifacts, issue three-state verdicts (agree / disagree / not_computable), and sign every
receipt with ed25519. Our protocol is published CC-BY; anyone can implement it or verify
our receipts without trusting us. Operator: 伊洛科技有限公司 (Yiluo Technology).

Why this exists: agent benchmarks have a lemon-market problem. Self-reported scores are
unfalsifiable marketing; independent recomputation is rare, unstandardized, and usually
unsatisfying to either side. We are building the standardized version — cheap enough to
be default, honest enough to be cited.

## 2. What we verified this month (external targets)

| # | Target | Claim | Our recompute | Verdict |
|---|---|---|---|---|
| 1 | Aider — SWE-bench Lite | 26.3% | 79/300, exact subset relations verified | **AGREE** |
| 2 | Terminal-Bench v1 — OpenHands row | 41.25% ± 0.69pp | **165/400 = 0.4125 exact**; strict variant 40.74% within 1σ | **AGREE** |
| 3 | NanoJev — embodied controller, 6 claims | frame/collision/rollout stats | six claims recomputed, incl. frame-level trajectory replay | **AGREE** |

All three receipts are on our wall with detached ed25519 signatures and one-command
verification instructions. Two disclosures from this work: (a) Terminal-Bench's
leaderboard excludes 5 incomplete trials from the denominator — defensible, but
undocumented until now; (b) the OpenHands row was flagged `verified: false` on their own
site — third-party recompute is exactly what such flags are waiting for.

## 3. What we verified this month (our own house)

The same rules apply inward — arguably the point:

- **verdict-bus pilot, 10/10 NOT recomputable** (inputs lived only in session logs,
  producer-set flags, token counts zero). This finding started our criteria catalog.
- **X1 judge incident, 47/47 self-inconsistent → entire batch voided.** No "partially
  usable" lane.
- **First-party exam: 1/5 → 2/5 → 3/5 → 3.5/5 → 3.5/5**, every point published at the
  time it was measured, including the failures. Same model, same tasks; all score
  movement came from harness-layer fixes — the boring, reproducible kind of progress.
- Latest datapoint (355a pass@2): **disagree** — a wiring-class failure (function-local
  import + tuple arity), documented with the two directional hints we returned and
  nothing more.

## 4. The criteria catalog (open)

15 registered criteria, ratcheted (may only tighten with evidence chains). Highlights:
`verdict-recomputability-v1`, `external-verified-provenance-v1`, `adversarial-*` (four
gaming classes), `paradigm-corroboration-chain-v1`, `calibration-claim-verify-v1`
(calibration claims of probability-output models are safety claims — recomputable on
public holdouts).

## 5. Tooling released (free layer, permanent)

- **assay-verify** SDK on PyPI — three lines, zero dependencies: `keygen / attest /
  verify`. Includes an MCP stdio server (`python -m assay_verify.mcp`) so any MCP client
  can verify receipts.
- **VerifyPack v0.3** — the packaging protocol for verifiable claims: evidence seals,
  episode/trajectory checks (frame-level invariants), and receipts with **subject
  fingerprints + TTL** (expired = UNVERIFIABLE until re-verified — continuous trust, like
  certificate renewal).
- Protocol text: CC-BY, one page. "Verification of verification" is free by design.

## 6. BC1 — our first benchmark cohort (preview)

30 items across 4 dimensions (criteria-catalog reasoning, provenance, gaming detection),
public/holdout split 18/12, seed committed before generation. Public items ship with the
wall page; holdout stays sealed for first-party exams. Release: 2026-09-27.

## 7. Liability (the part most trust products skip)

Our teeth, in the protocol (§5b): if we misjudge, the claimant gets an **OVERTURNED
verdict of the same rigor + refund + challenge costs**, and our track-record counter
resets. Challenge window 90 days; anonymous verifications are treated as UNVERIFIABLE.
Named operator: 伊洛科技有限公司.

## 8. Get verified (free)

Post a claim + public evidence anywhere, then open a recompute request:
https://github.com/chunxiaoxx/nautilus-compass/issues/new?template=recompute_request.md
(English or Chinese). Self-attestation via the SDK is free forever; independent
verification is what we sell.

---

*Receipt for this report:* see `TRUST_REPORT_2026-09_EN.md.sig` (ed25519, pubkey
`f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be`).
Verify: `pip install assay-verify` → `verify(Path(report), Path(sig), pubkey_hex)`.
