---
name: orgfuel-ORGD-72abb64f9bb39870-4b9513108f
description: "[## 4. 设计要点] - **双臂**:A 臂=带 compass 记忆栈(recall+session 节点+dr"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-72abb64f9bb39870
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 4. 设计要点] - **双臂**:A 臂=带 compass 记忆栈(recall+session 节点+drift 锚);B 臂=每 session 冷启动。同一 agent 镜像,顺序平衡(借栖达交叉设计)。
- **计量单位**:"agent×session 对",非 agent 个体(agent 数太少;同栖达 n=20 只作方向判断纪律)。
- **揭盲与评判**:compass 小判分器(verdict)读 session 记录判"接续成功/失败"——方法论同构:判据预注册+可复算。
- **数据源**:compass daemon 记忆库+session jsonl+drift_check 历史,全本地,复算脚本比照 scripts/qida-validation-measure.ts。
- **防污染**:评"自发引用"时,引用须出现在用户提示之前;用户提醒后的引用不计(同栖达"每日访谈禁'记'字"红线精神)。
