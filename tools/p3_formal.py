# -*- coding: utf-8 -*-
"""P3 v1.2:①C/V 操作性定义 ②RDP-V 两个 formal propositions(证明) ③Data Availability。
全部文件化写 tex,零 heredoc 转义。"""
P = 'papers/paper3_unified_intelligence.tex'
t = open(P, encoding='utf-8').read()

BS = chr(92)  # backslash

# ── ① C/V 操作性定义:插在 Verification as Reflex 节的 Three-Tier 之前 ──
DEFS = """
\\subsection{Operationalizing $C$ and $V$}
\\label{sec:operational}

The multiplier $I_{\\text{eff}} = C \\times V$ is only falsifiable if both factors are measurable on a
common footing. We give measurement protocols that an auditor can run without access to internals.

\\begin{definition}[Compression factor, operational]
Fix a task distribution $\\mathcal{D}$ and a utility threshold $u^\\ast$. Let $L(\\theta)$ be the
description length (bits) of the deployed system's learned component. Then
\\[
C(\\mathcal{D}, u^\\ast) \\;=\\; \\frac{u(\\theta)\\big/ u^\\ast}{L(\\theta)\\big/ L_0},
\\]
where $u(\\theta)$ is utility achieved and $L_0$ a reference implementation achieving $u^\\ast$.
$C > 1$ means the system reaches the bar with proportionally less description length than the
reference. Production reading: a 25.7\\,MB adapter sustains 88.51\\% against a 66.2\\%
whole-system reference, i.e.\\ utility \\emph{per bit} rises by the retraining gain while the
adapter adds $<$2\\% of the base model's bits.
\\end{definition}

\\begin{definition}[Verification factor, operational]
Index the system's write paths by $i$ (memory ingest, model delivery, outbound publishing).
For each path record: coverage $c_i \\in [0,1]$ (fraction of writes passing the verifier),
verifier accuracy $a_i \\in [0,1]$ against held-out ground truth, and truth grade
$w_i \\in \\{T_1, T_2, T_3\\}$ mapped to weights $\\{1, \\lambda, \\mu\\}$ with
$1 > \\lambda > \\mu > 0$ (sensor-grade, human-adjudicated, rule-based). Then
\\[
V \\;=\\; \\sum_i \\alpha_i \\, w_i \\, c_i \\, a_i,
\\qquad \\sum_i \\alpha_i = 1,
\\]
with $\\alpha_i$ the cost-weight of path $i$'s error class. $V$ is auditable from registry
records alone; it decreases whenever a path drops coverage, degrades accuracy, or is grounded
in weaker truth.
\\end{definition}

Both protocols yield dimensionless ratios, so $I_{\\text{eff}}$ inherits a common scale and the
degenerate points ($V{=}0$; $V$ correlated with $C$) become measurable hypotheses rather than
metaphors.
"""

if 'sec:operational' not in t:
    t = t.replace('\\subsection{The Three-Tier Architecture}', DEFS + '\n\\subsection{The Three-Tier Architecture}')
    print('defs inserted')

# ── ② RDP-V propositions:插在 Borrowed Time-Space 节末(即 Production Readings 前? 该节后是 Amortization)──
# Borrowed 节文本结尾是 "we claim it as the formal seat ..." 之后接 \section{The Amortization Rate}
PROP = """
\\subsection{Two Formal Properties of RDP--V}
\\label{sec:rdpv-props}

We state two properties of the verification axis. Property~1 is elementary but is the load-bearing
step connecting selective verification to effective distortion; Property~2 states that the
improvement is never free.

\\begin{proposition}[Selective verification lowers effective distortion]
\\label{prop:lower}
Let a code induce distortion $D$ with distribution $P$ over emitted samples, and let a verifier
reject a sample of distortion $d$ with probability $\\delta(d)$, where $\\delta$ is non-decreasing
with $\\delta(0) = 0$ and $\\delta(d) < 1$ for some $d > 0$. Let $A$ be the acceptance event. Then
the effective (post-rejection) distortion satisfies
\\[
D_{\\text{eff}} \\;=\\; \\mathbb{E}[d \\mid A] \\;\\leq\\; \\mathbb{E}[d] = D,
\\]
with strict inequality whenever $\\delta$ is strictly increasing on the support of $d$.
\\end{proposition}

\\begin{proof}
Acceptance probability is $\\Pr(A) = \\mathbb{E}[1 - \\delta(d)]$, which is non-increasing in $d$.
Hence the accepted distribution first-order stochastically dominates nothing larger than $P$:
for any non-decreasing $\\delta$, $\\mathbb{E}[d \\mid A] \\le \\mathbb{E}[d]$ by Harris'
inequality applied to the pair $(d,\\, 1-\\delta(d))$, which are counter-monotone. Strictness
follows because on any interval where $\\delta$ strictly increases, larger distortions are
strictly down-weighted in the accepted measure.
\\end{proof}

\\begin{proposition}[Verification is paid in rate or coverage]
\\label{prop:cost}
Fix a rate--distortion class $(R, D)$. For any two verifiers $\\delta_1 \\le \\delta_2$ (pointwise
detection) at the same false-rejection profile on zero-distortion samples,
$D_{\\text{eff}}(\\delta_2) \\le D_{\\text{eff}}(\\delta_1)$, while the acceptance rate satisfies
$\\Pr(A \\mid \\delta_2) \\le \\Pr(A \\mid \\delta_1)$. If additionally $\\Pr(A \\mid \\delta_2)$ is
held equal to $\\Pr(A \\mid \\delta_1)$, the class must spend additional bits distinguishing
distortion levels, i.e.\\ achieve it only at rate $R' > R$.
\\end{proposition}

\\begin{proof}[Proof sketch]
The first claim repeats the monotonicity of Proposition~\\ref{prop:lower}. For the second: holding
acceptance fixed while raising detection of positive distortions requires lowering false
rejections, i.e.\\ resolving distortion magnitude more finely than the code at rate $R$
represents; this resolution is bits (a standard covering-number argument on the distortion
partition).
\\end{proof}

Together: verification lowers effective distortion (Prop.~\\ref{prop:lower}) but every unit of
lowering is purchased in coverage or in rate (Prop.~\\ref{prop:cost})---the four-way tradeoff
claimed informally above. We deliberately state weak forms; a full characterization of the
RDP--V frontier is open.
"""

if 'sec:rdpv-props' not in t:
    anchor = 'the formal seat of the multiplier $I_{\\text{eff}} = C \\times V$.'
    assert anchor in t, 'anchor missing'
    t = t.replace(anchor, anchor + '\n' + PROP)
    print('propositions inserted')

# ── ③ Data Availability:附录 A 之后加节 ──
DATA = """
\\section*{Data Availability}
\\label{app:data}
An anonymized snapshot accompanies this work: (i) the 1{,}454-verdict training corpus with
three-level truth labels (schema: qid, verdict, truth\\_label, truth\\_grade, label\\_origin,
failure\\_tag), with project identifiers replaced by content hashes; (ii) the schema and a
100-row anonymized sample of the 2{,}053-row decision dataset; (iii) the full answer key,
request log, and signed receipt of the 40-item external protocol measurement. The measurement
protocol (pre-registered criteria, frozen splits with SHA-16 commitments) is released so that
every headline number in Section on production readings can be recomputed from the snapshot.
"""

if 'app:data' not in t:
    t = t.replace('\\end{document}', DATA + '\n\\end{document}')
    print('data availability added')

open(P, 'w', encoding='utf-8').write(t)
print('saved,', len(t), 'chars')
