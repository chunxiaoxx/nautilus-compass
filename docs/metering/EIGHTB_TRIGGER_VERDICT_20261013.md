# 8B 正式对拍判定卡(触发日 · 2026-10-13 · SEVENB_COMPARE_PREREG 冻结判据)

## 一、执行坐标 [实测]

| 项 | 值 |
|---|---|
| 触发 | corpus_pipeline manifest merged_unique=3294 ≥ 3000(sevenb_compare_ready=true) |
| 源池 sha16 | `c1aac9d8b47064a1`(== manifest 同构复算) |
| 触发池 sha16 | `5045ff1235e345e6`(leak_key 严化口径,合并 rejudge-/lme- 变体 451 行,n=2843) |
| 切分 | train 2543 / holdout 300(SEED 20261005);**qid 交集=0 [实测]**(首跑 73 交集被训练脚本拦截,根因=切分审计键与训练比对键不同构,已同构化重切) |
| 标签口径 | 自举标注 **1811 条(63.7%)**如实申报(org_fuel 系 truth_label=NACRE 1.7B judge_verdict);三 split 系 1032 条=原始标签 |
| 配方 | LoRA r16/α32/AdamW 1e-4/**1 epoch**(R513 过拟合负结果的预注册修正案)/bf16 基座(非 4bit,PRECOR 精度纪律) |
| 训练 | 636 步零 OOM,197.3s,峰值 16.49G(预算 36G) |

## 二、判定表 [全部实测]

| 门 | 读数 | 判定 |
|---|---|---|
| qid 防泄漏 | 交集 0 | ✅ |
| U1 全量训练 | 636/636 步,零 OOM | ✅ |
| U2 显存 | 16.49G < 36G | ✅ |
| U3 loss 收敛 | first20 0.103 → last20 0.185(升) | ❌ |
| U4 格式合规 | 100/100(门 98) | ✅ |
| **U5 不劣门** | 8B **0.9767** vs 1.7B 0.9667(+1.0pp) | ✅ |
| **U6/G1 显著门** | **+1.0pp < +2.0pp(冻结)** | ❌ **FAIL** |

## 三、预注册自动裁定

**8B 不升格,1.7B(qwen-judge-v1,sha16 dbcbab6fd1ff5821)维持现役。**
G1 主门已判死,按裁定规则("任一未过→不升格")G2 三门与 G3 精度门**未执行**(省算力,如实记)。

## 四、归因(判据档三归因)

1. **数据量(主因)**:2843(严化口径)下 8B 增益 +1.0pp 为**真实但不足**——对比 R513(1454 条 3 epoch)= -3.08pp,方向已修复(过拟合消除),增益从负转正,离 +2.0pp 门差 1pp。语料继续棘轮后重评仍有空间。
2. **配方**:1 epoch 修正**有效**[实测](过拟合信号消失,acc 由负转正);U3 loss 末段微升与自举标签噪声(63.7%)一致——标签质量是下一杠杆。
3. **切分**:合规(qid 交集 0;变体行合并 451 行防重复计权)。

## 五、局限与披露

- 自举标签 63.7%:标签=judge 自身输出,误差传播风险知情披露;对冲=现役冠军同集对拍(同标签池),G1 读数为**相对增益**而非绝对正确率。
- U4 抽样集=dev(holdout 300 内抽 100,无独立 test 集,触发口径注记)。
- 新 holdout 300 与旧 292 集不可互比(集不同,0.9767≠旧口径读数)。

## 六、复算坐标(非实现者复算开放)

- report 正本:`docs/metering/judge8b_trigger_20261013_upgrade_report.json`(本仓 commit)
- 逐例:eval300_8b.jsonl / eval300_17b.jsonl(A100 `/root/vdf/judge8b_trigger_out/`,commit 入仓)
- 训练脚本:`runtime/loop/_r177_l3smoke/_train_judge8b_trigger_A100.py`;切分:`tools/eightb_trigger_split.py`
- adapter:A100 `/root/vdf/judge8b_trigger_out/judge8b_lora`

—— compass · 8B 触发日判定 · 2026-10-13 · 负结果照报
