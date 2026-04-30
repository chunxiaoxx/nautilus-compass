# arXiv Preprint · Outline + Status

**Title**: Black-box Persona Drift Detection for Production LLM Agents:
A Hook-level Anchor Matching Approach

**Target venue**:
- arXiv cs.CL primary (no peer review barrier, fastest)
- Optionally submit to NeurIPS 2026 Workshop on Memory in LLM Agents (if exists)
- Or ACL ARR rolling review

**Length target**: 8 pages + refs (workshop/preprint style)

---

## Section status (W = written tonight, ⏳ = TODO)

| § | Title | Status | Owner | Time est |
|---|---|---|---|---|
| 0 | Abstract | ✅ W | drafted | done |
| 1 | Introduction | ✅ W | drafted | done |
| 2 | Related Work | ⏳ | TBD | 1.5h |
| 3 | Method | ⏳ | TBD | 2h |
| 4 | Evaluation | ⏳ | TBD | 2h (figures) |
| 5 | Discussion | ⏳ | TBD | 1h |
| 6 | Limitations | ⏳ | TBD | 0.5h |
| 7 | Open Source | ⏳ | TBD | 0.5h |

**Total remaining**: ~7.5 hours work over 2-3 days.

---

## Figures needed

| Fig | Content | Source |
|---|---|---|
| Fig 1 | System architecture (hook → 3 paths → injection) | Adapted from README ASCII art · need TikZ |
| Fig 2 | 4-step AUC evolution line chart (0.51 → 0.79 → 0.84 → 0.92) | Today's eval data · matplotlib |
| Fig 3 | LongMemEval-S head-to-head bar chart (zenmind vs mem0 by question type) | Today's eval data · matplotlib |
| Fig 4 | Drift score distribution: aligned vs deviation prompt histograms | Today's eval data · matplotlib |
| Fig 5 (optional) | Anchor weight evolution over feedback rounds | Synthetic / extrapolation |

---

## Tables needed

| Tab | Content | Source |
|---|---|---|
| Tab 1 | Comparison matrix (zenmind-mem vs mem0/Letta/claude-mem/Zep across 6 dims) | README |
| Tab 2 | Drift detection 4-step ablation table (AUC + delta) | RESULTS.md |
| Tab 3 | LongMemEval-S subset 12 results table | RESULTS.md |
| Tab 4 | Latency vs accuracy trade-off (bi-encoder vs cross-encoder for drift) | RESULTS.md |

---

## Open issues to resolve before submission

1. **GitHub repo URL**: must be public · stable URL
2. **Author identity**: chunxiaoxx + GitHub handle? Real name optional
3. **Code reproducibility**: ensure `tests/run_all.sh` runs end-to-end on Linux+macOS in CI
4. **Anchor sample**: include the actual 25+35 anchors (anchors.json) as appendix
5. **Negative result inclusion**: cross-encoder null result is in RESULTS.md, decide if appendix
6. **Persona Vectors disambiguation**: get this clean — we are NOT implementing Anthropic's method
7. **Cite mem0 properly**: their paper or just GitHub? Check their preferred citation
8. **Optional**: contact Persona Vectors authors before submission to invite review

---

## Submission checklist

- [ ] All sections drafted
- [ ] Figures (5) generated as PDF/SVG
- [ ] Bibliography (refs.bib) complete
- [ ] Anonymized for double-blind? (if going to a venue that requires) - skip for arXiv
- [ ] Latex compiles cleanly
- [ ] arxiv abstract category: cs.CL (primary) · cs.AI (secondary)
- [ ] License: CC BY 4.0 for paper
- [ ] Affiliation: independent researcher? plus GitHub/email
- [ ] Acknowledgments: BGE/Anthropic/mem0/Letta authors

---

## Schedule (5 calendar days)

```
Day 1 (today): outline + abstract + intro · ✅ done
Day 2: Related Work + Method (1+1 sections)
Day 3: Eval section + figures (most work)
Day 4: Discussion + Limitations + Open Source
Day 5: Final pass, fix latex, generate PDF, upload to arXiv
```

**Target arXiv submission**: 2026-05-04 (5 days from today).
**arXiv review**: ~24-48h cs.CL endorsement.
**Public on arXiv**: 2026-05-05 to 2026-05-07.
