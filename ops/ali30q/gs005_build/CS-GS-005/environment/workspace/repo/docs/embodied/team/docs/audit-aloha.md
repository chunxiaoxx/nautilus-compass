# 审计报告 · aloha_static_coffee(LeRobotDataset v3.0)

> qc_judge v0 · fps 50 · 50 episodes / 55000 帧 · 夹爪通道:第 -1 维 · 2026-07-17

## 双口径判定

| 口径 | 合格(可结算) | 说明 |
|---|---|---|
| A · 严格结算口径(须成败标签为真) | **0/50(0.0%)** | 有成败标签的 episodes:0/50 |
| B · 质量口径(七维规则,不看标签) | **49/50(98.0%)** | 时长/丢帧/停滞/平滑/越限/夹爪 |

**头条发现:该数据集没有任何 episode 级成败标注**(无 next.success 类字段)——按「成功才结算」的合同口径,这批数据一条都结不了账。真机公开数据集普遍缺验收基础设施,再添一证。

## 质量口径规则命中

| 规则 | 命中 |
|---|---|
| R4_smoothness | 5 |

## 最差 5 条(质量口径)

- **ep_000029** score=0 不合格:[critical]R4_smoothness
- **ep_000000** score=90 合格:[warning]R4_smoothness
- **ep_000019** score=90 合格:[warning]R4_smoothness
- **ep_000026** score=90 合格:[warning]R4_smoothness
- **ep_000034** score=90 合格:[warning]R4_smoothness

## 校准与诚实声明

- 平滑度阈值分布校准:warn=p90(4823.4)、critical=p99(5320.6),单位随数据集(本集为弧度制真机数据则为 rad/s³)。
- 时长/停滞按 3 秒 × 50fps 折算;jerk 中位数 4055.4。
- 判定确定性:同输入同输出,可复跑核验。
