---
name: orgfuel-ORGH-cd6c19a88213ed91-496faadbe9
description: "工具决策记录 p3_promote.py P3 S5 · 冠军上岗切换器(原子写+三代回滚+kill switch,纯 "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-cd6c19a88213ed91
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 p3_promote.py
P3 S5 · 冠军上岗切换器(原子写+三代回滚+kill switch,纯 CPU)。

设计档 §六:
  champion.json 原子切换(tmp 写+os.replace):{gen, adapter_path, adapter_sha16,
  gate_report_sha16, corpus_delta_sha16, promoted_at}
  回滚:champion_history.json 保留最近 3 代;kill switch=--rollback 指回上一代
  硬约束(§八·5):上岗只走本管道,任何人不手动替换 champion 而不过门。

前置校验(防偷渡):
  ①gate_report.verdict==PASS;②gate_report_sha16 与报告文件实算一致(防改判后复用);
  ③challenger adapter 目录存在且含 adapter_model.safetensors。

用法:
  python tools/p3_promote.py --init                     # 首跑:gen0=P2v2 冠军入账
  python tools/p3_promote.py --gate GATE.json --adapter DIR --ticket T.json --record
  python tools/p3_promote.py --rollback --record        # kill switch
  python tools/p3_promote.py --show
