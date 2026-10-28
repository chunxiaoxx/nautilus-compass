# 🎯🔴 platform-soul → V5 + compass · 2026-06-24 · 战略重评:A 类产率根瓶颈=强模型 glm·qwen3.7-max 是解药(ALE+SWE 共享)

> 用户要求重评(路A 三重成本 vs agent 自治第②维)。grounded 重评后发现:三条路卡同一瓶颈。全框对齐。

## 贯穿性发现:三条路共卡「强模型解出率」
今天 SWE verify(0 A 类)+ 回看 ALE,坐实一个贯穿瓶颈:
- **SWE**:glm 产 diff 全解不对(pytest p2p 破·flask f2p 0/2·6/23 glm 2 道也 0 A)。
- **ALE**:glm @32000 跑难题全 timeout(13 道难题·只救活易题)。
- = **A 类产率(ALE + SWE)根瓶颈 = 强模型 glm 解出率/吞吐**·非路径选择。

## 🔴 最高杠杆 = glm → qwen3.7-max
- **probe 实证**:qwen3.7-max 解出率高(`rsi2/probe_*.json` model=qwen·pytest 2/2·sklearn 9/10·flask 1/2·django 6/7)。glm 没验证过解这些·实测解不对。
- **换 qwen 是 ALE + SWE 的共同解药**·是让蒸馏 forcing function 真正能跑的前提。glm 再熬(timeout retry)≠ 解对。

## forcing function 现状(诚实)
- 北极星 forcing function = 「先证/杀蒸馏那一步」**还没干净达成**:ALE 弱 KILL(0.18·料量 vs 同质未排除)· SWE 没测成(glm + 根盘 infra)。
- 绕过它转纯 agent 自治 = 回"内部自循环不闭外部环"老病(中心环 dossier 元教训)。第②维(今天 soul 修了 #1 a2a/#3 evolution/#5 kairos 基础)是中心环另一半·但产料质量同样依赖强模型解出率。

## 推荐逻辑顺序(便宜 → 贵)
1. **glm → qwen3.7-max 换 producer strong model**(V5·根瓶颈解药·ALE+SWE 都受益)。
2. **ALE qwen 重凑料**(可能破 glm timeout 墙·凑 n=30-50·便宜·pipeline 已通)→ 排除"料量"假设。
3. **若 ALE n=30-50 仍弱** = 坐实"同质性/本质难" → 才值得投路A 三重成本(qwen 重产 + 根盘迁 datadisk0 + soul 建 SWE eval pipeline)测同质性。
4. 根盘 50G infra(SWE verify 吃不消)= 投路A 前置 · V5 迁 docker datadisk0。

## 球
- **V5**:① producer strong model 全换 qwen3.7-max(ALE + SWE 共同解药·最高杠杆)② ALE qwen 重凑 n→30-50 ③ 根盘迁 docker datadisk0(投 SWE 前置)。
- **compass**:#4 memory_records 复活(agent 自治第②维·与蒸馏并行不冲突)。
- **soul**:协调中枢 · ALE qwen 凑到 n=30-50 跑蒸馏第4测 · SWE eval pipeline 待 ALE 排除料量后再建(de-risk:未实现·成本高)。
- **元判断**:别再用 glm 熬(timeout/解不对都是它)。qwen 是解药。先用 qwen 让"证/杀蒸馏"真正能跑·再谈路径选择。

— platform-soul · 2026-06-24(战略重评:三路共卡强模型 glm 解出率·qwen3.7-max 是 ALE+SWE 共同解药·推荐 glm→qwen 后先 ALE qwen 重凑排除料量·再决定投路A·第②维基础已修够)
