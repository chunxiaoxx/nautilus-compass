# 10/9 死线带执行 Runbook(2026-10-08 夜冻结 · R375)

> 明日四线:垫跑/冲正重算窗/RFC 表决/判读岗值守。本 runbook 把执行序/触发条件/命令全部实物化,新会话零考古直接执行。

## 00 · 开轮序(不变)

信箱(`to=compass&unread=1`,[派单·assay] 前缀优先接单)→ 9876 probe(必带 \n)→ 本 runbook 各线。

## 01 · S6 垫跑(夜班已实质起跑)

- **现状[实测]**:pull_batches 后台跑,#17/30 进行中,#1-16 OK(单镜像均值 ~1.9G);余 37G;护栏=余量<25G 自停(预计自然停在 ~#23)。
- **晨检**:`tail -20 /home/ubuntu/s6_rerun/pull_batches.log`+`docker images | grep -c sweb.eval`+`df -h /`——报三数(完成数/余量/是否触 GUARD)。
- **扩容切换**(候用户 a/b 拍板):
  - a) 用户控制台扩 180→280G → 平台 growpart+resize2fs+df 三验 → **我方重跑 `nohup bash /home/ubuntu/s6_rerun/pull_batches.sh`(EXISTS 自动跳过,只拉剩余)**;
  - b) 用户供国际站 SecretId/Key → 平台 tccli intl 代执行 → 同上;
  - 判据不变:30/30 镜像齐→swebench run→判读岗 L2 深度(执行者 v5/平台协同,排期 10/9-11)。

## 02 · 冲正重算窗(10/9 12:00 窗 · 平台执行+我方判读)

- 前置核态:10670 序=v5 处方落地回函(#10616)确认(信箱留意落地函);**再生成 SQL 现算版为唯一权威**,执行日现场重算。
- 执行完成函到后(判读岗 24h SLA):
  1. 五门 SQL 依 `docs/metering/S6_RECOMPUTE_ACCEPTANCE_20261008.md`(A1 全量 SUM=balance/A2 逐行连续/A3 押注释放对称/A4 触发器 DDL/A5 双案例回归)——单一只读 REPEATABLE READ 快照;
  2. 五门全绿=PASS 出卡(卡号顺延),任一红=FAIL 如实报,零"部分通过";
  3. 卡带五门 SQL 原文+行数读数(可复算)+回函 platform/v5。

## 03 · RFC 表决(死线 10/9 22:00)

- 表决函候收(信箱未到;身份层宪章 10629 相关线)。到函后:读表决项→对照 `docs/sops/ROLE_PERMISSION_MAP_V0_20261008.md`(角色三级映射已备,spec 到即零现场工作)→判据表态→正本回函(**不走 ack note**,R351 教训)。

## 04 · 判读岗值守

- [派单·assay] 真实单:接单→判据档 sha 复核→三态判读→出卡→回函;SLA l1+1d。
- 首例链已通(#10727 平台复现✓),按制运转即可。

## 05 · 随行件(非明日死线,排期锚)

- 10-11 终检:final_check.py 复跑(预演已 12/12 全绿,R372)——正日一键;
- 10-12 开业:XERJ PR 窗开(草稿备妥 R373,零现场工作);PRECOR 候两拍板(R374 决策卡);
- mem0/扩容/PRECOR 三拍板项候用户中,勿催勿代办。

—— compass · DEADLINE-RUNBOOK-1009 · R375

## 夜班终态补记(2026-10-08 深夜 · R376 实测)

- pull_batches **21/30 OK 后 GUARD 自停**(avail=23G<25G,#22 精确触发)——护栏语义验证通过;
- 磁盘 148G/178G(余 23G);剩余 9 镜像待扩容后重跑脚本补拉(均值 1.9G,~17G,280G 盘零压力);
- 晨检命令不变(tail log+images 计数+df);扩容 a/b 拍板后按 01 节切换。
