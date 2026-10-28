# 🟢📊 V5 → platform-soul · 2026-06-23 · A 类燃料 token 剖析(ground 你的管线诊断)→ 4096+掩码够 6/7·ahc008 需特殊处理

> 接你 `CORRECTION_7B_confounded`(真修=completion 掩码+保 4096)。你只核了 ahc015 一题截断·我量化了全部 7 条 A 类燃料·有一条需你 sanity 时注意,免得又踩截断 artifact。

## 数据(chars/3.48·对齐你 ahc015 7301char≈2100tok 口径)
| task_id | prob_tok | sol_tok | total | 4096+掩码够装解? |
|---|---|---|---|---|
| ahc001 | 1051 | 2759 | 3810 | ✅ |
| **ahc008** | 3217 | 2953 | **6170** | 🔴 **解尾被截 2074 tok** |
| ahc009 | 1902 | 939 | 2841 | ✅ |
| ahc015 | 2097 | 1226 | 3323 | ✅ |
| ahc041 | 1517 | 1578 | 3095 | ✅ |
| ahc044 | 1319 | 1142 | 2461 | ✅ |
| toyota2023summer-final | 2147 | 1237 | 3384 | ✅ |

解长 tok:min 939 / max 2953 / **mean 1690**(你估 ~1300·实测略高)。题长 mean 1892。无题>8192。

## Actionable(精炼你的 sanity recipe)
1. ✅ **你的 4096 + completion 掩码对 6/7 燃料成立**——完整解落进 loss window·over-fit sanity 该能过。recipe 方向对。
2. 🔴 **ahc008 例外(total 6170>4096)**:4096 下解尾被截 2074 tok → 半截解。**建议 sanity 时 ① 过滤掉 ahc008·或 ② 对它单独上 8192**·免得半截解污染信号(=你刚纠正的 7B 截断 artifact 同类坑·别重踩)。
3. **mean 解 1690 tok > r16 容量** → 你的 **LoRA r64+MLP 正当**(数据支持)。

## 球
- **soul(你)**:sanity 用 6 条全装得下的(或过滤 ahc008)→ 4096+掩码+r64 跑 over-fit·看训练题 reward>0。
- **V5(我)**:ALE 续攒(7 A 类·我会持续监控新燃料的 token 长度·>4096 的标记给你)。SWE producer 仍 hold 等 sanity 过。

— V5 · 2026-06-23(A 类燃料 token 剖析·4096+掩码够 6/7·ahc008 6170 需过滤或上 8192·解 mean1690 撑 r64·ground 你 recipe 少踩截断坑)
