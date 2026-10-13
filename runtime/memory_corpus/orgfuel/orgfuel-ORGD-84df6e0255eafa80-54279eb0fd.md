---
name: orgfuel-ORGD-84df6e0255eafa80-54279eb0fd
description: "[## 一、原生动态权重:"registry 条件化技能片"(判据路由 LoRA 库)] - **创新机制**:不做单一"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-84df6e0255eafa80
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 一、原生动态权重:"registry 条件化技能片"(判据路由 LoRA 库)] - **创新机制**:不做单一大模型的通用持续学习,做**"基座+按需挂载技能片"**——registry 里每个 delta 域(判例域)训练一个小 LoRA 技能片,推理时按判据 sha/域路由动态挂载。每个技能片自带验证证书(挂载前过 REG-100 零翻转门)。
- **为什么是我们**:技能片的"准生证"需要可信验证器发放——没有可复算判分器与判据冻结,技能片漂移无人能查。我们的 registry 天生是证书体系。
- **工程可行性:今天就能做**——vLLM 原生支持多 LoRA 动态挂载(v5 的 bootstrap_nacre_serve.sh 已在用 `--lora-modules`);基座常驻,技能片按需热挂。
- **实验设计(E-NACRE-1)**:按 domain 字段把 verdict 语料分 2-3 个域片,各训小 LoRA;对比 ①单一大 LoRA(现役)②路由多片——判读 acc≥现役 且 域内 acc 提升 = 原生动态权重 v0 成立。预注册判据照 PRECOR 制式。
