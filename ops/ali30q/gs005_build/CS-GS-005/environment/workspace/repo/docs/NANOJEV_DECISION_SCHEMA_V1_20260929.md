# 组织决策 Schema V1(NanoJev 方法论×组织任务·2026-09-29)

> 精读源:NanoJev(commit 拉取 2026-09-29,scripts/build_game_decisions.py 代码级)。试点=b-human-001 帧质检。目标:把组织任务建模为 Jev 式原子决策,人类众包交付=gold 生产,判据=oracle,喂小模型动态权重训练。

## 一、Schema 定义(逐字段对齐 NanoJev)

```json
{
  "id": "frameqc:{frame_hash}",
  "family_id": "embodied_frame_quality_v1",
  "split": "train|dev|calibration|test|ood",
  "state": "帧特征读数(luma/blur_norm/前后帧差)+帧缩略图坐标(多模态可选)",
  "questions": {
    "label":  {"type": "choice", "instructions": "该帧画面质量属于哪类?",
               "criteria": {"black":"几乎全黑","freeze":"与前一帧相同","blur":"细节发虚","normal":"无上述问题"}},
    "is_confident": {"type": "boolean", "instructions": "此判断把握高吗?"},
    "agree_machine": {"type": "boolean", "instructions": "与机判基线(qc v0.3)一致吗?"}
  },
  "gold":     {"label": "black", "is_confident": true, "agree_machine": false},
  "gold_probs": {
    "label": {"black": 0.9, "freeze": 0.05, "blur": 0.0, "normal": 0.05},
    "is_confident": {"true": 0.9, "false": 0.1}
  },
  "gold_probs_kind": {"label": "annotator_distribution", "is_confident": "deterministic_truth"},
  "metadata": {
    "source": "human_crowd_annotation",
    "frame_id": "frame_0042", "qc_machine_baseline": "v0.3",
    "annotator_tier": "external_p1", "judge_version": "b-human-001-judge-v1",
    "review": {"auto_pass": false, "spot_check": "pass", "jury": "n/a"}
  }
}
```

## 二、方法论六精髓→组织映射

| NanoJev 精髓 | 组织映射 |
|---|---|
| 三种原子问题(choice/boolean/score) | 标注四分类=choice;置信度=boolean;结算档位=score |
| oracle 免费 gold | **判据管线=oracle**(机判基线+验收判据自动产生 gold_probs);**人类标注=高价值 gold**(机判盲区的帧,如局部黑帧 T2/T3 类) |
| 软硬双目标 gold_probs | 标注者置信度→软目标;判据机判→硬目标 |
| 原子判断与规划分离 | 标注=原子判断;质检流程/结算=代码规划——模型只判帧,不碰流程 |
| 五分区+calibration | train/dev/calib/test/OOD:calibration 用 Brier/NLL 管概率质量(组织判据管线天然支持) |
| 0.6B+决策头小模型 | 端侧 qwen3-0.6B~3B+决策头——**与小模型动态权重路线合流** |

## 三、数据生产线(因果倒置×训练飞轮接口)

```
任务市场派单 → 人类标注(朱亚鹏们) → 验收(判据+陪审)
     ↓                                    ↓
  组织赚服务费                    gold 标注(决策问题)
                                          ↓
                    oracle 补 gold_probs(机判软目标) → 五分区入库
                                          ↓
              小模型+决策头 SFT → TTT 动态权重(任务内适应)
                                          ↓
                    E1 金标裁判环(改前/改后对照) → 达标上线
                                          ↓
              学到的决策先验 → GEP 胶囊(跨体继承)
```

**商业×训练双闭环**:每一单众包交付=同时是服务收入+训练数据——SSI 路线里"快权重固化"的最难环节,用组织判据纪律+评测环解。

## 四、试点判据(b-human-001 衍生)

- 首批:朱亚鹏 100 帧 → 100 条决策问题(含机判对照)
- 扩批:每单人类标注自动入库(标注工具输出即 schema 格式——验收脚本直转)
- 门槛:≥2000 条后启动 0.6B 决策头 SFT 试训(NanoJev 参考:单任务 653 条即有效,Maze 653/train 到 75% 准确)
- 裁判:E1 金标子集 + Brier/NLL 校准报告

## 五、下一步(待批)

1. 验收脚本加"标注→schema"转换器(一行格式化,今日可做)
2. NanoJev 训练管线(开源)适配组织 schema(字段映射,10 月)
3. 与 TTT 层合流实验(10 月后)
