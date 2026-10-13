---
name: orgfuel-ORGQ-R245-3edbcee08f
description: "### R245 · 2026-10-06 09:0x(用户两连令落地:RSI 信号衰减→rsi-bench #4 已发"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R245
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R245 · 2026-10-06 09:0x(用户两连令落地:RSI 信号衰减→rsi-bench #4 已发+自有 benchmark 立项)
- **用户插话一**:"RSI 最大的问题是信号衰减严重"→**rsi-bench Issue #4 已发 [实测]**(https://github.com/sunghunkwag/rsi-bench/issues/4):effective-gain(margin-gain)gate 提案——表观增益 vs 有效增益,以我方 Round 1 案例反例开题(+10.0pp 表观/格式层 A15+B11 回收空间);承诺 25 题回归集+rubric 可开 follow-up PR;AI 协助披露随件
- **用户插话二**:"我们应该有自己的 benchmark"→**立项档落地** docs/benchmarks/SELF_BENCH_CHARTER_V0_20261006.md:两轴设计(信号衰减轨+判分器保真轨)/种子题库全自有资产(E1 金标 898+anchor 1454+L3 全工件+25 题回归集+16 案)/判据预注册框架/命名查重(signal-decay-bench 0 撞全净·JudgeBench 撞 133★ 弃)——**名字待用户拍**;PMF 第一件事(自建基准集)落位,rsi-bench #4=引流砖,自有基准=承接
- **E1 回放发车进行中**:判分器定位毕(BASE=Qwen3-1.7B@vdd2/models+champion_17b_lora adapter);金标件大(5.7MB zip/3.7MB tgz),put 通道 base64 慢——下轮分块或走 git 通道;v4 判分脚本=仓内 335b7e63 归档版
- M1:+2(rsi-bench #4=M4 直通车主动
