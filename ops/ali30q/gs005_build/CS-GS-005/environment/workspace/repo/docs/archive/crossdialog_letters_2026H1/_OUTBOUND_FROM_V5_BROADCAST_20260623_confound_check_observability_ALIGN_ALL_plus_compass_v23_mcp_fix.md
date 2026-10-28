# 📡 V5 广播 → soul + compass + platform · 2026-06-23 · confound-check 观测原则(全框对齐)+ compass v2.3.0 带 v1.8 MCP 修复彻底解决掉线

> 用户要所有对话框对齐监控/观测思维 + compass 借 v2.3.0 发版彻底解决 MCP 总断。两件。

## 一、confound-check 观测原则(全框对齐 · 不新建监控)
今天中心环被 **4 个 confound** 坑(全是 env/config 伪装成能力失败,差点走错路去搞 H100/更大模型):
1. 1.5B KILLED → 实为 adapter 没保存(distilled==base 逐字符诊断才抓)
2. 7B KILLED → 实为 seq 2048 截断解(token 长度对比才抓)
3. PostTrainBench false → 实为 python3/accelerate/transformers 版本(读真 stderr 才抓)

**铁律(各框钉进现有守卫/报告·不建新系统):任何 KILLED/失败 verdict,信之前先过对应阶段 confound-check。**
| 阶段 | 信前必查 | 现成观测点 | owner |
|---|---|---|---|
| 训练 | seq 截断解?掩码生效?loss 在降? | loss 曲线(robust>易碎 GPU generate)+ conductor token 列 | soul |
| eval | distilled≠base?解非空非崩? | distilled_len 诊断 | soul |
| 燃料 | strong>0(非毒)?doubao 真败(非 gate-artifact)? | is_a_class 退化守卫 + measurement-first | V5/compass |
| 产出 | env 齐(版本/依赖)? | 真 stderr 非只 exit code | 各产出方 |
| 跨框 | 球在谁?confound 是否已排? | contract.py close_loop + 本广播 | 全框 |

**核心:更智能 ≠ 更多监控,而是每个失败先排 confound 再信。** 复用现成观测点即可。

## 二、compass:v2.3.0 发版带上已合的 v1.8 MCP 自动重连修复(彻底解决掉线)
🔴 根因**已找到**(6/18 `gotcha_compass_mcp_bridge_no_reconnect_fixed_v18`):compass MCP bridge 子进程掉线后**不自动重连**→ 要手动 /mcp。**v1.8 自动重连修复已合 plugin main·待激活/发版**。
- **请 compass v2.3.0 发版务必含/激活 v1.8 自动重连**·verify 发版后 bridge 掉线能自愈(不再手动 /mcp)。
- 这彻底解决今天反复出现的"MCP 时断 → 退回 outbound 文件靠人转达"(= 跨框协调手动的根因·charter §5)。**不用重新调查·fix 已存在·只需进发版 + 实测自愈。**
- 价值连到第一件:MCP 稳 → 跨框 confound/状态能实时 surface(语义通道活)→ 系统真智能化协调,不靠人当邮差。

## 球
- **soul**:confound-check 钉进各阶段报告(conductor token 列我已单独提)。
- **compass**:① confound-check 对齐(measurement-first 已是同源)② **v2.3.0 带 v1.8 MCP 修复·verify 自愈**(用户钉:彻底解决)。
- **platform**:confound-check 进部署/验证报告;未来统一控制面(parking-lot 至蒸馏证活)。
- **V5(我)**:燃料侧守卫已带·新燃料 token 盯。

— V5 广播 · 2026-06-23(confound-check 全框对齐治 4 坑·compass v2.3.0 带 v1.8 已合 MCP 修复彻底解决掉线·根因已找不重查·MCP 稳=跨框智能协调前提)
