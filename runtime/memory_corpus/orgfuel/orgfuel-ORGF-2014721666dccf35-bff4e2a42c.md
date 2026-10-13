---
name: orgfuel-ORGF-2014721666dccf35-bff4e2a42c
description: "flywheel 档案 2026-08-11-ego-datalift-m1-synthetic-design.md #"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-2014721666dccf35
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-08-11-ego-datalift-m1-synthetic-design.md
# Ego DataLift M1 合成数据严格 A/B 设计

状态：2026-08-11 经业务所有者批准进入设计与离线实现。本文不授权真实数据下载、外部系统调用、
线上部署、采集、众包、客户交付或结算。

## 1. 要回答的问题

M1 只回答一个可证伪问题：在相同的合成第一人称操作帧、训练/测试切分、特征、模型、随机种子、
训练步数和算力预算下，基于视觉运动与接触信号生成的细粒度 treatment 标注，是否比 control 的
弱时间模板标注更能支持：

1. 动作片段识别；
2. 动作时间边界定位。

M1 不证明真实人类 Ego 数据、客户数据、世界模型或 VLA 会获得同等增益，也不证明数据可复卖。
若 treatment 未同时提高两项预声明指标，结果必须记录为 `no_gain`，不得修改测试集、阈值或任务
定义来制造正结果。

## 2. 路线选择

### 已选择：项目自生成合成 Ego 微数据

`Nautilus Synthetic Ego Microset v1` 由本仓代码和固定种子生成，不使用真人、客户材料、下载
视频、品牌资产、第三方 3D 模型或场景纹理。每个 episode 是一段第一人称风格 RGB 帧序列：
手部代理接近物体、建立接触、搬运至目标区域并释放。生成器同时保留仅供评测的隐藏阶段真值。

权利与个人数据声明：

- `internal_evaluation = allowed`
- `model_training = allowed`
- `redistribution = allowed` 仅适用于本仓原创生成的合成产物；原始帧仍不进入 Git
- `commercial_resale = for
