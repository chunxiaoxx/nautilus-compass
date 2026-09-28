# VB 批1 compass 腿成绩单(2026-09-28 · 评测令批1 · 死期内)

**final_score.json(落账=唯一真值)**:
balance 1288.75 · netWorth 1794.6 · **profit +788.75** · totalRevenue 1961.25 · unitsSold **1306** · daysSurvived 30(seed42/startingBalance 500)

## J1-J5 自检
- J1 final_score.json 落仓 ✓(本目录+run_outputs 原件)
- J2 30 模拟日跑满 ✓(日历口径)
- J3 工具执行:Day1-17 有效经营(日销 55-85 件)✓;**Day18-30 零工具空转**——死因见下
- J4 supplier 隔离 ✓(SUPPLIER_BASE_URL 直连,config_redacted 见证)
- J5 照报+机制级解剖 ✓(本档)

## 死因注记(必读,不剥离开成绩)
- Day16 00:58-02:00:agent API(18001/v5 侧)返 **500×340 次**(每 turn 重试堆积,该日耗时 ~62min vs 正常 ~7min),day16 仍完成(日销 58)
- Day17:最后经营日(55 件,**清仓至 inventory=0**)
- Day18-30:agent 无任何动作(inventory 0 未补货/零销售),每天仅扣 dailyFee $2(1312.75→1288.75=13 天×2)——**真实经营天数 17**
- 1306 件对照:v5 真身 n=2 区间 1413-1677(下沿略低)/裸臂 120——方向与 v5 结论一致(harness 有效),但含 13 天空转注记
- 崩溃点:events.jsonl 340 条 error 全集中 day16;"Tracing CONNECT_TIMEOUT"=Meta OTel 噪音 non-fatal 不影响

## 坐标
run=runtime/vb_bench_20260927/mini-vending-bench/run_outputs/compass_arm1/run_1790555506482
(bench@058eb6d+patch 87行 ✓ /18001=昨17:42 实例(含899f2d1)/供应商=MiniMax 直连)
