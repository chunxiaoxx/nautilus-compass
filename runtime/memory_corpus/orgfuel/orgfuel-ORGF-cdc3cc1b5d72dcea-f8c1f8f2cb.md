---
name: orgfuel-ORGF-cdc3cc1b5d72dcea-f8c1f8f2cb
description: "flywheel 档案 2026-10-01-系统化方案v2-三大项目骨架.md # 系统化方案 v2:三大项目骨架(2"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-cdc3cc1b5d72dcea
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-10-01-系统化方案v2-三大项目骨架.md
# 系统化方案 v2:三大项目骨架(2026-10-01 · 承用户四定调,全框碰撞稿)

> **用户四拍板(10/1 午后,已落)**:①具身帧标注先做 ②G1 优先 ③管道产品**真正跑通**(非原型) ④标注供给=MiniMax M3.1-Flash-Preview(coding plan 免费)。
> **④已实测坐实**:真机器人鱼眼帧→四维语义 JSON 高质量(场景/物体/机械臂状态/有效性);key 走 cloud /opt/ecc-shared/.env(sk-cp,不落仓),调用远端做。**A1 零成本即刻起步**;m3.1-flash 同时是自训 7B 的对照基线+蒸馏教师。

> 性质:flywheel 视角的下一步系统方案骨架,今晚细化,全框回函后 10/2 汇总呈用户终裁。
> 承:目标修正案(今晨,北极星=第一笔外部收入)不废——三大项目是它的执行形态:①②造产品能力,③造通道,全部指向"可卖的东西"。

## 总图:一套底座,三大项目,一个飞轮

用户定性:**记忆 + 具身 + harness 走到最终都需要同一套数据飞轮和底座架构(共性问题)**。

```
                    ┌─────────────────────────────────┐
                    │   底座:判据库+轨迹库+决策Schema    │←── 组织纲领:轨迹即本体
                    │   (calibration_bank+900+条Schema) │
                    └──────────┬──────────────────────┘
                     
