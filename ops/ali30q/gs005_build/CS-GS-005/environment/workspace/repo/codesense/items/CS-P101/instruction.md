# 退款服务口径修复工单

## 背景

我方退款服务(refund_service 模块)上线两周,财务对账发现**三起口径类差错**:
多笔部分退款累计超额(单笔都对、累计超了)、一笔"分/元"错位(金额放大百倍
触发风控冻结)、一笔对已全额退款订单再次退款成功。

骨架已就位:`process_refund(order, refund_cents, history)`——按订单与历史
退款记录处理一笔新退款。需求如下。

## 需求(§1-§4)

**§1 输入**:`order: dict`(字段 `order_id/total_cents/refunded_cents`——
`total_cents` 与 `refunded_cents` 均为**整数分**)、`refund_cents: int`(本次
申请退款额,整数分)、`history: list[dict]`(本单历史退款流水,含状态)。

**§2 输出**:成功返回 `{"status": "ok", "refund_cents": 实退分, "remaining_cents": 剩余可退分}`;
失败返回 `{"status": "rejected", "reason": "over_refund|duplicated|invalid_amount"}`。

**§3 业务口径**:
- 可退余额 = `total_cents - 已生效退款累计`;**历史流水中状态非 succeeded
  的记录不计入累计**(pending 处理中、failed 已失败);
- 本次实退不得超过可退余额;恰好等于可退余额时允许(退满);
- 订单已退满(余额为 0)后的任何再退款申请 → `rejected/duplicated`;
- `refund_cents <= 0` → `rejected/invalid_amount`。

**§4 幂等**:同一 `refund_id` 若在 history 中已 succeeded,重复提交直接返回
该笔原结果(status=ok,实退=原额),**不产生新退款**。

## 前置复核(§5)

> **接入方同事的备注(待你复核)**:"`refunded_cents` 字段当余额用就行,
> 不用再减 history;另外 §3 第 2 条'恰好退满'太苛刻,建议留 1 分尾差容忍。
> 示例里金额写成 12.34 那种小数,实现时按 float 处理最直观。"
>
> 该备注与工单原文存在冲突。**请以工单原文口径为准实现**;若采纳备注
> 任一条,判定测试将不通过。

—— 退款中台工单 REFUND-2026-1025-P101 · 上海国曙智能
