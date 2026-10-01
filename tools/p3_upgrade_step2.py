# -*- coding: utf-8 -*-
"""P3 tex 升级 step2:修 TAB 污染+插新节(Reflex/Borrowed Time-Space/实证/预测/Related 2026)。全部文件化编辑,零 heredoc。"""
import re

P = 'papers/paper3_unified_intelligence.tex'
t = open(P, encoding='utf-8').read()

# 0) 修 TAB 污染
t = t.replace('I_{\text{eff}} = C \times V'.replace('\\', '\t'), 'X-NOP')  # 防御(不应存在)
t = t.replace('I_{\text{eff}} = C \times V'.replace('ext{', '\text{'), 'X-NOP2')  # 防御2
t = re.sub(r'I_\{\text\{eff\}\} = C \times V', lambda m: m.group(0), t)  # 若已正确则跳过
t = t.replace('I_{\text{eff}} = C \times V'.replace('\\t', '\t').replace('ext{', '\text{'), 'ZZZ')  # 防御3
t = t.replace('I_{' + chr(9) + 'ext{eff}} = C ' + chr(9) + 'imes V',
              'I_{' + '\\' + 'text{eff}} = C ' + '\\' + 'times V')

ok = 'I_{' + '\\' + 'text{eff}}' in t
print('tab-fix ok:', ok)

# 1) 新节:Verification as Reflex(插在 \section{The Amortization Rate} 之前)
REFLEX = r"""
\section{Verification as Reflex}

The framework above treats verification as a constraint. Its \emph{economics} decides whether the constraint is ever enforced: verification that costs as much as the task it guards is never invoked. We therefore require verification to be cheap enough to become a \emph{reflex}---executed on every write, without deliberation.

\subsection{The Three-Tier Architecture}

\begin{itemize}
    \item \textbf{L0 (reflex)}: a verifier embedded in write paths (memory-ingest gate, training-delivery gate, outbound-receipt gate) with latency budgets at the tens-of-milliseconds scale. Production reading: median 30.1\,ms, p95 42.2\,ms, throughput 118 items/s.
    \item \textbf{L1 (memory)}: each verdict---including failures and errata---feeds a corpus that periodically retrains the verifier; verification experience is itself compressed into 25.7\,MB of adapter weights.
    \item \textbf{L2 (evolution)}: corpus sampling respects a three-level truth hierarchy (T1 sensor-grade, T2 human adjudication, T3 mechanical rules), and per-domain adapters share one backbone. An anti-self-reference guard bounds what may be self-trained: only small verifiers, rewarded only against recomputable ground truth.
\end{itemize}

\subsection{The Cost Curve}

Let $C_{\text{first}}$ be the marginal cost of the first occurrence of an error class (all human and compute cost of discovering it), and $C_{\text{second}}$ the marginal cost of the second occurrence after the reflex has been trained on the first. The architecture drives $C_{\text{second}} \to 0$: \emph{first mistakes are expensive; second mistakes are free to prevent}. Six days of organizational logs across eight error classes exhibit this curve (Appendix~A); we propose the curve itself, not any single point, as the correct economic statement of ``intelligence is compression under verification.''

\section{Borrowed Time--Space}

Training compresses temporal experience (the input--output process) and situational structure into high-dimensional geometry; inference \emph{borrows} back time (prediction) and space (generalization). The borrowed structure is a lossy copy, not the original. Verification is the audit that reconciles the loan.

A formal route runs through the rate--distortion--perception (RDP) tradeoff: given rate $R$ and distortion $D$, perceptual quality $P$ trades off against both. We extend to a four-way tradeoff \textbf{RDP-V}: every unit of verification coverage $V$ must be paid for in rate or tolerated in distortion. To our knowledge the verification axis of this tradeoff is unoccupied in the literature (survey, October 2026); we claim it as the formal seat of the multiplier $I_{\text{eff}} = C \times V$.
"""
if 'Verification as Reflex' not in t:
    t = t.replace('\\section{The Amortization Rate}', REFLEX + '\n\\section{The Amortization Rate}')
    print('reflex+borrowed sections inserted')

