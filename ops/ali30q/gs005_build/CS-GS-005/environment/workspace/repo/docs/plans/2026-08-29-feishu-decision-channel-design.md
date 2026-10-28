# 飞书双向选择题通道 · 设计稿(2026-08-29)

> 用户拍板:IM 通道用飞书。本文为设计稿,platform 认领实施,V5/compass 消费。
> 背景:各框升级事项靠 outbound 文件+cron 催办,用户看不到、决策不闭环。目标 = 升级事项变成飞书卡片按钮,用户点选,决策入库,goal-loop 轮询执行。

## 复用现有资产(不重造)

| 资产 | 位置 | 用途 |
|---|---|---|
| 飞书自建应用 | T1 闭环已在用(OAuth/Bitable 权限齐) | 发卡片+收回调,不建新应用 |
| platform 云服务器 | nautilus.social(nginx+backend 8000) | 卡片回调接收端(公网 HTTPS) |
| mailbox 端点 | platform org OS P0(commit 5654eb801) | 决策落库可复用其幂等/deadline/ack 模式 |

## 数据流(单向发 + 回调收)

```
升级事项(任一框)
→ POST platform /api/feishu/decision/card
  {trace_id, question, options[2-4], deadline}
→ 飞书开放平台 im/v1/messages(card)发到用户
→ 用户点按钮
→ 飞书回调 platform /api/feishu/decision/callback(card_action)
  → 落表 feishu_decisions(trace_id, option, decided_at)
→ 各框 goal-loop 轮询 GET /api/feishu/decision/pending?frame=v5
  → 读到答案 → 执行 → ack
→ 超时未决:卡片更新提示"已超时,默认按保守项执行/挂起"(预注册 default)
```

## 关键设计决策

1. **卡片必须有 deadline + 默认项**:不点 = 按预注册保守默认执行,治"等确认空转"
2. **trace_id 强制**:与 outbound 事件协议同 trace,决策可溯
3. **幂等**:同 trace_id 重复回调只记第一次
4. **安全**:回调验飞书签名(verification token),platform 已有验签经验(8/27 TDD 过)
5. **权限**:先只发给用户本人(open_id 单发),不做群广播

## 实施拆解(platform 侧,估半天)

- [ ] 表 `feishu_decisions`(trace_id/option/decided_at/ack)
- [ ] POST /decision/card(发卡片,复用 T1 应用 tenant_access_token)
- [ ] POST /decision/callback(验签+落表+幂等)
- [ ] GET /decision/pending?frame=(goal-loop 消费端)
- [ ] 事件订阅 URL 配置(飞书开放平台后台,需用户在管理后台点一次"确认回调地址")

## 用户需做的(1 次性,5 分钟)

1. 飞书开放平台后台:给现有 T1 应用加"卡片回调"事件订阅,或告诉我把回调 URL 填哪
2. 提供该应用的 app_id/app_secret 存放位置(若 platform 未持有)

— V5 框代拟 · 2026-08-29
