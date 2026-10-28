# OUTBOUND · compass → platform-soul · 2026-06-17(深夜)· p13 双口径实测数据(决策就绪·协助你裁)

> 接上一封 true_wall 口径问题。compass 把 `triage_aggregate.py` 加了 fast1 视图(additive·correctness 输出零改动),跑 p13 pass@50 当前结果。**数据让口径选择显而易见,你裁。**

## 实测(p13 pass@50·temp=1.0·当前 7/50·趋势已决定性)
```
p13_passk50  n=7
  correctness 口径: pass=6  gated=0  fail=1  rate=0.857  → TOO_EASY
  fast1 口径:       fast_pass=0       rate=0.0          → FAST1_TRUE_WALL
```
- **correctness 口径**:6/7 doubao 样本产出**正确**kernel(虽都慢 0.73-0.74×)→ p13 是 **TOO_EASY**(连 pseudo 都不是)。
- **fast1 口径(correct AND speedup>1)**:**0/7** 产出**又对又快**的 kernel → p13 是 **FAST1_TRUE_WALL**。

## 这说明(你 thesis 的关键)
同一道题,两口径结论相反:
- correctness 口径太松 → p13 沦为 too_easy → **不是燃料**。pass@5 的"true_wall"是采样假象。
- fast1 口径 → p13 是真 true_wall → **是燃料,且有 headroom**(doubao 产不出快 kernel·V5+复利记忆求"又对又快"有真实提升空间)。

→ **强烈支持口径并轨 fast1**:① 飞轮 reward 要 headroom(corerct-only 太易·doubao 6/7 就清)② 与买方 stump fast1@5 口径统一(一份投入喂两处)。

## 给你的(协助你决策)
1. **工具就绪**:`triage_aggregate.py` 现在一跑出双口径桶(`bucket` correctness + `fast1_bucket`)。eval 跑完(~90min)我回你 p13 完整 50 双口径数。
2. **verifier 待你一句话**:我的 `bench_eval_kernelbench.py` 现 emit `passed=pass_final`(correctness)。你若定 fast1,我把 `passed` 改成 `pass_final AND speedup>1` → mint 的题 reward=1.0 仅当 V5 产出又对又快的 kernel。`is_fast_pass` 逻辑已在 triage(speedup>1·可调阈值 FAST1_MIN_SPEEDUP)。
3. **若定 fast1**:p13 直接就是合格燃料(已 mint-ready·fuel dir + payload builder 都在)→ 等 gate B platform timeout + MCP 回来登 PoI 即可点火。不用再跑 p14/p15 找新题(p13 在 fast1 口径已是 true_wall)。

## 请你回(一句话即可)
true_wall 口径 = **fast1(correct+speedup>1)** 确认?确认我就把 verifier `passed` 切 fast1 门 + 准备 p13 mint(gated platform timeout + MCP)。

— compass · 2026-06-17(p13 双口径实测:correctness=too_easy / fast1=true_wall·工具就绪·verifier 待你定口径切门)
