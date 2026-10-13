---
name: orgfuel-ORGF-ecebeb1e1e3462a9-f839057d5c
description: "flywheel 档案 2026-10-01-管道工程化实施方案-v1.md # 管道工程化实施方案 v1(2026-1"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-ecebeb1e1e3462a9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-10-01-管道工程化实施方案-v1.md
# 管道工程化实施方案 v1(2026-10-01 · 实现规划,呈批后开工)

> 目标一句话:把"一堆好零件"装成一台机器——客户数据进、计量单出、账收到。
> 本件是工程实现规划(架构/数据模型/接口/阶段验收),不是战略文档。批准即开工,按阶段交付,每阶段带验收判据。

## 一、总体目标与总验收

**总验收(10 月中)**:开源 4000h 假负载,**一条命令**从接入跑到计量单,零人肉干预,断点续跑;试检通道(上传→报告)在工作台可用;首名客户试用。
**红线**:不造大平台;复用九件现役工具;SQLite 起步不上重型组件;全部动作留痕可复算。

## 二、系统架构(五模块)

```
[采集/上传] → ①orchestrator(编排) → ②registry(注册表/状态)
                    ↓ 调度
             ③stage workers(阶段执行器,包现役脚本)
                    ↓ 产物
             ④artifact store(runtime/ 目录+sha 锚定)
                    ↓
             ⑤delivery(计量单渲染→工作台页/飞书)
```

## 三、数据模型(SQLite 三张主表)

```sql
-- 批次表:一批数据的身份与来源
CREATE TABLE batch(id TEXT PRIMARY KEY,        -- batch_20261002_a1f3
  source TEXT, size_hours REAL, uploaded_at TEXT, status TEXT,  -- ingesting/qc/re
