# jev-trust

**Trust middleware for Jev decision APIs — spend confidence at its verified exchange rate.**

Jev gives you calibrated-looking probabilities. But calibration is a property of
**(model, domain)** pairs, not models. We measured hosted Jev 1.13 at
ECE 0.041 on closed deterministic tasks — and **accuracy 50% while stating
91% confidence** on synthetic email triage ([Assay research #1/#2](https://github.com/chunxiaoxx/nautilus-compass/discussions/59)).
Same model. Same day. The number you actually care about is the one for *your* domain,
and nobody has measured it yet — including the vendor.

`jev-trust` wraps the Jev API and measures it in *your* domain while you work:

- **Every call logged** — append-only JSONL: question, answer, stated confidence, effective confidence, usage, timestamp.
- **Outcomes fed back** — as ground truth arrives, `record_outcome()` builds your domain's calibration record: accuracy, Brier, ECE, and calibration currency **C = 1 − ECE**.
- **Effective confidence on every answer** — `r.effective_confidence` = what the stated confidence is *worth* here so far (observed accuracy of the matching confidence bin, ≥5 samples; else C-adjusted; else `None` = insufficient evidence).
- **Overconfidence alerts** — a callback fires when a decision is confident enough to act on but the domain hasn't earned that confidence yet.
- **Signed evidence** — one call signs the whole log (ed25519). Publish log + sig + pubkey; anyone — including [Nautilus Assay](https://compass.nautilus.social/wall.html) — can independently recompute your numbers.

Zero dependencies. Pure stdlib. Python ≥ 3.8.

## Install

```bash
pip install jev-trust
```

## Quickstart

```python
from jev_trust import TrustedJev

jev = TrustedJev(api_key=API_KEY, domain="email-triage")

# decide() never lets unexamined confidence through:
r = jev.decide(state, {"q": {"type": "choice", "instructions": "...",
                             "criteria": {...}}})["q"]

r.decision              # 'alpha'
r.stated_confidence     # 0.91   <- what Jev claims
r.effective_confidence  # 0.50   <- what 0.91 is worth in YOUR domain so far
r.basis                 # 'bin_observed' | 'C_adjusted' | 'insufficient_n'
r.domain_verdict        # FACE_VALUE | DISCOUNT | DOWNGRADE | UNVERIFIED

# feed ground truth back as it arrives:
jev.record_outcome("q", truth)

# your domain's running scorecard:
jev.stats()
# {'n_outcomes': 42, 'accuracy': 0.52, 'brier': 0.41, 'ece': 0.39,
#  'C': 0.61, 'verdict': 'DISCOUNT', ...}
```

## The alert that pays for itself

```python
def on_overconfidence(r):
    # fired when stated >= 0.90 but the domain hasn't earned FACE_VALUE
    log.warning(f"{r.qid}: Jev says {r.stated_confidence}, "
                f"worth {r.effective_confidence} here — route to human?")

jev = TrustedJev(api_key=API_KEY, domain="fraud-flag",
                 alert_confidence=0.90, on_overconfidence=on_overconfidence)
```

## Bipolarity self-check (v0.2) — ask both ways, or don't ask

We measured Jev answering yes/no questions whose required computation was too
expensive for it: the answer collapsed onto the **question's polarity** rather
than the data (both directions — reword the question the other way and the
verdict flips with it; [study artifacts](https://github.com/chunxiaoxx/nautilus-compass/tree/main/runtime/jev_trust_domain4_20260922)).
Stated confidence does not warn you — the two wrong halves each look confident.

`decide_symmetric` asks every question in both polarities inside ONE API call
(you write the flipped wording — the library never rewrites your semantics):

```python
r = jev.decide_symmetric(state, {"q": {
    "question":     {"type": "noul", "instructions": "Is this transaction fraudulent?"},
    "opposite":     {"type": "noul", "instructions": "Is this transaction legitimate?"},
}})["q"]

r.decision              # answer from the original polarity
r.polarity_consistent   # False -> the two wordings disagree
r.trust_flag            # "POLARITY_CONFLICT" — do not act without review
r.effective_confidence  # None on conflict, regardless of stated confidence
r.stated_confidence     # min of the two cross-polarity confidences (conservative)
```

Conflicting items fire `on_polarity_conflict` and are force-degraded: the
question the model can't actually compute is exactly the one this catches.

## Verdicts (Assay calibration-currency reading levels)

| Verdict | Condition | Reading |
|---|---|---|
| `UNVERIFIED` | < 20 outcomes in domain | stated confidence is an unbacked claim |
| `FACE_VALUE` | C ≥ 0.80 | use stated confidence as-is |
| `DISCOUNT` | 0.50 ≤ C < 0.80 | multiply trust by C |
| `DOWNGRADE` | C < 0.50 | route to human review |

The library ships with Assay's published reference rates (informational — your
verdict is always computed from *your* outcomes):

```python
jev_trust.ASSAY_REFERENCE_RATES
# {'closed-deterministic': {'C': 0.959, ...},   # n=240, ECE 0.041
#  'adversarial-stress':  {'C': 0.988, ...},    # n=200, ECE 0.012
#  'synthetic-email-choice': {'C': 0.086, ...}} # acc 50% @ conf 91%
```

## Signed evidence — make your numbers independently checkable

```python
sig_path = jev.sign_log()          # writes <log>.jsonl.sig
jev.keys.pub_hex                   # publish this next to the log

# anyone can verify:
from jev_trust import verify_log
verify_log("session.jsonl", "session.jsonl.sig", pub_hex)  # -> VALID
```

Same canonical-JSON + ed25519 scheme as
[assay-verify](https://pypi.org/project/assay-verify/) — a signed `jev-trust`
log is directly submittable to Nautilus Assay for independent recomputation
(the evidence format behind their [Domain Calibration Reports](https://compass.nautilus.social/dcr.html)).

## Why this exists

Nautilus Assay independently verifies AI-agent performance claims. Their two
public Jev studies found: overall accuracy 92.2% / Brier 0.048 on closed tasks
(good), but domain calibration collapses on distribution shift — 50% accuracy
at 91% stated confidence in one synthetic triage domain. Vendor benchmarks
can't see your domain. `jev-trust` is the always-on instrument that can.

Methodology: ECE = equal-width 10-bin top-label; Brier = mean (1 − p_true)²
(binary-identical to the standard (p − y)² form). Identical formulas to Assay's
published verification code.

## License

MIT. © 2026 Nautilus Assay.
