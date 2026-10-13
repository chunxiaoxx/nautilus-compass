---
name: orgfuel-ORGF-2212475cd3fb19b6-da2ebc7476
description: "flywheel 档案 2026-09-01-labeling-sop-v0.md # 轨迹标注 SOP v0（骨架）—"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-2212475cd3fb19b6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-09-01-labeling-sop-v0.md
# 轨迹标注 SOP v0（骨架）——Label Studio 自托管

> 2026-09-01 立档（GOALS S8-3 起步）。标注台=cloud 上 Docker 自托管 Label Studio v1.23
> （容器 labelstudio，数据 /opt/flywheel/labelstudio-data，nginx /labelstudio/ 反代）。
> 对外入口随 443 端口方案落定后开放。试点启动（W1）时本骨架升 v1。

## 已就绪（9/1 内部验证）

- 自托管实例：cloud 127.0.0.1:8081，账号 flywheel@nautilus.social（密码金库 CONSOLE_ LS_*）
- demo 项目"轨迹质量标注 demo"（id=1）：视频+质量单选（合格/黑帧/抖动/遮挡/含人脸待脱敏），1 任务导入 PASS
- 认证：v1.23 legacy token 已禁用，用 session（curl 配方：GET /user/login/ 取 csrf → POST login → 带 cookie+X-CSRFToken 调 /api/）

## 标注规范（W1 试点前充实）

- 任务单元：一条 episode（=一次技能演示视频），与 LeRobot episode 一一对应
- 标注项（v0）：整体质量单选五档（同 demo config）；v1 增加时间段标注（起止帧
  打成功/失败标签，对应"条目化演示+成败标签"数据形态）
- 判定口径：与计量协议 L 项联动——"含人脸待脱敏"直接触发 QC 复检，未脱敏不入库
- 一致性：同一任务 ≥2 人背靠背标注，分歧入 C 指标（跨采集者一致性）训练集

## 验收抽检

-
