# VB mini-vending-bench 批1 · 预注册判据档(compass)

> 报数纪律(用户 9/15 拍板 + soul 提案 approved):对外报数字的任务,开工
> 先落预注册判据,收工走非实现者视角。判据只许更严。交接档只给坐标与
> 命令,**不给任何预期读数**。
> 评测令:platform 1105 转发(用户原令)· 批1 死期 **9/28** · v5 出周榜。

## 冻结口径(禁改)

- seed42 · 30 模拟日 · 落账(final ledger)=唯一真值 · features 默认
- 同口径禁改判分;负结果照报(宪法第五条);供应商隔离(SUPPLIER_BASE_URL)

## 预注册判据(跑完自检,全过才算完成)

| # | 判据 | 红灯处置(先证伪自己) |
|---|---|---|
| J1 | final_score.json 生成于本框仓 `runtime/vb_bench_20260927/` | 无产物=没跑完,不算任何分 |
| J2 | 30 模拟日跑满(seed42 不变) | 中途崩=照报崩溃点,禁改 seed 重跑凑数 |
| J3 | **工具执行>0**(v5 第四坑 899f2d1 修的零工具病;若 30 日零工具→先查 patch 链:API 探活/config 指向/版本,非 bench 有病) | grep 工具调用痕迹;API 18001 日志 |
| J4 | supplier 隔离生效(判分链独立于被测模型链路) | 查 BENCH_CONFIG/SUPPLIER_BASE_URL 实载值 |
| J5 | 分数照报:正负同权,失败解剖到机制级 | 负结果=照报+解剖,不许只报 day 数 |

## 执行坐标(今晚 22:00 窗,约 15-25 分钟)

1. bench clone:`Wayfound-AI/mini-vending-bench` @`058eb6d` →
   `runtime/vb_bench_20260927/mini-vending-bench`(干净 clone,非复用)
2. bench 侧 patch:`git apply C:/Users/chunx/nautilus-v5/docs/vb_bench_side.patch`
   (87 行:getAgentModel 显式 ChatCompletions+BENCH_CONFIG loader+supplier 隔离;
   物理验证 9/27 01:04 存在 3757B ✓)
3. 依赖:`npm install`(node ≥24 已在机)
4. v5 侧 API:`cd C:/Users/chunx/nautilus-v5 && python _run_v5_api_18001.py`
   (前置:仓 HEAD 必含 **899f2d1**(tool_calls 非空时 content=None——
   @openai/agents JS SDK 规矩,MiniMax planning 文本同填两字段=工具被丢,
   v5 昨夜 30 日零工具根因);当前 HEAD c309d73 已含 ✓;SelectorEventLoop 已处理)
5. 跑法五步:见 `C:/Users/chunx/nautilus-v5/docs/VB_ONBOARDING_PACK_20260926.md`
6. 产物:final_score.json + run_outputs 落 `runtime/vb_bench_20260927/`
7. 报数:坐标函报 v5(周榜)+ LOOP_STATE 记轮 + 本档 J1-J5 自检表回填

## 交接纪律

- 本档不含任何预期读数;执行会话照坐标跑,读数以 final_score.json 为准
- v5 patch 坐标函:id 1166(已 ack);我方排期函:id 1150
