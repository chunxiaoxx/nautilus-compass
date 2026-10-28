# 承运契约 M1 备线配方(设备到货触发,本文档=待命配方,零新机制)

> 9/7 立。背景:9/6 承运契约投影函逾期未回,**契约默认生效**;函内约定"到货前平台不动工接线,只备配方"——本文档即该配方。触发条件=飞轮函报设备到货(其仓路线图 M2.1/M1.3 关键路径)。

## 现有机制盘点(9/7 实测 DB 真值)

- `tasks.task_type` = enum `tasktype`,现值:`CODE / DATA / COMPUTE / RESEARCH / DESIGN / WRITING / OTHER`——无采集域 kind,需扩值
- `tasks` 关键字段:`publisher / description / input_data(text) / expected_output(text) / reward(bigint) / agent / result / status(enum taskstatus 含 VERIFIED/verified_at)`
- verdict 载体 = `fde_verdicts` 表(名带 fde 前缀但为通用 verdict 记录):`verdict_id / task_uid / source / checklist_uid / overall_pass / veto_failed / score / items(jsonb) / artifacts(jsonb) / external_verified`——**复用表结构,不等于复活 fde_dispatch 管道**(红线③)
- 结算侧:`platform_agent_capability_stats`(capability 记账);reward 金额口径=挂飞轮报价成本(红线②,数值到货时对账后填)

## M1 范围(只三个环节)

一集真实采集数据从 #3 流到 #5,全程任务化留痕,verdict 可查。

## Step 1 · enum 扩值(一次迁移)

```sql
ALTER TYPE tasktype ADD VALUE IF NOT EXISTS 'COLLECT_EPISODE';
ALTER TYPE tasktype ADD VALUE IF NOT EXISTS 'QC_PASS';
ALTER TYPE tasktype ADD VALUE IF NOT EXISTS 'CONVERT_LEROBOT';
```

注:PG 12+ 事务内 ADD VALUE 后同事务不能用新值——迁移单独提交,再走业务写入。

## Step 2 · 三环节任务发布与机械判据(红线①:全部机械/客户可验,禁 LLM 自评)

| kind | input_data(JSON) | expected_output 判据(机械) | verdict items 示例 |
|---|---|---|---|
| `COLLECT_EPISODE` | 询价单口径:场景/动作清单/时长阈值/素材路径 | 素材文件存在 + 时长≥阈值 + 动作清单逐项命中 | `{"file_exists": true, "duration_ok": true, "actions_hit": "N/N"}` |
| `QC_PASS` | qc_pipeline 报告路径 | 读报告 JSON:全过=PASS / 超阈=REJECT(回 #3) | `{"checks_total": n, "checks_pass": n, "threshold_breach": []}` |
| `CONVERT_LEROBOT` | LeRobot 输出目录 | 读回验证:parquet 帧数==源 / 双 mp4 存在 / valid=1.0 | `{"frame_parity": true, "mp4_both": true, "valid": 1.0}` |

publisher=platform;agent=9000014(flywheel-resident,#3 由采集员 P1 实名注册后归属其 id)。

## Step 3 · verdict 接线

每环节完成时落 `fde_verdicts` 一行:`source='carrier_v1'`,`checklist_uid=carrier-m1-#<环节号>`,`items`=上表机械检查结果,`overall_pass`=全项 true。L 红线一票否决(veto_failed)属环节 #6 计量,不在 M1。

## Step 4 · M1 达标验证查询(复活判据,一查即知)

```sql
SELECT t.task_id, t.task_type, t.status, v.overall_pass, v.created_at
FROM tasks t JOIN fde_verdicts v ON v.task_uid = t.task_id
WHERE t.task_type IN ('COLLECT_EPISODE','QC_PASS','CONVERT_LEROBOT')
  AND v.source = 'carrier_v1'
ORDER BY v.created_at;
-- 达标 = 同一集数据三行连续 overall_pass=true
```

## 红线复述(与 9/6 函一致)

①verdict 机械可验或客户可验,禁 LLM 自评 PASS;②reward 数值挂飞轮报价成本口径,平台不自定价格;③fde_dispatch 不复活,业务走 org task 语义(本配方用 tasks+fde_verdicts 表,不触碰 dispatch);④环节 8(客户交付+收款)永远人类专属,不进本配方。

## 触发前平台侧零动作声明

本文档落盘即备线完成。设备到货前:不改 enum、不发布任务、不写 verdict——一切等飞轮到货函。
