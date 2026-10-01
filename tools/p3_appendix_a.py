# -*- coding: utf-8 -*-
"""P3 v1.1 附录 A:六天组织教训数据表 LaTeX 化(八行×四列:教训/失真类型/验证抗体/成本曲线点)。"""
P = 'papers/paper3_unified_intelligence.tex'
t = open(P, encoding='utf-8').read()

APPENDIX = r"""
\appendix
\section{Organizational Lessons as Compression-Distortion Data}
\label{app:lessons}

Eight error classes from six days of organizational logs (2026-09-26 to 10-01), each mapped to its
distortion type (the compression-theoretic reading), the verification antibody deployed, and the
cost-curve point it contributes (Section~\ref{sec:reflex}). All rows are traceable to
organization-internal artifacts; identifiers are elided for operational security.

\begin{table}[h]
\centering
\small
\begin{tabular}{p{2.6cm}p{3.4cm}p{3.8cm}p{3.4cm}}
\toprule
\textbf{Error class} & \textbf{Distortion type} & \textbf{Verification antibody} & \textbf{Cost-curve point} \\
\midrule
Verifier ceiling (66.2\%) & lossy summary drops discriminative structure & heterogeneous re-training (LoRA, three-state verbalizer; 88.51\%) & $C_1{=}$2 GPU-h; $C_2{\to}0$ \\
Self-report overwrite & verdict field overwritten by judge output (same-source) & artifact-anchored truth + dual-layer recompute (500 rows recalled) & near-miss; audit cost only \\
Open-book features & verifier features contain the judged output & feature-pipeline excision; re-run under frozen criteria & same $C_1$, +22.3\,pt \\
Equivalence mislabeling & mechanical rule cannot canonicalize surface forms (13.8\% conflict) & rule demoted to sampled pool; criterion registry & 3 verified instances \\
Fake training & 200 steps logged, zero weight update (six checkpoints, identical MD5) & delivery telemetry: trainable\,$>$0, grad-norm\,$>$0, distinct checkpoints & single telemetry check \\
Synthetic-benchmark mirage & local 175\,MB vs.\ production 4.9\,GB (legacy stock unmodeled) & test sets sampled from production distribution & two rollbacks, one fix \\
Theater metrics & income self-produced 100\%, external settlement $B{=}0$ for two months & world-reply criterion (external readings as final measure) & institutional antibody \\
Platform-boundary friction & publish attempts die at captcha/permission/schema edges & pre-registered protocol templates; boundary checklist & one manual step remains \\
\bottomrule
\end{tabular}
\caption{Eight organizational error classes as compression-distortion data. Each antibody, once
trained into the reflex layer, drives the marginal cost of the second occurrence of its class
toward zero---the economic statement of $I_{\mathrm{eff}} = C \times V$.}
\label{tab:lessons}
\end{table}

\paragraph{Reading the table.} The first column is what failed; the second is \emph{why} the
failure was invisible to the system that produced it (always a compression artifact: a dropped
field, an overwritten bit, an unmodeled stock); the third is the heterogeneous grounding that
caught it; the fourth is the amortization evidence. Four of the eight classes recurred at least
twice before their antibodies were institutionalized---the baseline against which the
reflex-threshold prediction (Section on falsifiable predictions) will be scored.
"""

if 'app:lessons' not in t:
    # 插到 \end{document} 前
    t = t.rstrip()
    assert t.endswith('\\end{document}')
    t = t[:-len('\\end{document}')].rstrip() + '\n' + APPENDIX + '\n\n\\end{document}\n'
    open(P, 'w', encoding='utf-8').write(t)
    print('appendix A inserted,', len(t), 'chars')
else:
    print('already present')

# Reflex 节加 label 供引用
t = open(P, encoding='utf-8').read()
if '\\label{sec:reflex}' not in t:
    t = t.replace('\\section{Verification as Reflex}',
                  '\\section{Verification as Reflex}\n\\label{sec:reflex}')
    open(P, 'w', encoding='utf-8').write(t)
    print('sec:reflex labeled')
