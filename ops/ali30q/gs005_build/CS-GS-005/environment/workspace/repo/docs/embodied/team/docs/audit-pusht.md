# 首份真实数据审计报告 · lerobot/pusht(LeRobotDataset v3.0)

> 审计器:qc_judge v0(7 规则,确定性可复现)· 数据:HuggingFace `lerobot/pusht` (codebase v3.0,fps 10,206 episodes / 25650 帧)· 2026-07-17

## 头条发现:成功判据口径决定一切

- **口径 A(数据集官方判据:覆盖率 ≥0.95)= 0/206 条成功**。206 条人类演示最好只到 0.94 —— 按「成功才结算」口径,这个知名公开数据集**一分钱都结不了**。
- **口径 B(商业交付口径:覆盖率 ≥0.9)= 92/206 条达标**。
- 这不是数据集烂,是**判据没写清就会颗粒无收** —— 正是行业验收纠纷("谁来判断,谁来承担成本?")的定量演示;合同必须写分级判据。

## 总判定(口径 B)

| 指标 | 值 |
|---|---|
| episodes 审计 | 206 |
| **合格(可结算)** | **91(44.2%)** |
| 判废/扣分未过线 | 115(55.8%) |
| 任务达标(覆盖率≥0.9) | 92 |
| 任务未达标 | 114 |

## 各规则命中(废品归因)

| 规则 | 命中次数 |
|---|---|
| R5_success_label | 114 |
| R4_smoothness | 22 |

## 最差 10 条(废品清单样例,每条附证据)

### ep_000000 · score=0 · 判废/不合格
- [critical] R5_success_label: 任务标注为失败(按需求方 spec 可转入失败样本池,不计合格小时) · evidence={}

### ep_000003 · score=0 · 判废/不合格
- [critical] R4_smoothness: jerk 峰值 33640.3 > 判废阈 33500.0(动作变形/抖动) · evidence={'max_jerk': 33640.28137058939}

### ep_000006 · score=0 · 判废/不合格
- [critical] R5_success_label: 任务标注为失败(按需求方 spec 可转入失败样本池,不计合格小时) · evidence={}

### ep_000007 · score=0 · 判废/不合格
- [critical] R5_success_label: 任务标注为失败(按需求方 spec 可转入失败样本池,不计合格小时) · evidence={}

### ep_000008 · score=0 · 判废/不合格
- [critical] R5_success_label: 任务标注为失败(按需求方 spec 可转入失败样本池,不计合格小时) · evidence={}

### ep_000012 · score=0 · 判废/不合格
- [critical] R5_success_label: 任务标注为失败(按需求方 spec 可转入失败样本池,不计合格小时) · evidence={}

### ep_000014 · score=0 · 判废/不合格
- [critical] R5_success_label: 任务标注为失败(按需求方 spec 可转入失败样本池,不计合格小时) · evidence={}

### ep_000015 · score=0 · 判废/不合格
- [warning] R4_smoothness: jerk 峰值 24519.0 > 告警阈 17600.0 · evidence={'max_jerk': 24519.02432236931}
- [critical] R5_success_label: 任务标注为失败(按需求方 spec 可转入失败样本池,不计合格小时) · evidence={}

### ep_000016 · score=0 · 判废/不合格
- [critical] R5_success_label: 任务标注为失败(按需求方 spec 可转入失败样本池,不计合格小时) · evidence={}

### ep_000017 · score=0 · 判废/不合格
- [critical] R5_success_label: 任务标注为失败(按需求方 spec 可转入失败样本池,不计合格小时) · evidence={}

## 阈值校准与诚实声明

- 平滑度阈值 = **分布校准法**(ICLR 2025「过滤最差 10-20% demo 反而提升策略性能」的操作化):warn = 全集 p90(17600 px/s³,最差 10% 标复核)、critical = p99(33500 px/s³,最差 1% 判废)。首轮曾用弧度口径硬套像素空间导致 90% 误报,已按 confound-check 纪律证伪并校准。
- pusht 状态为 512px 平面坐标(非弧度);stall 按 10fps 折算 3s。
- 数据集无夹爪通道:R7(夹爪活动)已关闭并注明,不计入判定。
- 成功判据双口径并报(A=官方 0.95 / B=商业 0.9),判据本身即审计对象。
- 判定确定性:同输入同输出,本报告可由任何人复跑核验(`python scripts/audit_pusht.py`)。
- 本报告为审计器在公开数据上的能力演示;真实交付会按客户 spec 重校阈值并加双人抽检(κ≥0.8)。
