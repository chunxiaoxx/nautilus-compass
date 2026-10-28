# 主链活性巡检 Runbook V1(2026-10-14 · 四步方案②落地)

> 缘起:/submit/ 死 4 天、判读卡断链 8 天、judge_status 502——死因共性=无维护回路。本 runbook=主链节点的定期走查清单,挂 loop prompt 每周全量+每轮抽查。

## 一、主链节点与验收锚

| 节点 | 验收命令(期望值) | 上次验证 |
|---|---|---|
| bench 榜单页 | `curl -sL https://bench.nautilus.social` → 200·含"免费榜单收录"+"nautilus-judge-action" | 10/14 ✅ |
| 提测表单 | `curl -sL -o /dev/null -w '%{size_download}' https://www.nautilus.social/submit/` → **>10000**(794=SPA兜底=死) | 10/14 ✅ |
| 判读 intake | POST `/api/platform/org/assay/submissions` 全字段 → 200(smoke 提交,is_smoke 自动标记) | 10/14 ✅ |
| judge_status | `GET /api/judge_status?id=任意` → **非 502**(200/404) | 10/14 ✅(代修后) |
| 判读卡样例 | `curl -sL -o /dev/null -w '%{http_code} %{size_download}' https://org.nautilus.social/L1_READOUT_CARD_mini_swe_agent_20261006.md` → 200·3027 | 10/14 ✅ |
| Action self-test | `gh workflow run self-test -R chunxiaoxx/nautilus-judge-action` → run success | 10/14 ✅ |
| 函件回路 | org_mailbox to=platform 未读清零 + 我发函 ack 非 NULL 比例(>50% 为健康) | 巡检项 |
| criteria 披露页 | GET /criteria/ → 200·含 L1_READOUT 新链 | 10/14 ✅ |

## 二、loop prompt 增强模板(下次挂 loop 用)

```
[nautilus loop 轮] 开轮三查:①信箱未读+我发函ack;②时钟事件;③in-flight。
每周首次轮(+全量):跑 docs/LIVENESS_RUNBOOK_V1 全表 8 锚,任一红=按红灯序处置;
触客帖(邮件/issue)发出后 24h 内必跑"贴文承诺链接全链验证"。
主线:首单线索即呈用户;零线索按 PlanB。纪律:一轮一件/claim 必附验证/4h 拒 ship/R1 自停/闭轮 memory+函。
```

## 三、已修死点台账(防复发对照)

| 死点 | 死龄 | 根因 | 防死位 |
|---|---|---|---|
| /submit/ SPA 兜底 | 4 天 | 10/10 基座改版未验目录页 | 巡检锚 2;目录页必配 location |
| 判读卡 404 | 8 天 | 对外链接指 commit 锚 | 铁律:外链禁指 commit;24h 链接验证 |
| judge_status 502 | ≥2 天 | compass api 分支缺 else | 巡检锚 4;compass 读函回路待修 |
| fde/claim 风暴 | 31.5h | GRACE 后客户端未升级 | 归因指纹法(UA+节奏);本机任务栈 CPU 关照 |

—— platform · 2026-10-14
