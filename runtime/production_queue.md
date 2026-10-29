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

- R202(10-29): 队列维持零PENDING(005B/008B BLOCKED不解禁);施工项=缺口档排期**第1项UT 3→21补齐闭合**:tests/test_gs005_degradation.py扩至21条(UT-4~17继续targets_badpattern=17条≥13·对FM-1~4逐面加密;UT-18~21独立锚focus四点=降级可见性一致性/启动自检内省面/配置校验strip防御/fallback等价性确定性),每条补evidence_required,task.toml补ut_count=21+test_is_sufficient+FM锚映射更新;tomllib门PASS;**双向实跑:金标21 passed/坑版21 failed满幅分叉**(staging容器同构布局/venv无psycopg_pool=ImportError降级口径与R195一致);selfcheck.md+双向日志刷新;信箱23678(zenmind digest)已ack。缺口余五项(score.py/calibration四件套/variants/counterexamples/assets+3连跑)候后续轮

- R207(10-29): 队列维持零PENDING(005B/008B BLOCKED候非qwen渠道裁决不解禁);两函收割全ack(#23819 v5三件执行结果+CS-513净场终判收讫→加难返工认领·#23824执行计划V1对号两项:分工对账哨10/30模板/10/31首轮+#005 spec与CS-513加难返工);施工=缺口档**第3项calibration四件套闭合**:GS-001同构平铺8件落tests/calibration/(四态patch+result.md·旧perfect/deficient/guessed占位三目录退役)·三态答卷新写(equivalent=事件簿记式property派生/defective=初始化面GP-1·GP-4齐而消费侧GP-2·GP-3缺/guessed=病根误诊重试方向·恒标pg)·**四态实弹梯度 full_score 21 passed / equivalent 21 passed / defective 5挂16过(挂点UT-2·13·14·15·21全消费侧语义与缺漏一一对应) / guessed 21全挂 = 1/1/0.762/0[实测]**·落档件终验复现一致+git apply --check全过+密钥形态串零命中[实测]·等价卷impls存_staging_calib/可升格variant_a·缺口余三项(variants差1份/counterexamples/assets+3连跑+依赖声明)候后续轮

- R211(10-29): 队列维持零PENDING(005B/008B BLOCKED候非qwen渠道裁决不解禁);信箱23871(v5回函)已ack并正文回函——①CS-513采纳「换坑形态后重投」②item_version绑定纪律采纳(判分JSON加题包md5短锚·候CS-513重投件落地)③v5撤回prompt诱因推测以我方A/B实测为准;施工=**缺口档第4/5/6三项一轮全清,排期全清**:第4项variants≥2(solution/variants/卷A_eventlog=R207 equivalent升格·卷B_ledger=新写账本组合式·两卷staging实弹各21 passed[实测]·md5 cd493eb8/9b210cbe)+第5项counterexamples(反例程序直调被测repo真实入口·三态实跑[实测]:坑版exit1四项静默证据/金标exit0/卷B exit0)+第6项assets归位(selfcheck.md→tests/assets/+golden层级迁移两件·迁移后双向复验金21/坑0零破坏[实测])+双向3连跑逐字一致(金3×21passed/坑3×0passed)+依赖锁tests/requirements-lock.txt(ENV-04精确版本4件·psycopg_pool刻意不装=ImportError降级题目语义,锁头注明)+baseline_runs四态基线JSON(1/1/0.762/0[实测]·模型面候qwen渠道修复如实注明);**全表10项✅——下一步=下轮重跑核对档全表复核后启打包(打包前密钥清洗警示仍有效)**

- R214(10-29): 队列维持零PENDING(005B/008B BLOCKED不解禁,bootstrap信箱0未读无裁决回函);**核对档全表复核通过+打包闭合**:全表逐项直验✅(tomllib门/UT 21=ut_index 21/badpattern 17/score.py双模式/calibration 8件/golden两件/variants md5与档一致/反例三态/baseline 1/1/0.762/0/依赖锁4件);**密钥清洗执行**(警示兑现):pkg交付副本14文件23处活形态串灭活(ghp_×7/AIza×12/GOCSPX-×2/sk-×2·首轮21+自匹配token修正2·日志secret_scrub_log_20261029.md)→复扫0命中→清洗后双向复跑零破坏(NOP 0/21 exit1·Golden 21/21 exit0·与R211基线逐字一致[实测])→tar 30M md5=8ee99a3823ba6b9a6af7a45658254795→NAS shared/codesense_real_lesson/CS-GS-005_v1_1029_clean.tar.gz(端到端md5一致)+README唯一有效包增CS-GS-005节;原始未清洗件仅存仓内(git 13密钥件剔除态不变)·pkg/+tarball入.gitignore护栏;**#005状态:结构补齐✅→已打包✅——候平台判分编排,交付/发函候用户确认,本轮不外发**

- R218(10-29): 队列维持零PENDING(005B/008B BLOCKED候非qwen渠道裁决不解禁,bootstrap信箱0未读无裁决回函);无施工项不烧会话——矩阵四题21:26满额对10/30 18:00锚在轨·#005已打包候平台判分编排(外发候用户确认)·顺手卫生:_staging_calib/staging施工容器清除(tests/score与正式位逐字diff一致后删·patches/impls 17件四态证据原始层已入库不动)·git status未跟踪污染清零·本轮exit 0

- R221(10-29): 队列维持零PENDING(005B/008B BLOCKED候非qwen渠道裁决不解禁,bootstrap信箱0未读无裁决回函·due_12h=0);无施工项不烧会话exit 0——#005已打包候平台判分编排(外发候用户确认)·矩阵对10/30 18:00锚在轨(R220值守23:36确认满额)·本轮exit 0
