# G4《Verification as Protocol》P2 终核清单(2026-09-28 · 投稿前最后一关)

> 方法:文章 77 条数字行→35 条硬声明,逐条对工件 grep 复核。
> 结论:**34 PASS / 1 修正(已改)**——文章达到投稿口径。

## 对账表(声明 → 工件锚 → 判)

### BC1 域(15 条,全 PASS)
| 声明 | 工件 | 判 |
|---|---|---|
| 30 题/130 天 | BC1_LAUNCH | ✓ |
| 首考 11/18 | SCORECARD_V2 | ✓ |
| 7 失败=2 真值+3 歧义+2 边界 | SCORECARD_V2(T12×2/T11×3/T31×2) | ✓ |
| 三臂 16/11/18 | BC1_LAUNCH 三臂段 | ✓ |
| mem0 2.2.0/MiniMax-M3 | BC1_LAUNCH | ✓ |
| 压缩丢 7 分 | 18−11 | ✓ |
| artifact: null 字段 | BC1_LAUNCH 机制段 | ✓ |
| DIM3 4/4→1/4 | BC1_LAUNCH | ✓ |
| raw 69/62 vs 报 71/67 | SCORECARD_V2 复算段 | ✓ |
| v2 18/18/5 缺陷/7 转 PASS/零新错 | SCORECARD_V2 | ✓ |
| sha256=3b9def7d | BC1_LAUNCH+发布页 | ✓ |
| 四维 7/8/7/8 | 轮2 记账(DIM1-4) | ✓ |
| public 18/holdout 12 | BC1_LAUNCH | ✓ |
| 90 天挑战窗 | BC1_LAUNCH §5b | ✓ |
| ed25519 签名 | SCORECARD_V2 签名记录 | ✓ |

### TypeSafe 域(9 条,8 PASS+1 修正)
| 声明 | 工件 | 判 |
|---|---|---|
| 193.6x/444.6x 宣称 | typesafe_home.html 快照 | ✓ |
| 440.1x(vs opus5)/183.8x(vs sonnet5) | RECOMPUTE_SCOPE 口径节 | ✓ |
| **64 timed calls** | 逐轮原始 JSON 重数 | **✗→已修:90 调用/82 成功/8 失败** |
| Jev 0.44-0.48s 恒定 | bench_multi/v2(中位 0.44-0.48) | ✓ |
| MiniMax 3.7-8.0s | bench_v2 A=3.69~multi=8.03 | ✓ |
| 比值 7.9-18.2x | RECOMPUTE_SCOPE 三轮 | ✓ |
| 69 vs 406 output tokens | bench_b_results | ✓ |
| PARTIAL 判定 | RECOMPUTE_SCOPE 终判 | ✓ |
| 准确率同档不占优 | evals_extract.json | ✓ |

### τ-bench 域(3 条,全 PASS)
29 失败/16 值级(4 支付)/7 漏多——LOOP_STATE 轮30 ✓;5 题被复核推翻=结果传达失败——轮31 ✓;两道判定门(终态 hash+outputs 串)——轮31 ✓

### 其他(8 条,全 PASS)
T32-0 样题 4 行+时间戳 ✓(exam_paper_v2.json 原文)·伊洛科技有限公司✓ ·repo URL ✓ ·"September 2026"竞品核验 ✓ ·判据三态/判分器公开/挑战窗表述 ✓ ·n=1 与利益冲突披露(自审档)✓ ·考题实物与考卷一致 ✓ ·运营方披露句 ✓

## 修正记录(本轮 1 处)

- 「64 timed calls」→「90 timed calls, 82 successful (8 supplier-quota failures
  excluded)」:逐轮重数(10+48+32=90,成功 82)推翻轮次汇报速记。
  文章已改;**已发背书信在帖下补更正评论**(msgId 1554120528833413201)——
  验证机构先抓自己的错,与文章主题自洽。
- 教训入 RECOMPUTE_SCOPE:累计数必须逐轮从原始 JSON 重数。

## 终核结论

**投稿就绪**。剩余:投稿信(guest post pitch)→ Latent Space 提交。
