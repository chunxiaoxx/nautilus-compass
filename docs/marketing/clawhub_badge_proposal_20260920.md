# ClawHub 徽章提案函(草稿 · 待用户过目后投 openclaw/clawhub issue)

> 目标仓:openclaw/clawhub(Skill + Plugin Registry for OpenClaw)
> 姿态:产品对产品(他们显示·我们供给·互相获客),不是求助。
> 预案:若 issue 通道冷场 72h,转 ClawHub Discord/邮箱(CLAWhub 官网 footer 查)。

---

**Title: Proposal: third-party "assay-verified" badge for ClawHub cards — we supply, you display**

Hi ClawHub team —

We publish [nautilus-compass](https://clawhub.com/chunxiaoxx/nautilus-compass) on
ClawHub (1.0.2, security review passed), and we run **Nautilus Assay** — an independent
verifier for AI-agent performance claims (signed recompute receipts, ed25519, protocol
published CC-BY).

**The gap:** every marketplace (yours, Glama, MCP Registry) shows what a card *claims*
(stars, self-reported benchmarks). None shows whether anyone *checked*. That's the trust
layer browsers solved with the lock icon — and nobody owns it for agent listings yet.

**The proposal — a lock icon for ClawHub cards:**

1. A card-level badge slot: **verified · disagree · unverified** (+ `until <date>` when
   the receipt carries a TTL).
2. Verification input = a *detached ed25519 receipt* the publisher attaches, produced by
   anyone running the open protocol — us, another verifier, or eventually the publisher's
   own key (self-attestation level, clearly labeled).
3. Your integration cost is **one function call**: `pip install assay-verify` (zero
   dependencies, pure stdlib, MIT) → `verify(target, sig, pubkey)` → three-state result.
   No API of ours, no lock-in — the signature verifies mathematically, you never have to
   trust us.
4. Non-participation is fine: unverified cards keep listing exactly as today. The badge
   only makes *checked* claims visible — the "Not Secure" pattern works because it's
   comparative, not punitive.

**Why this is differentiated for you:** no registry currently displays third-party
verification state. First mover gets the trust layer as a feature; we get a display
surface. Mutual customer acquisition: publishers who want the badge learn verification
exists from your cards; your buyers get a signal nobody else offers.

**Track record (all receipts public & signature-verifiable):**

- Aider on SWE-bench Lite — claimed 26.3%, recomputed **26.3% AGREE**
- OpenHands row on Terminal-Bench v1 — claimed 41.25%, recomputed **165/400 exact**
- NanoJev (embodied controller) — six claims **AGREE**, incl. frame-level trajectory replay
- And the honest-numbers discipline: our own pipeline's bad scores go on the same wall
  (10/10 unverifiable verdicts, a 1/5 exam score that became 3.5/5 in public view).

Protocol text: https://github.com/chunxiaoxx/nautilus-compass/blob/main/docs/protocol/ASSAY_PROTOCOL_V0.md
SDK: https://pypi.org/project/assay-verify/

Happy to do a live walkthrough or ship a reference PR for the badge renderer if useful.

— Nautilus Assay (伊洛科技有限公司 / Yiluo Technology Co., Ltd., verification operator)
