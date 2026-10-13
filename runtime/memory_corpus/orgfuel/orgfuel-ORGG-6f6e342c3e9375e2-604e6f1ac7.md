---
name: orgfuel-ORGG-6f6e342c3e9375e2-604e6f1ac7
description: "判读档判例 EMB_BAKEOFF_PREREG_20261009 · 评测结果 V1(2026-10-09 · R40"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-6f6e342c3e9375e2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 EMB_BAKEOFF_PREREG_20261009 · 评测结果 V1(2026-10-09 · R401-R402 执行 · A100 fp16 · 三池化官方用法)
## 评测结果 V1(2026-10-09 · R401-R402 执行 · A100 fp16 · 三池化官方用法)

| 模型 | Set A_all R@1/R@5/MRR (n=30) | Set C_live R@1 (n=3) | 载入 |
|---|---|---|---|
| **bge-m3(现役锚)** | **0.9667 / 1.0000 / 0.9833** | **0.6667** | 4.5s(本地) |
| Qwen3-Emb-0.6B | 0.4667 / 0.5333 / 0.5152 | 0.0000 | 293s(hub) |
| Qwen3-Emb-4B | 评测中 | — | — |

- **换模型门判定:0.6B 惨败(-50pp,门要求 +2.0pp)→ 一票否决,bge-m3 留任**。9/25 对拍结论二次独立验证(GPU+官方用法+指令前缀全给足仍未敌)。
- **如实披露**:①Set B 中文切片 n=1(cjk>0.5 过滤在混排语料上几乎全灭)——该门无统计力,判读以 A_all/C_live 为主;②Set A+ 情境改写查询已生成(30/30,质量高)但未及接入 eval 硬编码套件——4B 结果后补跑 A+ 套件;③A_plus 样例质量佐证 Set A+ 价值:"这轮用户的实质诉求推进了吗"(真实教训的完美情境改写)。
