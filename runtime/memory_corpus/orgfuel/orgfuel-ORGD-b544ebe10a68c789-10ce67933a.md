---
name: orgfuel-ORGD-b544ebe10a68c789-10ce67933a
description: "[## 三、原生记忆:"记忆效用信号→训练燃料"(双层打通的具体协议)] - **创新机制**:记忆层(M5 后)每条记"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-b544ebe10a68c789
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 三、原生记忆:"记忆效用信号→训练燃料"(双层打通的具体协议)] - **创新机制**:记忆层(M5 后)每条记忆带**效用遥测**(被检索→被引用→任务成败),高效用记忆自动**晋升为 delta 训练条目**进 registry;低效用自动衰减。记忆不再只是"可查",而是"可转化为权重"的活数据。
- **为什么是我们**:效用信号的可信判定需要验证内核(任务成败=可复算判定);mem0/MemRL 类无此闭环。
- **实验设计(E-NACRE-3)**:M5 部署后跑 2 周,取效用 top-10% 记忆构造训练条目(经三态判读验证),混入 P3(按回放配方 10-15%);对比混入前后 judge 在记忆密集型 qid 上的 acc。
