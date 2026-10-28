# compass → soul · 2026-06-29 · ping 你跑 LOO · 用户决策 A

> 用户 6/29 22:00 拍:选项 A · 接受 3 A-class · 跑小样本 LOO · verdict=INCONCLUSIVE 守教训1

## 你接球(立即)

**跑 distill_loo --kind swe** · 输入 3 A-class:
- scikit-learn__scikit-learn-10297
- sympy__sympy-20049
- django__django-13551

**预期 verdict=INCONCLUSIVE**(守教训1 n≥12 · 实际 n=3)· 但仍可看:
- distill 训练 loss 曲线
- hold-out win_rate(若有泛化趋势 → 后续加料再跑)
- confound-check(5 类 fold-starvation / train-eval-skew / over-fit / under-trained / adapter-failure)

## SSOT 护栏(6/29 用户拍)

1. n≥12 才跑 LOO(verdict-gate 拦 n<12 · 防 whipsaw 教训2)
2. 易 django PROVEN → 须非易料复证(教训3)
3. confound 先核再下结论(教训3)
4. SSOT 钉死+广播四框(教训4)
5. ship 了必验活(教训5)

## 球

- **soul(你)**: 跑 LOO · 出 verdict · 无论 INCONCLUSIVE/PROVEN/KILLED 都报
- **compass(我)**: 等 verdict · 据结果决断下一步
  - INCONCLUSIVE + 有趋势 → 加 9 道(Autodata weak-strong discrimination)再跑
  - KILLED → 核 confound · 治根因
  - PROVEN → 闭环 · 接 MCP tools Phase 4

## 你输出格式

1. verdict(PROVEN/INCONCLUSIVE/KILLED)
2. train_loss 曲线(若跑了)
3. hold-out win_rate(若跑了)
4. confound-check 结果(5 类全核)
5. 失败模式(若有 · grounded · 不泛化)

— compass · 2026-06-29(ping 你跑 LOO · 决策 A · 等 verdict 决断下一步)