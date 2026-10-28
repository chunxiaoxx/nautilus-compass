# 飞书选择题通道设计(decision-card · 2026-08-29)

> 用户拍板:决策兜底在人,人做选择题,随时随地接入 IM=飞书。
> turf:platform 实施(端点+订阅),各框复用;本稿由 V5 起草供 platform 认领。

## 目标

升级事项/待拍板项 → 用户飞书里看到 **卡片+2-4 个按钮** → 一点 → 决定落库 → 各框 goal-loop 读数执行。治"outbound 文件用户看不见+催办靠碰"。

## 架构(五步)

```
① 发起方(V5/compass goal-loop)
   POST {backend}/api/feishu/decision
   {trace_id, title, options:["A","B","C"], default:"A", deadline, context(1 句话)}
② platform 用既有飞书应用凭证发 interactive card 给用户 open_id
③ 用户点按钮 → 飞书回调 {backend}/api/feishu/card/callback
   (URL 验证 challenge + 加密签名校验,飞书开放平台事件订阅配置)
④ platform 落库 decision(card_trace_id, choice, decided_at, operator)
⑤ 各框轮询 GET /api/feishu/decision/{trace_id} 读结果执行
   deadline 未决 → 记 default 并在值守汇报亮牌
```

## 复用与前置

- 复用 T1 智涌飞书应用(已有 OAuth/Bitable 权限)——**需增配**:①启用机器人 ②IM 权限(im:message:send)③事件订阅 URL 指向 platform 回调端点 ④发布版本
- platform 已有:cloud backend(systemd)+ Bitable 仓储 + 验签先例(T1 设计里飞书验签已设计未接)
- 新增表:`feishu_decisions`(id, trace_id, title, options_json, default, deadline, choice, decided_at)

## 需要用户做的(10 分钟,一次性)

1. 飞书开放平台 → 智涌应用 → 加机器人+IM 权限 → 事件订阅填 platform 回调 URL → 发版
2. 告知接收 open_id(或拉机器人进一个"决策"群,发群卡片)

## 安全红线

- 卡片内容不携客户 PII/甲方名/密钥;context 只放决策必需
- 回调验签失败静默丢弃+计数告警;decision 表仅内部读
- 未配置完成前,本通道不上线,不替代现有值守汇报

## 工作量

platform 端点+表+验签:TDD 半天~1 天;飞书配置(用户):10 分钟。完成后各框只需一个 POST 调用。

— V5 起草 · 2026-08-29
