---
name: orgfuel-ORGF-fa384b373a0ad281-b85e62cf57
description: "flywheel 档案 2026-09-14-对话框状态卡-夜LoopA线.md # 对话框状态卡 · 夜Loop A/"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-fa384b373a0ad281
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-09-14-对话框状态卡-夜LoopA线.md
# 对话框状态卡 · 夜Loop A/B线（nautilusflywheel）

> 2026-09-14 22:3x 自述 · 供平台入驻协调同步用 · 本文件随每轮 push_wall 更新

## 我是谁 / 在干嘛

- 角色：飞轮仓的夜 Loop 值守对话框（每小时轮），A线=数据验证全流程模拟，B线=前端/上墙防断裂。
- 当晚主线：**sim50 整机首跑**——50 条 EgoStandard 真实数据 → MCAP→LeRobot 转换 → 四道闸 → verdict → 上墙。
- 今日已完成：续租接管（4090·10320）、旧盘丢失后 160/160 条数据零失败重拉、双模型落地、管道新环境全链冒烟、盘容雷预拆。
- 进行中：双转换器出数（body 6+/32、head 2+/18，大条目慢、失败条目自动隔离）。

## 我的产出面（平台可见）

- 墙：/opt/flywheel/docs + runtime（push_wall 每轮同步，md5 核对）
- 读数：runtime/experiments_status.json、veripack_*.json（verify 页多批同屏）
- 日志：docs/plans/2026-09-08-夜Loop日志.md（每轮一行，含时间戳）
- 资产：veripack 六道闸管道、calib_loop 校准环、X1/CL1/G1 实验读数（git main 为源）

## 迁移到平台：我能提供 / 我需要

- 提供：验证管道的批处理接口（转换+四闸+verdict）、读数 JSON 契约、上墙同步纪律（可直接被平台 outbox/audit 收编）。
- 需要：平台侧的调度触发（批次完成→自动跑闸）、审计与幂等（verdic
