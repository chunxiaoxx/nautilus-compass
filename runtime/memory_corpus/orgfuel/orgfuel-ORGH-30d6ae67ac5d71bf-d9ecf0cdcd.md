---
name: orgfuel-ORGH-30d6ae67ac5d71bf-d9ecf0cdcd
description: "工具决策记录 org_fuel_harvest.py ORG-FUEL 判分收割段(2026-10-08 语料冲刺):A"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-30d6ae67ac5d71bf
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 org_fuel_harvest.py
ORG-FUEL 判分收割段(2026-10-08 语料冲刺):A100 verdicts → 本地 → 管道重跑 → 站点语料数刷新。

用法:
  set -a; source ~/.claude/.cache/a100_env; set +a
  python tools/org_fuel_harvest.py          # 拉取+本地管道+刷新 corpus_stats
  python tools/org_fuel_harvest.py --check  # 只查远端进度(不写任何文件)

A100 环境锚:判分脚本必须用 /root/venv/bin/python 绝对路径启动
(nohup 非登录 shell 无 conda/python 别名,2026-10-08 rerun 空转教训)。
