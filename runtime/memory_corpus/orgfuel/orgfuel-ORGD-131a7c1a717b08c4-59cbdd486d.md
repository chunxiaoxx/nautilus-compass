---
name: orgfuel-ORGD-131a7c1a717b08c4-59cbdd486d
description: "[## ③ 对外文档一致性 · 真实缺口 = 版本 5 套 + 成本/AUC 打架 + 反而低估] - **P0 版本统"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-131a7c1a717b08c4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## ③ 对外文档一致性 · 真实缺口 = 版本 5 套 + 成本/AUC 打架 + 反而低估] - **P0 版本统一到 2.3.0**(单一源 = pyproject):中文 README 徽章 `1.0.0_stable`→`2.3.0`;英文 README "What's new" 头条补 2.2.0/2.3.0;paper/ 安装命令 `==1.0.0/1.1.0`→`==2.3.0`;网页 v0.9.0-dev(网页非 repo 内,另通报)。
- **P1 口径统一**:成本定一个数(注区域差);drift AUC 对外统一标 "0.83 held-out"(0.92 是 in-set,标注清楚)。
- **P1 招牌诚实**:README "activation in progress" 措辞按实测更新为"v2.3.0 已接生产 recall"(**现在是 understate,该上修不是下修**)。
- 风险:低(文档改)。可本 session 做 P0 版本硬伤。⚠️ 甲方保密:不往公开 repo 加 FDE 叙事。
