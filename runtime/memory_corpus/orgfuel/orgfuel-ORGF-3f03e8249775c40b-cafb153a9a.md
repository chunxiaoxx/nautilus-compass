---
name: orgfuel-ORGF-3f03e8249775c40b-cafb153a9a
description: "flywheel 档案 2026-09-21-Dexbotic格式衔接实测-真相记录.md # Dexbotic 格式衔"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-3f03e8249775c40b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-09-21-Dexbotic格式衔接实测-真相记录.md
# Dexbotic 格式衔接实测——真相记录（对外表述校准点）

> 2026-09-21 · 依据 dexmal/dexbotic@HEAD 源码实读（本机 clone）

## 实测发现（证伪了此前表述）

技术方案 v2 中"数据链路经官方 `convert_lerobot_to_dexdata.py` 衔接"的表述**过强**，实测真相：

1. **该脚本是 Galaxea 双臂机器人专用硬编码**——解析的列名 `observation.state.left_arm/right_arm/chassis/torso/双夹爪` 等均为 galaxea_open_world_dataset 专属 schema，对我们的数据（LIBERO panda 单臂 8 维 state / EGO 系列）直接运行会失败
2. Dexbotic 的官方定位是"提供数据转换范式（guide）"，**每接一种新机器人形态需要写一个适配转换层**——这不是缺陷是设计（各家机器人 schema 千差万别）
3. 我们的 LeRobot 3.0 产物与 Dexbotic 衔接的**真实路径 = 写一个"我们数据 → DexData schema"的适配转换器**（读懂其 target schema 后约半天工作量）

## 对外口径修正（原力灵机材料升级时）

- ❌ 旧表述："官方转换脚本衔接路径现成"
- ✅ 新表述："转换范式官方已有（我们实测过其脚本），我们与你们数据格式的适配层我们承接——半天量级，试检时一并交付"

**这个校准反而更强**：显示我们真读过他们代码（知道脚本是 Galaxea 专用这种细节），且主动承接适配工作。

## 跟进

- 适配转换器（LIBERO/EGO → 