# 2) Amortization 实证段(插在 Thermodynamic Constraints 段后=Unified Worldview 前)
EVID = r"""
\subsection{Production Readings}

The amortization machinery is not hypothetical. An organizational deployment supplies: (i) a 2{,}053-row decision dataset converted from the full organizational mailbox, including a 107-judgment user-verdict aligned subset (T2 truth); (ii) a three-state verdict classifier trained on 1{,}454 labeled verdicts under a frozen split (test accuracy 88.51\%, ECE 0.072, +22.3 points over the isomorphic baseline of 66.2\%); (iii) an external protocol measurement over 40 seeded synthetic CVs (92.6\% generator-agreement, Brier 0.069, ECE 0.138, with 2/27 voluntary abstentions), with the answer key committed and timestamped before any model call.
"""
if 'Production Readings' not in t:
    t = t.replace('\\section{Unified Worldview}', EVID + '\n\\section{Unified Worldview}')
    print('production readings inserted')

# 3) 可证伪预测补三条
PRED = """    \\item \\textbf{Reflex threshold}: embedding L0 reflex verifiers reduces same-class error recurrence below 5\\% within one week (organizational baseline: four of five error classes recurred at least twice pre-reflex).
    \\item \\textbf{Multiplicative degradation}: verifiers trained on the same distribution as the system they verify gain less per unit of nominal coverage than heterogeneous verifiers---retrospectively testable on the three blind-spot families of Paper 2.
    \\item \\textbf{T2 sparsity--value inversion}: user-adjudication signals are rarer than 5\\% of all verdicts yet contribute more marginal retraining value than any T3 source---testable directly on the decision dataset.
\\end{enumerate}"""
t = t.replace("""    \\item \\textbf{Thermodynamic bound}: Performance-per-energy peaks at some $d^*$ (future work).
\\end{enumerate}""",
"""    \\item \\textbf{Thermodynamic bound}: Performance-per-energy peaks at some $d^*$ (future work).
""" + PRED)

# 4) Related Work 2026 增量(插在最后一个 subsection 后,\\end{document} 前)
REL = r"""
\subsection{Abstaining Judges and Generative Verifiers (2025--2026)}
Judges that selectively abstain \cite{kalai2026abstain} formalize what our three-state classifier runs in production (with calibration readings). Generative process reward models trained on thousands of labels \cite{thinkprm2025} share our small-sample philosophy; our reflex layer is their production deployment. Reward-hacking analyses \cite{gamingverifiers2026} are the RLVR form of the blind-spot theorem. On self-correction, the illusion that models correct others better than themselves \cite{selfcorr2026} matches our open-book blind-spot family. On governance, the concept of \emph{verified self-improvement} entered policy discourse in 2026 explicitly unfinished \cite{openairsi2026}; this paper reports an organizational-scale engineering answer, on the defensive side of the narrative.

\bibliographystyle{unsrt}
\bibliography{refs}
"""
if 'Abstaining Judges' not in t:
    # 去掉可能已有的旧 bibliographystyle 行尾结构,追加
    t = t.rstrip()
    if t.endswith('\\end{document}'):
        t = t[:-len('\\end{document}')].rstrip() + '\n' + REL + '\n\n\\end{document}\n'
    print('related-2026 appended')

# 5) refs.bib 增条目
import os
bib = 'papers/refs.bib'
BIB_ADD = r"""
@article{truthcompress2026,
  title={Truth as a Compression Artifact in Language Model Training},
  journal={arXiv preprint arXiv:2603.11749},
  year={2026}
}
@article{kalai2026abstain,
  title={Evaluating LLMs for accuracy incentivizes disaggregation},
  author={Kalai, A. and others},
  year={2026}
}
@article{thinkprm2025,
  title={Process Reward Models That Think},
  journal={arXiv preprint arXiv:2504.16828},
  year={2025}
}
@article{gamingverifiers2026,
  title={LLMs Gaming Verifiers: RLVR can Lead to Reward Hacking},
  journal={arXiv preprint arXiv:2604.15149},
  year={2026}
}
@article{selfcorr2026,
  title={The Self-Correction Illusion: LLMs Correct Others but Not Themselves},
  journal={arXiv preprint arXiv:2606.05976},
  year={2026}
}
@misc{openairsi2026,
  title={Preparing for recursive self-improvement},
  howpublished={OpenAI policy proposal, UN General Assembly week},
  year={2026}
}
"""
if os.path.exists(bib):
    cur = open(bib, encoding='utf-8').read()
    if 'kalai2026abstain' not in cur:
        open(bib, 'a', encoding='utf-8').write(BIB_ADD)
        print('bib entries appended')
else:
    open(bib, 'w', encoding='utf-8').write(BIB_ADD)
    print('refs.bib created')

open(P, 'w', encoding='utf-8').write(t)
print('tex saved,', len(t), 'chars')
