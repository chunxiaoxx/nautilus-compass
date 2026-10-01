# -*- coding: utf-8 -*-
"""P3 v1.3:V 口径回灌——混用 V 拆 V⁺(收益)/V⁻(成本)双符号+C 口径裁定(边际为主)。
承论文线回函任务 3+2。"""
P = 'papers/paper3_unified_intelligence.tex'
t = open(P, encoding='utf-8').read()

# ① 摘要乘法命题:V 明确为 V+
t = t.replace(
    "We sharpen this into a \\emph{multiplicative claim}: effective intelligence factors as $I_{\\text{eff}} = C \\times V$, where $C$ is compression capability and $V$ is the accuracy-weighted coverage of verification; the empty loop is the $V{=}0$ degenerate point and the blind spot the $V$-is-correlated-with-$C$ degenerate point.",
    "We sharpen this into a \\emph{multiplicative claim}: effective intelligence factors as $I_{\\text{eff}} = C \\times V^{+}$, where $C$ is compression capability and $V^{+}$ (\\emph{verification benefit}) is the accuracy-weighted coverage of verification; a companion ratio $\\eta = C / V^{-}$ tracks \\emph{verification cost} $V^{-}$. The empty loop is the $V^{+}{=}0$ degenerate point and the blind spot the $V^{+}$-is-correlated-with-$C$ degenerate point.")

# ② 操作性定义:V 拆双符号+新增 V- 定义
t = t.replace(
    """\\begin{definition}[Verification factor, operational]
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
\\end{definition}""",
    """\\begin{definition}[Verification benefit $V^{+}$, operational]
\\label{def:vplus}
Index the system's write paths by $i$ (memory ingest, model delivery, outbound publishing).
For each path record: coverage $c_i \\in [0,1]$ (fraction of writes passing the verifier),
verifier accuracy $a_i \\in [0,1]$ against held-out ground truth, and truth grade
$w_i \\in \\{T_1, T_2, T_3\\}$ mapped to weights $\\{1, \\lambda, \\mu\\}$ with
$1 > \\lambda > \\mu > 0$ (sensor-grade, human-adjudicated, rule-based). Then
\\[
V^{+} \\;=\\; \\sum_i \\alpha_i \\, w_i \\, c_i \\, a_i,
\\qquad \\sum_i \\alpha_i = 1,
\\]
with $\\alpha_i$ the cost-weight of path $i$'s error class. $V^{+}$ is auditable from
registry records alone; it decreases whenever a path drops coverage, degrades accuracy, or
is grounded in weaker truth.
\\end{definition}

\\begin{definition}[Verification cost $V^{-}$, operational]
\\label{def:vminus}
Let $n_i$ be the number of verifier invocations (or wall-clock verification time, reported
in parallel) consumed on path $i$ per unit of accepted output. Then
\\[
V^{-} \\;=\\; \\sum_i \\alpha_i \\, n_i \\, /\\, u_i,
\\]
where $u_i$ is the accepted-output volume of path $i$. $V^{-}$ is the denominator of the
efficiency ratio $\\eta = C / V^{-}$: \\emph{how much verification work is spent per unit of
deployed, accepted output}. Reflex-tier economics (Section~\\ref{sec:reflex}) is precisely the
engineering program for driving $V^{-}$ down at fixed $V^{+}$.
\\end{definition}

\\paragraph{On the two readings of $C$.} Compression may be scored \\emph{marginally}
(task-specific bits only: adapter, head) or \\emph{totally} (all deployed bits, including
pre-existing open-weight infrastructure). We adopt the \\textbf{marginal reading as primary}:
pre-existing weights carry zero opportunity cost to the task at hand, so the meaningful
question is how many \\emph{additional} bits each unit of utility costs. The total reading is
reported as background context. On the marginal reading the two deployed verifier systems of
Section on production readings score $C$-ratios in opposite directions of their latency
advantage---exactly the kind of definitional fork that preregistration exists to fix.""")

# ③ 其余 V 单符号处(预测/Reflex 引用)统一为 V+
t = t.replace("the reflex-threshold prediction", "the reflex-threshold prediction")
t = t.replace("verifiers gain less per unit of nominal coverage than heterogeneous verifiers",
              "verifiers gain less per unit of nominal $V^{+}$ than heterogeneous verifiers")
t = t.replace("the formal seat of the multiplier $I_{\\text{eff}} = C \\times V$.",
              "the formal seat of the multiplier $I_{\\text{eff}} = C \\times V^{+}$ and the efficiency ratio $\\eta = C / V^{-}$.")

open(P, 'w', encoding='utf-8').write(t)
print('v1.3 patched |', 'V+' in t, '| V- def:', 'def:vminus' in t, '| marginal:', 'marginal reading as primary' in t)
