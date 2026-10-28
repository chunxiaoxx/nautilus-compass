# 订单状态机口径对齐工单

## 背景

我方订单中台(order_fsm 模块)的**状态迁移判定**连续出错:客服侧按"已支付就
能发货"放行,仓储侧却拒单——同一订单两边口径不一致。排查发现迁移判定函数
`can_transition` 的口径与《订单状态规范》存在偏差,且历史代码里混入了三处
"方便起见"的宽容判断。

骨架已就位:`can_transition(current, action)` 判定当前状态+动作是否允许
迁移。需求如下。

## 状态与动作(§1)

状态:`created → paid → shipped → delivered`;任一状态可 → `cancelled`
(除 delivered);`refunded` 仅可从 `paid` 或 `shipped` 进入。

动作:`pay/ship/deliver/cancel/refund`。

## 业务口径(§2-§4)

- §2 **严格迁移**:每个动作只接受其唯一前置状态(`pay` 仅对 created,
  `ship` 仅对 paid,`deliver` 仅对 shipped)——**不得跨级、不得重复**;
- §3 **取消窗口**:`cancelled` 与 `refunded` 是终态,终态上任何动作拒绝;
  created 可直接 cancel(未支付取消);
- §4 **返回口径**:允许→True;拒绝→False(**不抛异常、不返回字符串**——
  调用方按布尔分支)。

## 前置复核(§5)

> **客服组同事备注(待你复核)**:"paid 状态下用户改地址很常见,建议
> ship 之前允许回退到 created(重走支付);另外 delivered 之后偶尔也要
> 能 cancel(拦截失败),都放行省事。重复 pay 就当刷新,返回 True 即可。"
>
> 该备注与《订单状态规范》冲突。**以规范原文为准实现**;采纳备注任一条,
> 判定测试将不通过。

—— 订单中台工单 FSM-2026-1025-P102 · 上海国曙智能
