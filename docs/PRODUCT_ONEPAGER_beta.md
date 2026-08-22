# compass · Verified Memory(Open Beta 一页纸)

> 你的 coding agent 犯过的错,不再重犯。

## 问题
AI agent 每次新会话都从零开始:上次修好的 bug、踩过的坑、验证过的解法,下次全忘。
现有"记忆层"产品(Mem0/Letta 类)记住一切——包括大量噪声和错误经验,
让 agent"记得多"而不是"学得对"。

## 我们做什么
**只把经过独立验证的经验喂给 agent。**

- 每次任务产出(代码/修复/决策)自动过**确定性验证器**(pytest/编译/程序化判据)
- 三臂对照实验(control vs treatment)证明经验**真的有用**才入库(Gold)
- 入库经验带全套溯源:谁产的、谁验的(必须异构)、哪次运行、什么判据
- 裸模型做不出来的任务才学(headroom 门)——模型已会的经验不浪费存储

一句话:**持续学习,不重训权重**——SSI 们承诺的方向,今天就能装在你的 Claude Code / agent 上。

## 效果怎么量
核心指标 = **重犯率**(同类错误再次出现的频率)。装上 compass 后你会看到它下降。
附:验证储蓄率(VSR)= 验证通过经验 / 总经验,你的 agent 的"学习质量"体检表。

## 为什么是我们
- 理论:判官盲区/空转定理(judge 与 generator 同构必盲——所以我们的验证全部异构)
- 实录:五万次空转的第一手失败账 + 首次 Gold 实验(经验迁移 delta=1,可复现)
- 工程:append-only 飞轮账本、fail-closed、防重放,证据链全程可审计

## 装(3 分钟)
```bash
# Claude Code 插件
claude plugin install nautilus-compass
# 或任意 MCP 客户端接云端点(带 token)
```

## 路线
- Beta(现在):插件 + 云 MCP + 重犯率仪表
- Next:verified-trajectory 数据交付(给你的持续学习模型供 B3 级真值燃料)
- 远期:VSR/B 分级计量标准

---
*开源 Gate B harness(验证学习参考实现)随论文发布;账本/裁决/PoI 闭源。*
