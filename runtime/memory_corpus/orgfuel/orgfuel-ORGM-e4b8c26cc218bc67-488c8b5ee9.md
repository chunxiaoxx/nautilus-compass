---
name: orgfuel-ORGM-e4b8c26cc218bc67-488c8b5ee9
description: "记忆条目 day-log-20261008-corpus-finalcheck.md 2026-10-08 compas"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-e4b8c26cc218bc67
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 day-log-20261008-corpus-finalcheck.md
2026-10-08 compass 主件制 loop 11 轮(R345-R355)+HANDOFF 追加(R356),全闭环:

**主数据**:语料 1846→2257(docs 源重提取 +382 / delta_0004 回填 13 案 / 判例集 v1.4 入池 16 案),7B 目标 3000 差 743;终检 10/11 清单清零(final_check.py 三口径首跑 11/11);S6 登记处正本回函闭环(判据档 sha16=b81eca8436887785 与外网 API criteria_sha16 同源)。

**Why**: 两条当天实测教训具跨项目通用性:
1. **nohup 假绿 flag**:A100 判分 rerun 用裸 `python` 启动,非登录 shell 无 conda 别名 → 命令不存在 → 但链尾 `echo DONE > flag` 照写 → 表面完成实际零执行。教训:**后台任务的完成标志必须从产出物验证(日志内容/GPU/行数),flag 本身是自报**;远程 python 一律绝对路径(/root/venv/bin/python)。
2. **ack note 可见性不足**:S6 坐标答复走 ack note,对方三催未见 → 登记处/坐标类答复一律走正本回函(platform_mail.py send)。

**How to apply**: 远程执行前先 `which python` 或用绝对路径;后台任务验收看产出物非标志位;平台信箱重要答复 send 不 ack。关联 [[sec-incident-a100-pw-20261008]] [[mainline-anchor-20261008]]。
