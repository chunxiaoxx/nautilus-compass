---
name: orgfuel-ORGF-ad6c5e95136156d0-6b6efb7b99
description: "flywheel 档案 dreamdojo-license-review.md # DreamDojo 许可全文评审（A"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-ad6c5e95136156d0
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 dreamdojo-license-review.md
# DreamDojo 许可全文评审（ADR-0006 L0 前置门 · 2026-08-28 凌晨）

来源 pin：https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/
（Version Release Date: 2025-10-24，2026-08-28 全文读回）

## 逐条评审（对 M2B-L0 用途：DreamDojo 2B 权重仅作离线评测器，不分发）

| 条款 | 内容 | 对 L0 的判定 |
|---|---|---|
| 序言 | Models are commercially usable；可自由创建分发 Derivative Models；**NVIDIA 不主张输出所有权** | ✅ 商用可用；**评测读数归本仓**（效用结算产物不被许可污染——关键利好） |
| §2.1 | 绕过安全护栏则许可自动终止；发起专利/版权诉讼则终止 | ✅ 评测用途不触碰 |
| §2.2 | 永久/全球/免版税/可撤销许可，含使用与再分发 | ✅ 内部使用在授予范围 |
| §2.3 | 须遵守 NVIDIA Trustworthy AI 条款 | ✅ 评测用途无冲突 |
| §3 | 再分发须带 Notice+署名；Cosmos 类须标 "Built on NVIDIA Cosmos" | ✅ L0 不分发模型/衍生模型，不触发；若未来 L1 产出衍生模型对外，须补 Notice |
| §5 | 商标仅限描述来源 | ✅ 文档提及 NVIDIA/DreamDojo 属合理描述 |
| §10/§11 | 特拉华法管辖；遵守美国出口管制（EAR/OFAC） 
