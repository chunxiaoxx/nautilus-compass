# 数据效用计量报告（样例批次 batch001）

> 协议版本：`utility-metrics-protocol-v1-frozen`（权重 D25%/T40%/C15%/L20%，L 红线一票否决）
> 生成：utility_report_gen.py v0 · 8 条轨迹 · 3984 帧 · 139.4 秒

## 0. 批次结论

- 转换完整性：D2 帧完整率 100.0000%，D3 轨迹完整率 100.00%
- 无效帧占比均值 0.0（黑+冻口径）
- 独一视频 4/8（同源双份独立转换产物哈希一致=4 组转换确定性证据；多样性/一致性计数按独一口径 n=4）
- **U 综合效用：本批不可计**（T 可训性未抽检；协议要求四项齐全方加权）
- 本批性质：管线与格式验证语料，**非付费交付**，不进入数据产品

## 1. 四项指标原始值

### L 合规（阶段 0 状态）

- 状态：阶段 0 未执行：脱敏复检与授权链抽检需采集者授权体系上线后运行；本批为外购池验证语料（commercial-training-no-resale-v1.0），非付费交付，L 红线结算语义不触发
- 原始样本人脸检出（QC 记录，脱敏前）：

| 轨迹 | 人脸帧占比 | 判定 |
|---|---|---|
| s2_body_1 | 0.3684 | WARN |
| s2_body_2 | 0.3684 | WARN |
| s2_head_1 | 0.0 | WARN |
| s2_head_2 | 0.0 | WARN |
| s2_egopro_1 | 0.2037 | WARN |
| s2_egopro_2 | 0.2037 | WARN |
| s2_egosuite_1 | 0.1683 | WARN |
| s2_egosuite_2 | 0.1683 | WARN |

### D 多样性

- 状态：不可计：本批 8 条 tasks.parquet 任务标签为索引（0），无语义枚举；D 需任务包 manifest 冻结清单（协议 §1.1），阶段 0.1 接标签源后可计

### C 一致性

- 时长变异系数 CV：0.639
- 池线集中度：{"body": 0.25, "head": 0.25, "egopro": 0.25, "egosuite": 0.25}（警告=False）
- 不可计分量：跨采集者动作分布KL（本批无同任务多采集者样本）；视角方差（同左）

### T 可训性

- 状态：待抽检（阶段 1，GPU 窗口）
- 口径：固定基座 π0.5+2000 步+LIBERO 10 任务×10 episodes，Δpp=训后−对照，≥20pp 判显著；双种子取低值；阳性对照 62% 校准跑（协议 §1.2）

## 2. 计算过程摘要

- 帧完整率=写入帧/解码源帧；轨迹完整率=rc=0 且 valid_ratio≥0.98 占比；无效帧=黑+冻（糊为软警告不计入本比值，逐条见明细）
- 协议 §1.3 部分口径：仅时长CV+集中度；C 本版无阈值只报数值

## 3. 数据包 sha256 manifest（前 16 位）

| 轨迹 | 主视频 sha256_16 | 视频（批次相对路径） |
|---|---|---|
| s2_body_1 | a2d96674974f01c7 | shard1/s2_body_1/videos/observation.images.cam_left/chunk-000/file-000.mp4 |
| s2_body_2 | a2d96674974f01c7 | shard1/s2_body_2/videos/observation.images.cam_left/chunk-000/file-000.mp4 |
| s2_head_1 | 4a28a276053e7840 | shard2/s2_head_1/videos/observation.images.cam_left/chunk-000/file-000.mp4 |
| s2_head_2 | 4a28a276053e7840 | shard2/s2_head_2/videos/observation.images.cam_left/chunk-000/file-000.mp4 |
| s2_egopro_1 | 5a37bacebae3be06 | shard3/s2_egopro_1/videos/observation.images.cam_left/chunk-000/file-000.mp4 |
| s2_egopro_2 | 5a37bacebae3be06 | shard3/s2_egopro_2/videos/observation.images.cam_left/chunk-000/file-000.mp4 |
| s2_egosuite_1 | a65ec2503f289bee | shard4/s2_egosuite_1/videos/observation.images.cam_left/chunk-000/file-000.mp4 |
| s2_egosuite_2 | a65ec2503f289bee | shard4/s2_egosuite_2/videos/observation.images.cam_left/chunk-000/file-000.mp4 |

## 4. 复现实验日志哈希

| 文件 | sha256_16 |
|---|---|
| worker1.log | 6b2724bff70d5622 |
| worker2.log | 7529d5ac3a7afeaa |
| worker3.log | f542e74ba13ccb04 |
| worker4.log | a6cc7385895b1dc1 |
| resource_log.csv | 1f9ce5cd319db717 |

## 5. 局限性声明

1. T 指标未执行：本批无 GPU 抽检读数，U 不可计（协议 §1.2 待阶段 1）；
2. L 抽检未执行：授权链与脱敏复检依赖采集者体系上线（协议 §1.4）；
3. D 不可计：任务标签无语义枚举（协议 §1.1 需 manifest 冻结清单）；
4. C 仅时长分量：无同任务多采集者样本，KL/视角方差不可计；
5. 样本量 n=8（外购池四线各 2 条，其中含同源副本，独一口径 n=4），批次统计不外推产能或合格率分布；
6. 本批数据来源 LightwheelAI 外购池，许可 commercial-training-no-resale-v1.0，禁转卖、不入数据产品（SOURCE_REGISTER EgoSuite-Open100K 行）。

## 6. 独立读回指引

```bash
# 复算本报告（Windows / Py3.13，依赖 lerobot 环境同转换器）
python scripts/utility_report_gen.py \
  --batch-dir <本批目录> --out <任意输出.md> --json <任意输出.json>
# 对比 payload JSON 中 per-episode 读数与本报告表值；
# QC 单条可独立复算：from qc_pipeline import run_qc; run_qc(<视频绝对路径>)
```

## 附：逐条明细

| 轨迹 | 池线 | 帧 | 解码帧 | valid | 时长s | fps | 元数据齐 | 备注 |
|---|---|---|---|---|---|---|---|---|
| s2_body_1 | body | 190 | 190 | 1.0 | 6.33 | 30.0 | True | — |
| s2_body_2 | body | 190 | 190 | 1.0 | 6.33 | 30.0 | True | — |
| s2_head_1 | head | 496 | 496 | 1.0 | 19.84 | 30.0 | True | — |
| s2_head_2 | head | 496 | 496 | 1.0 | 19.84 | 30.0 | True | — |
| s2_egopro_1 | egopro | 268 | 268 | 1.0 | 8.93 | 30.0 | True | — |
| s2_egopro_2 | egopro | 268 | 268 | 1.0 | 8.93 | 30.0 | True | — |
| s2_egosuite_1 | egosuite | 1038 | 1038 | 1.0 | 34.60 | 30.0 | True | — |
| s2_egosuite_2 | egosuite | 1038 | 1038 | 1.0 | 34.60 | 30.0 | True | — |
