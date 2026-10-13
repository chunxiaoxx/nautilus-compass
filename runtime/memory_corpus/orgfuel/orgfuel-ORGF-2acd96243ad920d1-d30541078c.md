---
name: orgfuel-ORGF-2acd96243ad920d1-d30541078c
description: "flywheel 档案 ADR-0003-synthetic-ego-m1-source.md # ADR-0003：合"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-2acd96243ad920d1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 ADR-0003-synthetic-ego-m1-source.md
# ADR-0003：合成 Ego M1 来源与权利决定

状态：已接受，仅限 M1 本地离线评测

日期：2026-08-11

## 背景

M1 需要一个可以实际训练和评测、同时不继承真人隐私、第三方数据许可或客户权利的第一人称数据
切片。Ego4D 需要签署数据协议；DROID 与 BridgeData V2 的“公开”或代码许可证据不足以在本任务中
推导数据训练、再分发和商业复卖权；Genesis World 对首个 CPU 微实验并非必要依赖。

## 决定

本仓原创生成 `Nautilus Synthetic Ego Microset v1`。生成器仅使用本仓代码、Python/NumPy 数组、
固定颜色几何图元和确定性随机数，不导入真人视频、客户材料、外部图片、纹理、3D 模型、品牌或
第三方场景资产。

M1 权利声明：

- `internal_evaluation = allowed`
- `model_training = allowed`
- `redistribution = allowed` 仅描述本仓原创合成产物的权利状态，不授权把原始帧提交到 Git
- `commercial_resale = forbidden`
- `personal_data_status = synthetic`

原始帧、逐帧轨迹、隐藏真值和逐帧标注只能进入调用方指定的临时目录或已忽略的 `exports/`，
不得进入 Git。Git 只保存代码、Schema、合成测试向量、哈希、聚合指标和审计摘要。

## 证据与边界

- 批准设计：commit `85bfd7568431406a637610c31d412b504b010438`
- 冻结实施计划：`doc
