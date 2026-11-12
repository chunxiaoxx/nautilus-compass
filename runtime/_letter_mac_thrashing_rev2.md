[任务单修订 REV2] thrashing 主犯定位完成——happy remote 会话层(非 relay 主责),处方更换

Mac compass:

撤回 autocompact-thrashing-fix-1031 中"relay 主责"的判断。compass 补齐对照实验后主犯锁定:

## 决定性数据(home 桶全部会话按入口分组)
| 入口 | 会话数 | ≥3 次 thrashing |
|---|---|---|
| remote_mobile(happy 手机/远程) | 3 | **3/3 = 100%** |
| cli(桌面原生) | 9 | 仅 1(轻度) |

thrashing 集中在 **happy remote 会话链路**,compact 触发阈值被钉在 ~64k(多会话一致复现)——happy SDK 对第三方模型(glm-5.3[1M])的 context window fallback 错误。机制推测:happy SDK 调 count_tokens → relay 404 → fallback 字符估算 → 中文内容高估数倍 → 6 万实际被估"满"。

## 三层责任重判
- CC CLI 桌面模式:基本无责(cli 9 会话仅 1 轻度,桌面长会话不受影响——实测 resume 正常)
- cc-switch:无责(纯配置管理,proxy 未启用)
- relay:单请求 usage 规范(input_tokens 准确);仅缺 count_tokens 端点(次要,但它是 happy fallback 估算的诱因之一,实现仍有价值)

## 处方(REV2)
1. **止血(即刻,零成本)**:长会话/重任务一律走桌面原生(`nclaude` 或 ~/.local/bin/claude 直开)——桌面已实测无 thrashing;手机 happy 只做轻交互/监控/审批
2. **happy 侧(你做)**:
   a. `npm i -g happy-coder` 升级到最新,复测 remote 会话 compact 触发点
   b. 向 happy 项目(github.com/slopus/happy)提 issue:第三方模型 glm-5.3[1M] 经 remote 入口时 compact 阈值钉死 ~64k,应读模型真实窗口(附本次数据:22/23 次 compact 在 61-69k 触发)
3. **relay 侧(候用户)**:实现 count_tokens 端点(对 happy SDK 与桌面 CC 双收益)
4. 验收:remote 会话 compact 触发点从 61-69k 抬升;或用户长会话全迁桌面后不再出现

—— compass 只读顾问 · trace=autocompact-thrashing-fix-1031-rev2
