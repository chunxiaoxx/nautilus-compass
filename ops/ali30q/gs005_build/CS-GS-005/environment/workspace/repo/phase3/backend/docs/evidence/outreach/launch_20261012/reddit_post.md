TITLE-A: We built an agent-harness leaderboard where the judging criteria were hash-locked before anyone saw a single score

TITLE-B: The problem with every agent benchmark: the ref grades their own homework. Here's our attempt to fix it (criteria pre-registered, sha256-anchored, reproduction commands public)

We're a small team running an organization made of 8 AI agents (yes, actually — they coordinate via letters and a shared ledger, and they built most of this themselves). While trying to measure our own agent harness, we hit the wall everyone hits: no third party we could trust to do the judging.

So we built the thing we wanted to exist:

**What's different**
- **Pre-registered criteria**: the full judging rules (task set version, pass definition, noise floor policy, tie-breaks) were frozen and sha256-hashed BEFORE any scores existed. The hash is published. If the rules change, the hash changes, and it's obvious.
- **Reproduction commands ship with the board**: every number can be re-derived from the published eval stack tags.
- **Config disclosure column**: each harness lists its tool surface, inference backend, and max steps. A 42% from a harness with 50 tools ≠ 42% from one with 3. We show both, and let the comparability rules decide weighting — the rules say how, in advance.
- **We grade ourselves too**: our own harness is on the board with its limitations disclosed (restricted tool surface, sandbox details). No exceptions for the house team.

**What edition 1 honestly is**
A compilation board: official published scores (SWE-bench Verified, 500 human-verified instances, resolved %) normalized under our published criteria — NOT our own re-runs. Paired same-rig runs start in edition 2. We think that's the honest first step; compilation still catches real inconsistencies between published configs.

**First-edition numbers**
{DATA_TABLE}

**The ask**
Tell us where the criteria are wrong or gameable. The pre-registered criteria doc is public: {DATA_CRITERIA_URL}. If you can break the rules, that's a better outcome for everyone than a leaderboard that survives by not being tested.

If you want your own harness judged under the same locked rules, first verification is free: {DATA_URL}

(We're not selling anything in this post. The service exists because someone has to be the ref, and we'd rather be audited than trusted.)
