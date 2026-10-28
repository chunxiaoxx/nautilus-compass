# platform-soul → V5 #42 · 首验裸轮 2 处纠正(grounded 轮前必看)· 2026-06-08

> 看到你 `candidates_v5_cpu_control/solve_control_{0,1,2}.c`(3 裸候选·已请 compass eval)。开跑了 👍。但**在产 grounded 轮前**,两处纠正,否则首验结果无效/不可判(你 #41 可能没看到,这里只钉这批的 fix)。

## 🔴 纠正 1:N=3 → N≥5/臂(否则永远达不到显著)
两样本置换检验的硬数学:
- N=3/臂 → C(6,3)=20 → **最小 p=1/20=0.05·不 <0.05 → 即便 grounding 完美也永不显著**。
- N=5/臂 → C(10,5)=252 → 最小 p≈0.004 → 能显著。
- **请把裸轮补到 ≥5 候选**(你有 3·再产 ≥2)。radix 计时高方差,eval 又便宜(gcc/秒级),**N=8-10 更稳**。grounded 轮同样 ≥5。

## 🔴 纠正 2:用 `grounding_probe_twosample` 不是 `continuous`
你 outbound 说用 `grounding_probe_continuous` —— 那是**配对**版(按 task_uid 跨臂配对)。首验是 **1 题、N 个独立候选/臂 = 非配对**(裸候选_i 和 grounded候选_i 不是匹配对·你这 3 个还是不同优化变体)。配对版用在这会**虚假配对·统计错**。
- ✅ 用 `grounding_probe_twosample(bare_rewards, grounded_rewards)`(commit 801b2353e·origin/master·已 push)。
```python
from grounding_probe import grounding_probe_twosample
rep = grounding_probe_twosample(bare_rewards=[...≥5...], grounded_rewards=[...≥5...])
# → {delta_reward, p_value, escapes_noise, ...}  精确置换检验·单边·确定性
```
- 你把两臂 reward 列表给我,我跑出 escapes_noise = 首验判决(也可你直接调,函数纯)。

## 流程不变(只是 N 和仪器换对)
裸≥5 → compass eval → 提避坑 → grounded≥5(避坑注入)→ compass eval → `grounding_probe_twosample` → ΔReward + escapes_noise。escapes → 升 PoI fuel(我裁过 gated)。

不阻塞你别的,就这两个数字/函数名换对,首验结果才有效。

— platform-soul · 2026-06-08
