# 会话交接节点(2026-10-14 全天版 · 接续 night 版 · 本机+云端双域)

> **先读**:docs/_NODE_session_handoff_20261014_night.md(凌晨窗五件)+本文(晨午后窗增量)。
> **loop**:Cron 45509a9d(session-only,每小时 :11/:41,增强版含 8 锚巡检)——新会话需 CronCreate 重挂,模板在 LIVENESS_RUNBOOK_V1 §二。
> **分支**:soul-distill-deploy 与 master 同步于 9e23fd7e8(三线合一后)。

## 一、晨午后窗新增(夜窗五件之外)

1. **GitHub Action 落地**:独立公开仓 github.com/chunxiaoxx/nautilus-judge-action(self-test CI 真跑 SUCCESS);README/action.yml 已修(仓引用+token optional);bench 榜单页+submit 页双 CI 入口。
2. **/submit/ SPA 兜底断面修复**:10/10 基座改版潜伏(conf 无 submit location,目录页落 app SPA 兜底);conf 已补,7 锚回归绿。
3. **judge_status 502 代修**(用户拍授权越 turf):compass tools/judge_status_api.py do_GET 缺 else 分支(id 不在 LEDGER→body 未赋值)→补 404 分支,四态实测绿;diff 留 compass 工作树候其收编。**真卡接入仍候 compass**(JD-20261013-001 不在 LEDGER,首考窗已过)。
4. **compass 读函失效定案**:非故障——10/6 收敛令停各框 loop,compass 无值守轮,函堆 DB 等开轮。对策=待办总汇函 **#11214**(六件必办一函并清),其下次开轮照单执行。
5. **收款三步操作包已备**:测试单 **sid=1caff8497a95444d**(l2,付款通道验证单 $1);微信通道 https://chunxiao.wang/pay/?sid=1caff8497a95444d&tier=test /USDC 通道 /pay/usdc?...tier=usdc_test;两链接实测 200。**pay 应用在 manus 机**(115.159.62.192,/opt/nautilus-pay/pay_service.py:3344,不在云机)。候用户转账→自动 transition→四件回执。
6. **四步方案①②③④全落地**:①正本三线合一 master=9596b15a1(conf-sync 分支已删,云端工作树已对齐)②LIVENESS_RUNBOOK_V1 8 锚 ③MAINCHAIN_MAP_V1 贯通图 12 节点 ④ASSET_WEEDING_LEDGER_V1(已拔:8 死任务+3 MCP+旧 happy;候拍 6 项:3-8 号)。
7. **本机治理**:13 定时任务 SYSTEM 化(CMD 弹窗根除)+3 失效 MCP 停配(.claude.json.bak-20261014-mcp)+旧 happy 杀(省 1.6GB);18001 密集调用=组织推理业务正常负载(context 超限重试放大已函 v5 建议 #11205)。
8. **Wave3 二批清单 V2**:三向搜索 25 仓(20 主+5 候补,排除记录齐),发车条件=首批观察窗(10/21)有回响。

## 二、在途/候件(接手即看)

| 件 | owner | 状态/死线 |
|---|---|---|
| 收款三步 | 用户 | sid=1caff8497a95444d,链接就绪候转账 |
| compass 待办总汇(六件) | compass | #11214;其开轮时清;真卡接入最重 |
| Wave3 首批 16 仓 | 触客 | 观察窗 10/21;2 关闭 14 open |
| Wave3 二批 25 仓 | platform | 候发车条件;清单 V2 就绪 |
| Wave2 七家回信 | 触客 | 0;PlanB 二触 10/20 |
| 候拍 6 项 | 用户 | 拔草台账 3-8 号(fde vhost/org 驾驶舱页/workbuddy/pipeline 待考/四 vhost 自查/DB 历史层冷备) |
| intake 免认证 token 门 | 用户 | 产品级候拍 |
| conf-sync 后续 | — | 已合并删支;云端工作树=9596b15a1 对齐毕 |

## 三、本 session 新增坑(免疫册)

1. **401 响应体=答案自证**:写认证指引前必 curl 无凭证请求看响应体(平台=X-API-Key 非 Bearer,曾写错发三框靠此自纠,#11188/89/90)
2. **发函 API POST 全字段**(from_agent/to_agent/trace_id/deadline)+GRACE 后 401;生产通道=ssh cloud+send_letter.py
3. **云端 nautilus-mvp 工作树独立 coord 线**:rebase 必冲突;正本收编走分支再 merge master(本次配方=本地 merge 三线→push master→云端 checkout -B 对齐)
4. **外链禁 commit 锚**(hash 烂尾于仓重建);触客帖 24h 内全链验证
5. **nginx 目录型页面**(/xxx/ 形态)必须配 location,单文件 .html 可靠 \.html$ 正则段
6. **powershell 经 git-bash 调用**:$ 与 $_ 被 bash 吞——写 .ps1 文件 -File 执行;schtasks 改 RU SYSTEM 需 UAC(Start-Process -Verb RunAs)
7. **LOOP_STATE_SSOT 类冻结档案冲突**:双版本并存+考古注,不裁历史

## 四、复启指引(新会话第一分钟)

1. 读 night 版+本文;CronCreate 重挂 loop(模板 LIVENESS_RUNBOOK §二)
2. 开轮三查:信箱未读+发函 ack(重点 #11214 是否被读)/收款单是否已付(GET /api/platform/org/assay/submissions/1caff8497a95444d 看 status)/时钟(10/20 PlanB、10/21 Wave3 窗止)
3. 若用户报已转账:curl pay 单据验证+查 transition+四件回执,销"收款三步"候办
4. 主线唯一:首单线索即呈;零线索候 10/21

—— platform · 2026-10-14 晚 · 接手者自第二节候件表起
