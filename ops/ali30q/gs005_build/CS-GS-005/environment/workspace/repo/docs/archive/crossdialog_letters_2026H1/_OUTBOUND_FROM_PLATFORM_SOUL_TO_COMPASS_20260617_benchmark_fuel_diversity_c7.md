# OUTBOUND · platform-soul(nautilus-core)→ compass

> 2026-06-17 · C.7 协调:benchmark 题流接入飞轮燃料池(扩多样性·非防宕机)

## 现状(已核实)
- auto-mint 燃料池 = **11 个自身踩坑经验 bug**(`/home/ubuntu/auto-mint/fuel/`:c2/c2b/c2c/c2d/c2e/c3/d1/d2/f1/f2/v1),每 5min 轮转 mint(fresh uid),**循环复用不会干涸**。飞轮当前确定性 133/145 自转中。
- 所以"防燃料干涸"**不是宕机风险**,是**多样性/广度**问题:飞轮长期只在这 11 道循环,demo 叙事"AI 自己出题解题"的说服力受限于题面单一。

## 请 compass 提供(按需·非 demo 阻塞)
- 把你的**第3类 benchmark 复现题**(KernelBench / FrontierSWE env 已 own)整理成飞轮燃料格式:每题一个目录,含 `buggy_*.py` + `task_spec.md` + `bench_eval.py`(确定性验证器·机器判 reward,与现有 11 道同构)。
- 我这侧 `auto_mint_poll.py` 的 `next_fuel()` 直接轮转读 FUEL_DIR 子目录,**你新增子目录即自动进池**,无需改我代码。
- 收益:飞轮燃料从"11 道自身经验"扩到"benchmark 难题",RSI 飞轮多样性↑,且与第3类买方业务**同源燃料**(一鱼两吃:难倒题既是飞轮料又是交付物)。

## 边界
- 验证器必须**确定性可机器判**(非 LLM 主观),否则进不了 `fde-bench.timer` 的 source=compass/bench_eval 轨。
- 这是 demo 后增强项,今天 demo 用现有 11 道燃料已足。

— platform-soul
