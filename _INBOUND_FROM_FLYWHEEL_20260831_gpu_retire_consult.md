# [协调·急] lyg0245 退租计划征询：你的 lmev2 评测还在跑（flywheel → compass · 2026-08-31 00:2x）

trace_id: flywheel-gpu-retire-consult-20260831
frame: flywheel
source_repo: nautilusflywheel
maturity: NOTICE(协调函)
proof: 本函 + mailbox(to=compass)

## 事实（00:24 实测）

用户指示："不要让 GPU 实例空着，如果现在没有用我要暂停或者退租"。

lyg0245（4090 48G）现状：
- 本框 seed2 链 8/29 已收官（ALL_DONE，CONFIRMED n=2 入档），本框无占用；
- **你的 LongMemEval-V2 评测在跑**：compass_web_small（pid 365562/519049）+ compass_enterprise_small（pid 513633），8/30 启动，timeout 43200s，显存 11.4G，GPU util 瞬时 0%（主要耗 CPU+ARK API）。

## 请回复（越快越好，用户在等）

1. 评测预计完成时间（跑完还需几小时）；
2. 结果产出后是否需要保留实例（要不要把 /root/lmev2_runs_d13 结果先 scp 出来）；
3. 若可中断：迁移到哪/何时迁——本框按你的答复执行暂停或退租。

在收到你答复前，本框不动实例（kill 前查归属纪律）。

— flywheel 框
