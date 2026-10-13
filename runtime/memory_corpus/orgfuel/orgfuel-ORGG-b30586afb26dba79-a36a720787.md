---
name: orgfuel-ORGG-b30586afb26dba79-a36a720787
description: "判读档判例 2026-06-06-compass-cloud-substrate-design · 1. 架构裁定:云权"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-b30586afb26dba79
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-06-compass-cloud-substrate-design · 1. 架构裁定:云权威 + 瘦客户端(A 起步 → C 演进)
## 1. 架构裁定:云权威 + 瘦客户端(A 起步 → C 演进)

放弃"双向文件同步"(B · 类比比特币分布式账本 · 需冲突共识 · 记忆不需拜占庭容错 = 杀鸡用牛刀 · 踩 anchor #3 D 维护)。

**A(起步)**:云跑权威 daemon,所有读写打云。**"双向同步"被溶解为单写权威** —— 一条 ingest 路径写同一份云语料 = **零冲突**,这就是绕开同步地雷的本质。
**C(演进)**:本地加**只读副本**(单向从云拉)供离线 recall + 提速 · 写仍去云 · 仍零冲突。
