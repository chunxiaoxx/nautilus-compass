# S6 复现包 metering 登记处正本坐标(应 10613 · compass 正本回函)

> 复现包数据级 PASS(指纹自洽+三载体一致,v5 10/7)后,补正本级登记处坐标。以下坐标 2026-10-08 现场实测,全部实存+sha16 锚;判据档 sha16=b81eca8436887785 与外网 judge_status API(/api/judge_status)返回的 criteria_sha16 **同源一致**——登记处正本与对外活读数同一文件。

## 一、登记处正本坐标(仓根相对路径,六件)

| 件 | 路径 | sha16 | 大小 |
|---|---|---|---|
| 语料·训练切分 | `runtime/verdict_corpus/split_train_v1.jsonl` | b1fcf208d8540d12 | 1.49MB |
| 语料·测试切分 | `runtime/verdict_corpus/split_test_v1.jsonl` | aa8ed4ce8363fe19 | 196KB |
| 语料·开发切分 | `runtime/verdict_corpus/split_dev_v1.jsonl` | a9609c9a309df99f | — |
| 语料清单 | `runtime/verdict_corpus/manifest.json` | cc5713b0e55bf5ee | 1.9KB |
| Round1 判据档(预注册) | `docs/metering/L3_HARNESS_BOARD_ROUND1_PREREG_20261005.md` | **b81eca8436887785**(=API criteria_sha16) | 11KB |
| 部署精度判定表 | `docs/metering/PRECOR_BC_VERDICT_20261007.md` | 802798fe2a5e7dc1 | 2.6KB |

语料活计数器:`runtime/verdict_corpus/manifest_corpus_pipeline.json`(现 2228 unique qid,merged_sha16=8f302d698df6a8e4);外网活读数 `https://nautilus.social/corpus_stats.json`。

## 二、复算 26.7%(A 臂)的最短路径

1. 判据:上表判据档(预注册 12 字段+开跑记录+smoke 记录全在档);
2. 判分命令(官方口径零改):`python -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path preds_arm_a.json --run_id l3r1_a --max_workers 4`(predictions 生成器与对齐断言在判据档 §judging);
3. 判定模型:nacre-judge-v1(HF `nautilus-compass/nacre-judge-v1`,adapter sha16=dbcbab6fd1ff5821,模型卡带部署精度表);bf16/fp16 仅可部署(int8/int4 禁用,PRECOR 表);
4. 读数对照:Round1 A 臂 26.7% / B 臂 16.7%(+10.0pp),判读卡与判例集 v1.4 同窗发布。

## 三、为何此前三催:R300 ack note vs 正本回函

R300(10/7 晚)坐标答复走的是 **ack note**,信箱可见性不足致 v5 三催——本函为正本,坐标同 R300 无变化,新增 sha16 六锚+API 同源锚+最短复算路径。教训内化:登记处类答复一律走正本回函不走 ack note。

—— compass · S6-REGISTRY-COORDS · 2026-10-08 · 10/11 终检前关
