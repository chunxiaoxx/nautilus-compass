# 诱饵层生产队列(2026-10-28 重建·原文件失联,内容自此快照恢复)

> 🔴 bait-loop 短路依赖本文件存在——缺失=grep 静默失败=短路永不命中(审计实锤的漏钱洞)。
> 本文件由 bait 轮更新状态列;其他循环只读不写。

| 序 | 题 | 状态 | 双态 | qwen | 备注 |
|---|---|---|---|---|---|
| 1 | CS-003(ephem·时区微秒域) | FAILED 超档 | ✅1.0/0.2593 | 0.963 | catalog层被看穿;时域+聚合=qwen强域 |
| 2 | CS-005B(audit·联审聚合层) | BUILT·BLOCKED(qwen渠道面) | ✅实测:坑版4挂(3gating全中+fsum)/金标8/8=1.0 | 无有效读数(四连溢出) | R176定谳:32K抬限无效——qwen3.8max 828s/bl 807s双渠道双时段均content empty(16:38-17:07),reasoning系统性吃满,「抬max_tokens取读数」备选路堵死;候出路=非qwen渠道判带或渠道面修(候裁决);scratch=/tmp/csCS-005B重建完好可复跑,件仓内档ops/ali30q/decoy_005B |
| 3 | CS-008B(OCR批清洗入口·版式处置) | BUILT·BLOCKED(qwen渠道面溢出,候非qwen渠道裁决,同CS-005B) | ✅R178重造复测一致:坑版4挂(3gating全中+validate²放行)/金标6/6=1.0(det 0.00s两遍一致) | 溢出(800.0s empty,19:13-19:22·F-009) | 515B二层=白名单静默丢弃≠§1打回("1²3"→"13"静默变形,跨§1/§3互锁)+isdigit放行'²';tomllib门过;🔴finding:①原golden.patch错配(内容=quota_gate记账金标,与OCR题面无关,已隔离,金标以solution直写件为准)②原conftest挂repo_bak与模型面repo/割裂(改A面测B面),已单面化+repo_bak退役;管道已同步;🔴10/28 R176:/tmp全灭连带件本体丢失,全盘无归档,重造需35min一轮(两层语义与双态结论在COLLAB_BOARD R174可考古) |
| 4 | CS-509B(三档加深) | FAILED(强域放弃) | ✅闭合 | 1.0(强域) | 10/28 R176终态更正:读数在案,无需再投 |
| — | CS-514 | SKIPPED | — | 强域 | 不投入 |
| — | CS-004B | CANDIDATE | ✅1.0/0.4643 | 0.4643 | 候五模型面+裁决 |
| — | CS-515B | CANDIDATE | ✅1.0/0.6923 | 时段分歧 | F-009定谳 |
| — | CS-513 | DELIVERABLE | ✅ | 0.5二值 | 过筛✅ |

## 配方纪要
- 有效(515B模式):双层互锁+policy枚举外语义+聚合层延伸;新实证 CS-008B:「处置纪律贯穿」型二层(policy §1 打回义务在批清洗入口缺位,输出形式合规但语义跳步)+校验函数字符类误判(isdigit≠ASCII)
- 无效(509B模式):单层延伸+草稿辩护;qwen强域勿投:版本解析/常规异常分类/时域微秒+聚合层(CS-003B 0.963看穿)
- 每道 stop-loss 35min;双态不过=FAILED 照标;**若 qwen 判分在途(队列标 BLOCKED),本轮 exit 0 不烧会话**
- 🔴真值翻转(10-28 裁决22765/F-005修复实测):CS-003(0.07)/CS-004(0.21) 金标真挂=出题故障冻结;CS-005/514/515 金标真过 1.0。原版 GOLD-PASS 旧记录全部作废
- G1 全量批 10-28 起:判据=修复后 gold_check(非静默);账 /tmp/g1_batch_20261028.log

- R178(10-28): CS-008B重造闭合,双态与R174定谳完全一致(重造=复原非漂移);qwen 32K再溢出800s空(渠道面系统性故障R176已定谳,未烧run2);件归档ops/ali30q/decoy_008B/14件+_s5溢出证据,管道已同步;scratch=/tmp/csCS-008B完好

- R188(10-29): 队列零PENDING(005B/008B维持BLOCKED候非qwen渠道裁决,不烧会话);本轮主件转素材线——平台三函办结(23288素材库/23299配额映射ack·23292样板题完工ack·领卡回函23301先前已发409不重发);**compass领卡#005(env静默降级)开工**:spec骨架档落ops/ali30q/GS005_SPEC_SKELETON_20261029.md(卡号#005/坑面=静默fallback+配置错静默skip两层互锁/UT计划4条/model_failure_modes 4条/载体=core真实模块群1672py>300门宽裕);证据分层:defb148半边[实测]实锤(git直验·super_agent.py:375引用缺失API自5/18静默file fallback),env DSN半边[待补]实物坐标候考古;badpattern预映射F03·30条表候选F06.01候对表;施工轮出全件(坑版/金标/UT/calibration)

- R195(10-29): 队列维持零PENDING(005B/008B BLOCKED候裁决不解禁);本轮主件=素材卡#005半边1施工出全件(题包gs005_build/CS-GS-005·双态实跑金过坑挂·tomllib门过),calibration判据测试候判分批,打包NAS候下一轮;UT-3候半边2坐标如实留白

- R198(10-29): **打包闸判读=未过,不打包**——对照标准全图V1 B系列+活样板CS-GS-001(nautilusflywheel fuel_codesense实测:23UT/13targets_badpattern/score.py沙盒双模式/calibration四件套8件/variants 2/counterexamples py+log)逐项核对:GS-005差六项(UT 3/21+·score.py·calibration四件套·variants≥2·counterexamples+运行日志·assets归位+baseline_runs)+双向预检3连跑与依赖锁定两⚠️;缺口档ops/ali30q/GS005_STRUCTURE_GAP_20261029.md(逐项标正本行号);WIP快照已归档NAS shared/codesense_real_lesson/_wip/(md5 c8851137·README防误取·密钥警示在档);#005状态:候打包判分→**结构补齐中**(六项分轮施工,补齐后重跑核对档全表再启打包);诱饵层队列维持零PENDING(005B/008B BLOCKED候非qwen渠道裁决,bootstrap信箱0未读无裁决回函不解禁)
