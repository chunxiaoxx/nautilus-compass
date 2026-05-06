# compass license · MIT vs Apache 2.0 (dual) · decision tracker

> Status: undecided · 2026-05-05
> Author: chunxiaoxx
> Decision deadline: v1.0 GA (2027-05) · earliest 2026-12 (融资节点)

## Current state (v0.9.0-dev)

**License**: MIT (sole · since v0.7.0 · `LICENSE` file in repo root)

```
MIT License

Copyright (c) 2026 chunxiaoxx
[full text in LICENSE]
```

## Tension

```
Pure MIT (current):
  + 最大化采用 (任何项目 · 任何商用 · 任何 fork)
  + 简单 · 1 个文件 · 0 法律开销
  + 跟 paper 1 (drift detector) license 一致 · 没分裂
  - 大企业可以 fork 自托管 · 不回流社区
  - 没有"高级版"区分点 · enterprise 卖不掉
  - 商业化路径不明 · 融资 deck 难讲

MIT + Apache 2.0 dual (v1.0 提议):
  + 个人/SMB: MIT (跟现在一样)
  + 大企业自托管: Apache 2.0 (要求贡献回流 · 专利反诉条款)
  + 给 enterprise 卖支持/培训/咨询的 anchor
  + 跟 Nautilus 平台 enterprise plan 衔接
  - 法律复杂度上升 · 需要 CLA (Contributor License Agreement)
  - 现有贡献者需要重新 sign · 麻烦
  - 不彻底解决 fork 问题 (Apache 仍允许 closed-source 衍生)

AGPL (拒绝 · 但提一下):
  + 强 copyleft · 自托管也要开源
  - 杀死大部分采用 (商业用户怕 copyleft)
  - 跟 MCP/A2A 开放生态对立
  → 不考虑
```

## 三家做法 (借鉴)

```
Mem0:        Apache 2.0 sole · 简单
Letta:       Apache 2.0 sole
Zep:         Apache 2.0 sole · 但有 Zep Cloud 闭源管理面
claude-mem:  MIT (但作者私人项目 · 没商业化)
我们 · v0.7: MIT
```

→ 业界主流 = Apache 2.0 sole · 不 dual

## 推荐

```
v0.9.x: 维持 MIT (现状)
v1.0:   切换到 Apache 2.0 sole (跟业界一致)
        · 加 CLA · 但保留所有现有 MIT 贡献以 MIT 许可证 (双重许可声明)
        · 在 v1.0 release 前 30 天通知所有贡献者
        · 商业化路径靠"compass.nautilus.social hosted plan" · 不靠 license
        · 严格的"自托管社区版" === Apache 2.0 OSS · 不阉割

理由:
  · Apache 2.0 比 MIT 多 1 条专利反诉条款 · 防御性更好
  · 跟 Mem0/Letta/Zep 一致 · 业界期待
  · 不要 dual · 复杂没必要
  · 不要 AGPL · 杀采用
  · 商业化靠 SaaS · 不靠 license
```

## 决策时间表

```
2026-05 (now): 维持 MIT · 不变
2026-12 (融资节点): 跟投资者讨论 license 取向 (普通 VC 不 care MIT vs Apache)
2027-02 (v1.0 RC): 决定 v1.0 license
2027-05 (v1.0 GA): 应用决定的 license

中间 (2026-06 ~ 2026-12): MIT 保持 · 加新贡献以 MIT · 不切换
```

## 不切换的退路

如果 v1.0 没切 Apache 2.0 · 后果:

- compass 维持 MIT 永久 · 可接受 (但商业化路径需要 SaaS-only)
- enterprise 客户买 hosting · 而非 license · 这条路也通
- 长期看 · MIT 跟 Apache 实质区别不大 (都允许商用)

## 如果切了 Apache 2.0

后续工作:

```
1. 写 CLA (Contributor License Agreement) · 用 cla-bot 自动收集签名
2. 确认现有贡献者 (目前只 chunxiaoxx 1 人 · 不复杂)
3. 修改 LICENSE (从 MIT → Apache 2.0)
4. 更新所有源文件 header (现有源文件没 header · 不破坏)
5. 更新 pyproject.toml license = {text = "Apache-2.0"}
6. 更新 npm package.json license = "Apache-2.0"
7. 更新 README · CONTRIBUTING · CHANGELOG 提到 license 切换
8. 通过 30 天 notice 通知用户 (虽然只是 OSS license · 法律上不需要)
```

## 决策记录 (本文件应在 v1.0 前保留更新)

| 日期 | 状态 | 说明 |
|---|---|---|
| 2026-04-29 | MIT 起点 | v0.7.0 release |
| 2026-05-05 | 评估 dual 决定不做 | 复杂度太高 · 暂维持 MIT |
| 2026-05-05 | 提议 v1.0 切 Apache 2.0 sole | 跟业界一致 |
| TBD | v1.0 实际决定 | 等到 2027-02 RC |
