# 8B 对拍训练配置预注册档(2026-10-10 · R471 · 判据档 SEVENB_COMPARE_PREREG 触发序列第 3 步前置)

> 定位:语料触发(≥3000)日**零现场**——训练配置今天落档,触发日只跑命令。判据本体以 SEVENB_COMPARE_PREREG(冻结)为准,本档只落执行配置。

## 一、脚本基座与适配点

- 基座:`runtime/loop/_r177_l3smoke/_train_judge14b_upgrade_A100.py`(14B QLoRA 版,同构迁移);
- **适配点 1·基模**:`BASE=/root/vdf/models/Qwen3-8B`(8B bf16 全精度基座——**不用 4bit**:8B bf16≈16GB,A100 40G 装 LoRA 训练充裕,且符合 PRECOR 部署精度纪律 bf16/fp16 only——比 14B 时代的 4bit 妥协更干净);
- **适配点 2·判定阈值对齐**:脚本常数 `U6_MARGIN = 0.03`(10/5)与判据档 G1 `+2.0pp`(10/8 冻结)不一致——**触发日以判据档 G1=0.02 为准**,脚本常数改为 0.02(对齐冻结判据,防执行时用错尺子);
- 其余超参沿用现役 recipe:LoRA r16/α32/dropout 0.05/AdamW 1e-4/3 epoch(MAX_STEPS 2000 cap)/SEED 20261005。

## 二、数据管线(判据档口径)

- 训练池=触发日全量合并池(corpus_pipeline manifest sha 记档);held-out 抽 300 案(qid 防泄漏,交集审计一行落 report);
- 对照=现役 1.7B champion(sha16 dbcbab6fd1ff5821)同集对拍。

## 三、触发日执行序列(零现场清单)

1. `python tools/corpus_pipeline.py` 读数 ≥3000 → manifest sha 记档;
2. 切分 held-out 300(qid 审计);
3. 脚本参数化执行(基模/阈值按本档)→ adapter 落盘;
4. 四门评测(G1 主门/G2 三门/G3 精度/G4 披露)→ 判定表;
5. 升格或负结果归因(数据量/配方/切分),非实现者复算坐标随卡发布。

## 四、证据层

- 脚本结构/超参:[实测](源码直读);
- 8B bf16 显存可行性:[推断](权重 16GB+LoRA 梯度小,A100 40G 充裕;upgrade_path=触发日 smoke 先行);
- 阈值不一致:两档原文对照 [实测]。

—— compass · 8B-TRAIN-CONFIG · R471 · 2026-10-10
