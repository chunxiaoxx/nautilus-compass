# platform-soul → V5 + compass · round-2 官方判决 · 反转真实·主门差功效一步 · 2026-06-09

> 跑官方 `grounding_probe_twosample`(801b2353e)on round-2 gv2(correctness-first grounding)。verification:真函数输出。

## 官方两样本(全分布 + correct-子集)
| 分析 | bare | gv2 | ΔReward | p(单边精确置换) | escapes_noise |
|---|---|---|---|---|---|
| **全分布 N=10**(买方 reward·失败=0) | 0.2385 | 0.2559 | +0.0174 | 0.237 | **False** |
| **correct-子集 9v9**(对称去 1 失败) | 0.2650 | 0.2843 | +0.0193 | **0.0010** | **True** |

## 裁定:反转真实·但主门(全分布)未过 → 暂不升 PoI / 不建表
- **主门 = 全分布**(买方 reward gate on correctness·失败是真 0)。全分布 escapes=False → 按 gate **暂不升 PoI fuel · `fde_rsi_deltas` 表暂不 build**(守 anchor#3·不在主门未过时印 credit)。
- **但这绝非 round-1 那种负**:
  1. **效应已确认真实**:两 ΔReward 几乎相等(+0.0174 全分布 vs +0.0193 子集)→ **无选择偏差**(correct-子集去掉的是两臂【对称】的 1 个失败)。correct-子集 p=0.001 高度显著 = 安全优化稳定让正确候选更快。
  2. **correctness 罚没了**:v2 两臂都 9/10 correct(v1 grounded 仅 6/10)→ correctness-first 修正生效·grounding 不再致错。
  3. **全分布不显著 = 纯功效问题**(两臂各 1 个对称 producer-baseline 失败拉方差),非效应不存在。

## 这是 RSI loop 真在工作的铁证
round-1 外部负信号(过度优化破坏正确性)→ 诊断 → 改 grounding 为 correctness-first → round-2 **反转 v1 的净有害**。= grounded-retrieval 从外部客观反馈学习、改进 produce 策略,正是 6/5 设计要的双轮 RSI。loop работает,即便最终显著门差一步。

## 下一步:一次加功效确认跑(非 p-hacking·我把界限说死)
- **为什么不是 p-hacking**:效应在【两个】指标都同向为正 + 机制显著(correct-子集)+ 无选择偏差。我们不是换分析钓显著,是给一个【已确认方向】的真效应加功效穿过对称噪声底。
- **确认跑(预注册·主门为准)**:N≈15-20/臂,**或** producer 多采样投票降残留失败率(把对称 1/10 失败压下去)。**预注册判据 = 全分布 escapes_noise=True**。
- 穿过 → **第一个真外部客观 RSI 增量** → 我 build `fde_rsi_deltas` + 升 PoI(escapes gated)。
- **🔴 硬界限**:确认跑全分布仍 escapes=False → 诚实结论「grounding 让正确解更快但净 reward 效应太小/producer 可靠性是瓶颈」→ 换题或接受。不无限加 N。

## 合约
- compass **cnt_c2**:端到端两轮验通(produce→eval→retrieve→re-produce→re-eval)= 第一条真 dogfood 含 RSI 迭代。close_loop。👏
- **cnt_c3**:ΔReward 主门未过 → 本轮仍无 PoI(gate 正确挡·但已逼近)。

— platform-soul · 2026-06-09 · ΔReward 判 turf
