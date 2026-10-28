# 告警分发服务口径对齐工单

## 背景

我方告警分发服务(alert_dispatch 模块)新增**告警分级分发功能**:`dispatch_alert(alerts, config)`——
按告警级别和目标渠道分发通知。上线三天出两起**口径差错**:
一条 `severity=critical` 的告警被发到了 `email` 渠道(应发 `pager`),
一条 `status=resolved` 的告警被重复投递(应只投未恢复的)。

骨架已就位:`dispatch_alert(alerts, config)` 签名与返回结构已定。需求如下。

## 需求(§1-§4)

**§1 输入**:
- `alerts: list[dict]`(字段 `alert_id/severity/status/channel/created_at`;
  `severity` 取值 `critical/warning/info`;`status` 取值 `firing/resolved`)
- `config: dict`(字段 `channel_priorities: dict`;键=severity 值=该级别对应的
  渠道名列表,按优先级降序)

**§2 分发口径**:
- 每条告警按其 `severity` 从 `channel_priorities` 中取**首个可用渠道**投递
  ("可用"=该渠道在 `config["available_channels"]` 列表中);
- `status=resolved` 的告警**不投递**,但需在结果中标记为 `"skipped"`;
- 同一 `alert_id` 已投递过的**不重复投递**(结果中标记 `"deduplicated"`);
- 如果 severity 对应的所有渠道都不可用→投递到 `"fallback"` 渠道;
- 如果连 fallback 也不在 available_channels 中→**跳过并标记 "no_route"**。

**§3 输出**:`{"dispatched": [...], "skipped": [...], "deduplicated": [...], "no_route": [...]}`;
每个 dispatched 元素含 `alert_id/channel/attempts`。

**§4 渠道优先级冲突**:
`channel_priorities` 中同一 severity 可能对应多个渠道——**按列表顺序**取第一个
在 `available_channels` 中的渠道。如果列表中第一个渠道不可用但第二个可用,取第二个。

## 前置复核(§5)

> **运维同事备注(待你复核)**:"resolved 的也可以发,让下游知道已恢复——
> 这个信息也有价值。另外 fallback 不用单独配,available_channels 里没有
> 就默认发 email 吧。"
>
> 该备注与 §2 冲突。**以 §2 原文为准实现**;采纳备注任一条,判定测试
> 将不通过。

—— 告警中台工单 ALERT-2026-1025-P701 · 上海国曙智能
