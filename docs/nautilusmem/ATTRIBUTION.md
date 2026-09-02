# NautilusMem/T0 attribution 与许可结论(2026-09-03 凌晨 · LOOP 轮产物)

## 上游事实(已核实)

- 仓库 [xiaowu0162/LongMemEval-V2](https://github.com/xiaowu0162/LongMemEval-V2)(Di Wu 等,UCLA 系;2026/08 仍在活跃更新 AgentRunbook-C V2)
- 组成:451 手工题 + 5 记忆能力(static state / dynamic state / workflow knowledge / environment gotchas / premise awareness)+ web/enterprise 双域 + small/medium 两档 + **官方 leaderboard(submission form,禁 issue 提交)**
- **官方口径**:reader 固定 Qwen3.5-9B(我们一致 ✓)· embedding Qwen3-Embedding-8B · judge **gpt-5.2 medium reasoning**(我们=doubao-seed-2-0-pro low/16384,口径不同 ✗)
- 第三方接入:官方支持自定义 memory backend(`@register_memory` + `insert/query` 接口)——**我们的 compass 后端(lmev2_compass_memory.py)正是这条官方路径**

## 许可结论(保守策略)

- 上游 GitHub README **无 license 声明**(GitHub API 超时未查到 LICENSE 文件;HF dataset license 字段同样待查——代理不稳,下轮补)→ 按 all-rights-reserved 保守处理
- **我们只发布**:①自研代码(lmev2_compass_memory.py 记忆后端/判分修正工具/摘要卡生成器)= 我们的作品,MIT 自定;②对上游 harness 的 patch **以 diff 形式**(不内嵌上游代码);③跑分 evidence(jsonl/成绩)
- **不发布**:上游题目/轨迹/截图/harness 副本
- T1 自创新题若用上游轨迹改编:需 HF dataset license 落地后再定(待查项)

## T0 路径修正(基于官方 leaderboard 发现)

**首选:向官方 leaderboard 提交 compass 跑分**(submission form)——权威背章、零分发负担、社区可见性最高。
前提二选一:
- A. 按官方 judge(gpt-5.2 medium)复跑 451 题(需 OpenAI key,成本 ~几美元级,与用户确认资源)
- B. 提交时声明 judge 口径差异(doubao low/16384 + 重判修正故事),附双口径数字——社区可信度略降,但判分修正本身是卖点

**并行:GitHub 发布自研部分**(compass backend for LME-V2 + 判分卫生学协议 + 调优记录),attribution 上游、不含其代码/数据。

## 待查项(下轮 LOOP)

- [ ] HF dataset license 字段(代理稳时用 python huggingface_hub.HfApi().dataset_info 拉)
- [ ] 上游 leaderboard 现有 baseline 数字(RAG/AgentRunbook 的公开成绩)——成绩册对比表的原料
- [ ] 上游 leaderboard 提交格式的具体要求(leaderboard/README.md,需进 repo 看)
