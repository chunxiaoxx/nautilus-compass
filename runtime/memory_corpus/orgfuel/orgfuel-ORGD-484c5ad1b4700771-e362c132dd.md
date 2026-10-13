---
name: orgfuel-ORGD-484c5ad1b4700771-e362c132dd
description: "[## 三、Terminal-Bench] - **上游正本**:GitHub laude-institute/term"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-484c5ad1b4700771
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 三、Terminal-Bench] - **上游正本**:GitHub laude-institute/terminal-bench(repo id 918420677 实测);任务集+官方 harness(terminal-bench CLI)+每任务官方 verifier;任务集持续扩张,版本敏感。
- **criteria_version v1 冻结口径**:主指标=**task resolve rate**(官方 verifier 判过);harness=官方 CLI 钉 release tag;**任务集钉 dataset 版本 tag**(成绩行必示 tag,防跨版本不可比);单 run 起步,agent 配置(模型/工具)全披露。
- **污染风险与对策**:①任务公开可被训练——对策:cutoff 晚于任务集 tag 发布者标"泄漏风险"进观察区;②verifier 版本漂移——对策:verifier 随 dataset tag 冻结,tag 升级=旧成绩转观察区;③环境侧信道——对策:容器镜像 digest 随行。
- **U 态条款**:任务集大版本迁移未复跑=转观察区。
