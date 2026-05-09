# arXiv Submission · Step-by-step · 2026-05-08

> Two papers · two tarballs · ~30 min total wall-clock if you already have an arxiv account.
> Order matters: paper1 first, then paper2 (so paper2 can cite paper1's arxiv ID).

---

## Pre-flight (one-time setup)

- [ ] arXiv account at https://arxiv.org/user · personal email · verify
- [ ] First-time submitter: arXiv requires endorsement from a previously-published author in the target category. Without an endorser:
  - Plan B: post on alphaXiv first (no endorsement needed), then arXiv after first arxiv paper accepted via co-author
  - Plan C: ask a co-author / collaborator who is already endorsed to forward the submission

---

## Paper 1 · Black-box Persona Drift Detection

- **Tarball:** `paper/arxiv_paper1_20260508.tar.gz` (~70KB · LaTeX source)
- **Local PDF for reference:** `paper/nautilus-compass.pdf` (19 pages · 600KB)

### Submit

1. https://arxiv.org/submit · "Start a new submission"
2. **License:** CC BY 4.0 (matches MIT code license; permits attribution+reuse)
3. **Primary category:** `cs.LG` (Machine Learning)
4. **Cross-list:** `cs.CL` (Computation & Language) · `cs.AI` (Artificial Intelligence)
5. **Title:** "Nautilus Compass: Black-box Persona Drift Detection for Production LLM Agents"
6. **Authors:** chunxiaoxx (Nautilus Open Platform)
7. **Abstract:** copy from `paper/sections/00_abstract.tex` (1814 chars · under arxiv 1920 cap)
8. **Comments line:** "19 pages, 6 figures. Code at github.com/chunxiaoxx/nautilus-compass"
9. **Upload `arxiv_paper1_20260508.tar.gz`**
10. arXiv recompiles · **review the auto-generated PDF** carefully — must match `nautilus-compass.pdf`
11. If anything looks off (figures missing, fonts swapped): cancel + investigate · don't publish
12. Submit · note the assigned `arXiv:2505.NNNNN` ID

---

## Paper 2 · LongMemEval-S system + EverMemBench cross-bench

- **Tarball:** `paper/arxiv_paper2_20260508.tar.gz` (~240KB · LaTeX source)
- **Local PDF for reference:** `paper/paper2_main.pdf` (27 pages · 499KB)

### Pre-submit edit (after paper 1 has an arxiv ID)

The `OUTLINE_PAPER2.md:107` and `paper2_v4_appendix.tex` placeholder TODOs say "companion paper-1 cross-cite". Backfill them now:

1. Edit `paper/sections/paper2_01_intro.tex` and `paper/sections/paper2_03_method.tex` — find where drift detection is mentioned · add `\cite{nautiluscompass2026}` (or matching key)
2. Edit `paper/paper2_refs.bib` — add the entry:

   ```bibtex
   @misc{nautiluscompass2026,
     title  = {Nautilus Compass: Black-box Persona Drift Detection for Production LLM Agents},
     author = {chunxiaoxx},
     year   = {2026},
     howpublished = {arXiv preprint arXiv:2505.NNNNN},  % paste paper1's ID
     note   = {Companion to this paper · drift detector formalization}
   }
   ```
3. Locally rebuild the tarball:
   ```bash
   ssh -i ~/Downloads/11111.pem ubuntu@43.173.164.32
   cd /tmp/paper && pdflatex -interaction=nonstopmode paper2_main.tex >/dev/null \
     && bibtex paper2_main >/dev/null \
     && pdflatex -interaction=nonstopmode paper2_main.tex >/dev/null \
     && pdflatex -interaction=nonstopmode paper2_main.tex >/dev/null \
     && tar czf /tmp/paper/arxiv_paper2_20260508.tar.gz \
        paper2_main.tex paper2_refs.bib paper2_main.bbl \
        sections/paper2_*.tex \
        figures/{pipeline_v08,trajectory_v08,fusion_diagram}.pdf
   scp ubuntu@43.173.164.32:/tmp/paper/arxiv_paper2_20260508.tar.gz \
     C:/Users/chunx/.claude/plugins/nautilus-compass/paper/
   ```

### Submit

1. https://arxiv.org/submit · "Start a new submission"
2. **License:** CC BY 4.0
3. **Primary category:** `cs.CL` (Computation & Language · LongMemEval is NLP)
4. **Cross-list:** `cs.IR` (Information Retrieval) · `cs.SE` (Software Engineering)
5. **Title:** (copy from `paper2_main.tex` `\title{...}`)
6. **Authors:** chunxiaoxx (Nautilus Open Platform)
7. **Abstract:** copy from `paper/sections/paper2_00_abstract.tex` (1293 chars · under cap)
8. **Comments line:** "27 pages, 6 figures, 7 tables. Companion to arXiv:2505.NNNNN [paper1 ID]. Code+data at github.com/chunxiaoxx/nautilus-compass"
9. **Upload `arxiv_paper2_20260508.tar.gz`**
10. Review auto-generated PDF · must match `paper2_main.pdf`
11. Submit · note `arXiv:2505.MMMMM`

---

## Post-submit (within 24h of both IDs landing)

- [ ] Update README.md: replace `[arXiv:TBD]` placeholders with real IDs (2 occurrences)
- [ ] Update PUBLICATION.md: cross-link both arxiv URLs
- [ ] Update GITHUB_RELEASE.md: cite arxiv IDs
- [ ] Twitter thread (use `paper/promo/forum_refresh_2026-05-07.md` X/Twitter section · paste arxiv IDs)
- [ ] Show HN (`paper/promo/forum_refresh_2026-05-07.md` HN pitch · 8am PT weekday timing · 周二 / 周四 best)
- [ ] r/LocalLLaMA + r/MachineLearning posts (different framing per `forum_refresh`)
- [ ] PaperWithCode submissions (per `paper/promo/papers_with_code_submission.md` · pending agent output)
- [ ] Outreach emails to 8 targets (per `paper/promo/outreach_emails_2026-05-08.md` · fill in real addresses, send manually)
- [ ] HuggingFace Spaces deploy (per `hf_space/` · pending agent output)

---

## Common arxiv pitfalls (we already avoided)

- ✅ Abstract under 1920 chars (paper1 = 1814 · paper2 = 1293)
- ✅ All figures embedded as actual PDF (no `\fbox{[figure placeholder]}` lines)
- ✅ All bib entries have proper journal/howpublished (no `note = {placeholder · TODO replace}`)
- ✅ No emoji / unicode emoji in tex (we replaced ⭐ → $\star$, ⚠️ → $\dagger$)
- ✅ pgfplots compat=1.16 (TeX Live 2019 compatible)
- ✅ scalable font (`\usepackage{lmodern}`) so microtype expansion works

If arxiv compile fails on their end:
- They email you the log within ~10 min
- Common rejection reasons: missing .bbl, broken figure include, license mismatch
- We pre-built .bbl with bibtex on T4 · should be in the tarball already
- All 6 paper1 figures + 3 paper2 figures verified embedded

---

**Bottom line:** both tarballs are submission-grade as of 2026-05-08 13:35 T4 local time. Only blocker is your arxiv account + endorsement (if first time).
