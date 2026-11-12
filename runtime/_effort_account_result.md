# 投入分布对账 · git 全量 commit 六线分类(脚本 _effort_account.py)

- 窗口: 2026-07-14 起 · 总 commit = 1701

## 月×线矩阵

| 月 | A | B | C | D | E | F | G | U | 合计 |
|---|---|---|---|---|---|---|---|---|---|
| 2026-07 | 9 | 3 | 7 | 0 | 18 | 1 | 4 | 17 | 59 |
| 2026-08 | 29 | 17 | 27 | 11 | 55 | 35 | 8 | 47 | 229 |
| 2026-09 | 288 | 29 | 38 | 93 | 66 | 109 | 10 | 12 | 645 |
| 2026-10 | 284 | 116 | 70 | 45 | 102 | 115 | 32 | 4 | 768 |
| 合计 | 610 | 165 | 142 | 149 | 241 | 260 | 54 | 80 | 1701 |

## B 线完整清单(自产燃料线,165 条)

`389392b7|2026-10-19|B1|fix(对外勘误): NACRE自举线底层无效定谳(用户亲审拍板)——registry.html挂勘误横幅+触发器改冻结(曾误显示8B触发5天)+errata账本10/19行公开留痕+q50真人卷下架;棘轮永久停止/语料数字撤出对外叙事/燃料只认人工与外部题/RAG用途保留;勘误正本+教训三条例checklist`
`5dbdafe7|2026-10-19|B1|feat(quiz): P2盲评50题真人对照卷上线(手机版)——nautilus.social/q50mhzqAH.html(随机token防猜,不外传);viewport+44px触屏按钮+复制式导出(下载json改剪贴板,适配手机);判据/题面与原卷一致,原runtime卷未动;用途=65%FAIL判定旁首个真人读数`
`9ca0b0a1|2026-10-19|B3|docs(metering): NACRE燃料路径决策档候拍——同日两正本矛盾坐实(964d22b6窗口开 vs 423997c0 P2 FAIL,池~2900自举标签已判死,8B窗口=程序开实质闭);选项A冻结等外部真评测题(默认零成本)/B小而净8B对照(1162人工标签+A100一次,SEVENB_PREREG v2前置);触发语义勘误建议随档`
`c685bf1c|2026-10-19|B1|fix(metering): pilot_r534_glm.jsonl损坏修复——HEAD版59行后断头残片(UTF-8前导丢失)+L45粘连/L61截断,写入端截断在提交前已发生;修复=粘连拆条+从HEAD素材恢复两条完整记录,62行全JSON合法;重复id×4=跑批重试痕迹原生保留,去重58唯一id与P0口径吻合;runner v1.3中文判定映射(glm偶发中文结论)配套收口;注:P0人工盲评侧逐条标签仅报告聚合(原有缺口,非本次损坏)`
`03284e85|2026-10-18|B3|docs(outreach): OGE状态呈报回函(id 13468)——cloud嵌入切换实测闭环(orgfuel recall hits=5/隧道mps ok)·迁移15包候openclaw导入·阻塞三件催办(378key/白名单/11213凭证)·69封未读全ack清零`
`1fe17170|2026-10-14|B1|feat(rag): ORG-FUEL语料2519条转RAG检索层(R536)——P2收口处置落地·独立项目目录orgfuel-corpus(daemon inotify收录)·md转换器(frontmatter带sm_verdict弱信号)·云端部署验证·FILL_BUDGET 300s drop-in(per-project锁安全)·预热watcher挂载(每10min触发直至hits≥2)`
`423997c0|2026-10-14|B3|feat(metering): R535 P2验收FAIL(二值65%<90%门)——重判标签不回池·根因=自产文档'判例vs非判例'任务人机一致性天花板65-75%·可信SFT燃料终局=1032条人工评测题·自产语料正确用途=RAG检索层·负结果链闭合(8B/1.7B-v2/P2三连)`
`b90c5b0b|2026-10-13|B1|feat(metering): R534 P1全批完成(2519条glm-5.3重判)·P2盲评包252条自动生成(watcher链无人工)·分布落档·待明早盲评对拍≥90%回池`
`b8c9db7b|2026-10-13|B3|feat(metering): glm-5.3经自建中转P0双达标(二值89.1%全场最高/pass精确88.9%/误pass仅2)·runner加relay通道·P1全批2519发车·P2抽样器就绪(10%分层SEED 20261014)·watcher自动衔接·IHUI#78四问全答(判据页/验证栈/自举事故披露/pre-pilot如实/验收付款流程)`
`0575a836|2026-10-13|B1|fix(corpus): R533空输入根修——org_fuel系verdicts行situation字段搬运(分级兜底content→situation→artifact_ref→数值)·触发池v1历史保留·新建orgfuel_v2(3551条·空输入=0·双sha)·42条修复后补盲评(一致率59.5%仍FAIL)·终局47%·judge全pass化为天花板·修复三步维持`
`f7e7e0a3|2026-10-13|B1|feat(metering): 自举标签审计R532——一致率37.9%方向门FAIL·judge全pass化(58/58+空样本42/42)·违反9/30反自指护栏(自产标签入训练燃料1800+)·四臂归因勘误(主因=标签崩坏非数据量)·数量棘轮暂停·修复路径三步(强模型重判+10%人工复检+复检审计)·8B/1.7B重训冻结`
`cae28c27|2026-10-13|B3|docs(metering): 四臂对照判定卡落档(现役0.9667最强/8B+1.0不升格/1.7B-v2-2.0不切换/4B挂起——A100盘配额顶格三路下载全阻·跨框协调解法留档)·合成结论:标签质量>数据量·下一杠杆=人工抽检自举标签`
`2d12ad7b|2026-10-13|B3|feat(metering): 现役线重训1.7B-v2负结果——U5不劣门FAIL(-2.0pp·0.9467vs0.9667)·预注册自动裁定不切换·自举标签池训同尺寸=负增益(标签质量>数据量直接证据)·4B观察臂接力已挂(下载完自动跑)·判据档R530出数前冻结`
`cf1bbfff|2026-10-13|B3|feat(corpus): r5 verdicts 正本入仓(-f过jsonl忽略惯例·复算开放)`
`964d22b6|2026-10-13|B1|feat(corpus): commit流源R5(本仓2033 commits+92 docstring→761候选·708过门93%史上最高密度)·merged 3294→4002(4000线达标)·线上stats同步·8B重评窗口再开(下次杠杆=标签质量)`
`2d3121f9|2026-10-13|B3|feat(metering): 8B触发日逐例评测双文件+upgrade_report正本入仓(复算开放,-f过eval忽略规则的既有惯例)`
`3a85fc6e|2026-10-13|B3|feat(metering): 8B触发日正式对拍判定——U6/G1主门FAIL(+1.0pp<+2.0pp冻结)·预注册自动裁定8B不升格1.7B维持现役·负结果照报·归因(数据量主因/1epoch配方修复过拟合生效/切分合规)·qid泄漏73首跑拦截(审计键与比对键不同构根修)·自举标签63.7%知情披露·复算坐标全公开`
`6b50daf0|2026-10-13|B1|feat(corpus): 3000判据达标——grain源892段级判定690过门入池·merged 2553→3294(unique qid)·sevenb_compare_ready=true触发·线上corpus_stats同步(3294)·触发文案对齐R524口径`
`a8688a1c|2026-10-13|B1|feat(corpus): 细粒度源生成器fuel_gen_grain(判读档##段级切分·metering/cases/incidents/plans/soul/benchmarks六树·domain自动分型·R524并集排除内建)·候选892条真新增·r4判定发车A100`
`9c474c0e|2026-10-12|B1|feat(corpus+l2): r3扩容判定614条入池+51(merged 2553→2604/3000·缺口口径修正n_train→n_total真差396)·三生成器加已入池排除(二选一漏并集/ORGM键错位/flywheel未加三bug连修)·L2首单演练全流程走通(G1静默丢段bug抓出修复·老卡兜底全字段·ANALYST槽演练装订三查过)`
`89d4af1c|2026-10-11|B1|fix(ci): _gate_keeper.py→.sh(bash脚本误命名py,ruff invalid-syntax 致 CI Lint 48 连败)·fuel_gen_flywheel红线R1-R7收紧·noqa格式修`
`e0eed280|2026-10-11|B3|data(nacre): R513——8B全量预跑读数收割[实测]U1-U4全过+U5 FAIL(-3.08pp过拟合信号:25步0.88>873步0.846)·负结果照报·下次配方1epoch+early-stop·配置档证据层全实测化`
`d6aa36f6|2026-10-10|B1|feat(nacre): R509——flywheel 423判定收官[实测]pass 133入池·语料2420→2553外网live(sha 831750e0)·pipeline扩org_fuel:flywheel源·A100双任务并行`
`eee2d758|2026-10-10|B1|feat(nacre): R504——跨框语料扩容专项立项(flywheel源盘点:decisions/delivery/evidence/plans≈300件候选)·透明知会函10968(脱敏五步+边界声明+48h异议窗)·v5源缓入避观感`
`bb30ed19|2026-10-10|B3|data(nacre): R494——8B smoke产物归档[-f 沿先例,gitignore *.jsonl挡路](eval292双臂明细27KB×2+upgrade_report)·NACRE线数据资产保全`
`0351f4c6|2026-10-10|B3|feat(nacre): R487-488——8B smoke读数兑现[实测]峰值15.07G/输出100/100/U5短训+0.34pp不劣·配置档证据层全实测化·启动门参数化+语料软链修·10941 P0闭环ack`
`a0ad92a6|2026-10-10|B2|feat(nacre): R487——8B bf16训练smoke跑通[实测26.4G无OOM,LoRA挂载正确]·配置档证据层推断→实测兑现·启动门参数化(12G)+语料软链修·10941 P0闭环ack`
`c7eda65b|2026-10-10|B3|docs(loop): R475记录——8B零现场清单实体齐(判据+配置+脚本+基模+触发器五件全)`
`e164442c|2026-10-10|B2|feat(nacre): R475——8B训练脚本预注册版落盘(_train_judge8b_upgrade_A100.py)·U6对齐判据档0.02·五默认路径修正到实际在位·评测内嵌基座确认(零现场最后拼图)`
`f4d72667|2026-10-10|B3|docs(nacre): R471——8B训练配置预注册档(bf16全精度不用4bit+阈值不一致发现U6 3pp vs G1 2pp以判据档为准)·触发日零现场清单五步`
`eba51d31|2026-10-10|B3|docs(nacre): R470——8B资源线收官[实测]下载完成守护自停·对拍四项全绿零现场就绪·NACRE下一件大事只剩等语料+跑对拍`
`00c6999c|2026-10-10|B3|feat(nacre): R466——8B下载守护部署A100(hf-mirror两断自动化兜底,loop续传+完成自停)·15G推进中[实测]`
`765d29a9|2026-10-10|B3|docs(loop): R464——窗前就绪核查(XERJ草稿在位)+8B断连续传修复(9.5G增长中)`
`bae0bbd8|2026-10-10|B3|docs(nacre): R463——对拍判据档勘误注记(被测物7B→8B事实性修正留痕,G1-G4零改动)·预注册缺口自我证伪(档已冻结完整)·对拍就绪度判据/触发器/基模三齐`
`1bfaab46|2026-10-10|B3|docs(loop): R459——r87判据冻结确认(函10925,无异议生效)·LOOP_STATE全面刷新(值守纪律补课,下一会话零考古)·8B下载慢速观察项`
`980f2731|2026-10-10|B3|fix(errata): R458——勘误第8例:Qwen3系无7B(实测404),实为Qwen3-8B·registry文案勘误部署·8B基模下载hf-mirror通道跑起[376M+]·下载链排障(modelscope record not found表象)`
`43593135|2026-10-10|B3|docs(nacre): R456——7B资源预检(三绿一下载中,基模已启动)·🔴J6口径重大澄清(J6=需求侧裁决≠7B对拍阈值触发,R454错误绑定修正推迟预案作废)·10899/10916双ack`
`43ce8fbf|2026-10-10|B1|feat(nacre): R455——ORG-FUEL扩容闭环[实测]244全判pass162/门过162·语料2258→2420外网live(新sha f92cb549)·pipeline扩queue/memory两源·base64分块传输修复`
`14eb95e1|2026-10-10|B1|docs(nacre): R454——NACRE路线图落档(四洞察+时间轴+专项四优先级)·ORG-FUEL扩容开工(queue82+memory162=244新candidates,本地side)·诚实重算:扩容天花板~2400<3000,10/26主场景=推迟报告`
`dce50b9c|2026-10-09|B1|feat(web): registry页加名词速览卡(用户10/9拍四页全修flywheel代执)——黑话保留保技术准确,访客视角人话注释(NACRE三态/ORG-FUEL/delta棘轮/qid);跨框代修声明:flywheel网页审查职责+用户拍板,改动仅此卡`
`4be1f1d4|2026-10-09|B3|feat(tools): R430——S3环境探针+S4全框状态一览双脚本落地✅(实测双绿)+10838 GRPO训练闭环首证致贺(v5 held-out+0.95·NACRE互鉴)+R419b/R423记账收拢`
`1261954b|2026-10-09|B2|feat(api): R418——T5.1 NACRE判分API产品化✅(A100 19988服务活·adapter sha实锚dbcbab6f·/judge双测语义正确·compass隧道全通·BP矩阵判分API热路径实锚;通道三连根因:端口错配8400/临时管道/systemd unit·v33 per-call proxy隧道通即自动生效)`
`e4ef2e3e|2026-10-09|B3|docs(outreach): R410——双响✅(XERJ PR #1255 MERGED=首个第三方轨迹语料入hub候签名Release+v5 R3认账10781三方全绿闭环)`
`a484728c|2026-10-09|B3|feat(memx): R402——Embedder对拍开跑(判据预注册冻结:换模型门A/B各+2.0pp且C不降·三候选bge-m3锚+Qwen3-Emb0.6B/4B;paramiko通道+语料160md上岛+eval脚本三池化官方用法;双模型下载中)`
`42671c12|2026-10-08|B1|feat(memx): R398——三向归因算子v0落地✅(A缺口/B弱标注/C检索失效/NONE四分类·相关性门REL_MIN0.60过滤topk噪声·selftest6/6+双实测全对·attributions.jsonl棘轮·站3因果倒置实弹)`
`47ee443a|2026-10-08|B3|docs(soul): R396——MEMX记忆自催化飞轮设计V1✅(NACRE全名即架构图·四站闭环·因果倒置三向归因算子·涡轮逐项映射·反自指护栏·glue本周可实现)`
`bb5a1b16|2026-10-08|B3|docs(outreach): R386——XERJ PR提前发出✅(pull/1255 OPEN·corpus-hub两件·正文checklist逐项+#1138跟帖回链6060713784·用户令现在就推动·独立于开业无依赖成立)`
`51faf42a|2026-10-08|B1|feat(corpus): R378——首卡判例入册delta_0006✅(nautilus-l1-0002升格·truth_label=pass判读流程先例·平台复现=第三方复算门首例PASS;语料2257→2258 sha=93dccd83·三副本同步外网实测;registry FALLBACK同步+终检11/11回归绿)`
`2283f456|2026-10-08|B1|docs(readme): R365——中文README同步October判分柱段九bullet(承R357英文版;NACRE judge/精度纪律/caliber-bench/Round1/判例集v1.4/语料2257/E-NACRE-1负结果/客户旅程/格式回归集;zh长期滞后10/5补齐)`
`00d29232|2026-10-08|B2|fix(corpus): R363——split三件语料正本补入仓(fix:gitignore静默挡split_*/anchor_v0/reg100从未commit——10664复核5件不符根因之一;S6正本六件自此GitHub全可寻址)`
`35b73ccc|2026-10-08|B1|docs(prereg): R361——7B阶梯对拍预注册判据档冻结✅(四门G1升级线+2.0pp/G2三门/G3精度99%/G4观察;禁改条款只许收紧;触发=语料3000现2257;判据先行纪律)`
`7687a2d4|2026-10-08|B1|docs(readme): R357——October柱段补10/8新资产五bullet(Casebook v1.4/语料2257活计数/E-NACRE-1负结果/客户旅程三口径/格式回归集v1)+承诺链接全实锚`
`3cc59cc5|2026-10-08|B1|docs(handoff): R356——HANDOFF追加二✅10/8全日R345-R355十一轮战果+死线带现状+新工具环境锚(7B语料2257/3000;冲正三SQL坐标;终检一键复跑)`
`2470e224|2026-10-08|B1|feat(fuel): R354——delta_0005判例集v1.4入池✅16案(casebook正文终判短语映射零新判定;pass9/fail3/insuff4;domain五类;2241→2257实测;外网corpus_stats 2257;7B差743)`
`6643aabc|2026-10-08|B3|feat(fuel): R353——delta_0004回填✅13案结构化入registry(C冲正4/A2复算/E-NACRE负结果/PRECOR精度门3/运维定谳4;零新判定零放宽;2228→2241实测;外网corpus_stats 2241;终检脚本回归11/11×2)`
`08a54d73|2026-10-08|B1|feat(fuel): R348——语料2000冲刺达成✅1846→2228(+382跨门槛;docs源提取器重写799候选/A100判分1222条pass759;corpus_stats三副本同步外网实测2228;sha16=8f302d69)`
`4dcba5f4|2026-10-08|B1|feat(fuel): R348——org_fuel_harvest.py 判分收割段(SFTP拉取+FLAG门+管道重跑;A100判分环境锚/root/venv/bin/python绝对路径,nohup非登录shell无conda教训)`
`724d1b02|2026-10-08|B1|feat(fuel): R347——org_fuel_docs.py docs源提取器(799候选L0 582/L1 217;正本表格行/要点行切块+四标记判级) 补齐ORG-FUEL第4源提取段`
`77d851e0|2026-10-08|B3|docs(site): R346——主站改版compass供给包(NACRE卡+caliber-bench卡+统一导航条;五链外网200复验;函10602挂10566,死线10/10)`
`22579c16|2026-10-08|B3|docs(anchor): compass主线边界锚定V1(用户三点:compass+assay+jev三位一体/NACRE创新模型/评测燃料判分全归compass)+融合方案V0标注决策结果`
`77c21258|2026-10-08|B1|feat(fuel): R337——第四源外联档案入池(12条,1834→1846;四源自产源近枯竭,余量靠开业外部单+V5适配器)`
`622582f1|2026-10-08|B1|feat(fuel): R327——语料第三源docs判据档入池(235候选→118过门,1716→1834=61%;外网仪表同步)`
`510ce6ff|2026-10-08|B3|feat(memgate): R322——M5三件套生产部署✅(v33四锚patch 5/5+ndarray真值守卫;四验收全绿:ping/dedup实弹unique/chain零异常/CPU常态;NACRE第五组件转✅)`
`93e53531|2026-10-08|B3|feat(site): R320——registry状态活数据页上线✅(五瓦片+7B进度条+sha锚表;活数据corpus_stats.json外网200;值守轮自动刷新)`
`e31da7fd|2026-10-07|B1|feat(3track): R306——三线执行规划V1+网站材料包v1交付(首页IA/对接表/榜页详版)+ORG-FUEL v1函件流闭环(172候选→47入池,语料1716)`
`b6568534|2026-10-07|B1|docs(fuel): ORG-FUEL v1判据预告(函件流接入+元判读边界条款固化+燃料供给结构注记:自产密度衰减,开业=燃料闸门)`
`ac3368da|2026-10-07|B1|feat(fuel): R294——ORG-FUEL v0试点闭环✅(判定369:pass258/fail21/U90;入池242条L0178+L164;corpus_pipeline接org_fuel源,语料1453→1695,7B缺口-242)`
`323ac9fa|2026-10-07|B1|feat(fuel): R293——ORG-FUEL v0采集首跑✅(369候选:L0 268/L1 82/L2 19,超目标7倍)+判据档冻结`
`791f1935|2026-10-07|B3|docs(fuel): R292——ORG-PRECEDENT-FUEL V0(组织历史判例燃料自动化:四段机制+四防污染护栏+零重复造轮子;v0本周单框试点)`
`cca0256e|2026-10-07|B3|feat(training): R290——E-NACRE-1收数判门:负结果照报(路由无增益坐实,Δ-36.6pp三域全回退;归因=域片过拟合+训练量不足;升级路径=攒语料);判定档+CSV/log在档`
`dfd15e71|2026-10-07|B2|docs(training): E-NACRE-1 v1.2注记——分片键修订(domain全空→qid前缀)+三可训域片冻结(rejudge500/lme-d14451/lme-d12451)+对照公平性补充`
`14ae3463|2026-10-07|B3|docs(nacre): R288——理论基础四视角档(锚定链/投影算子/阻抗即权威/逆向因果)+E-NACRE-1判据冻结(路由技能片,主门Δacc≥+1.5pp)`
`01a7dab2|2026-10-07|B3|docs(nacre): R287——原生化路线图V0(核心洞察:验证内核作训练回路原生信号=可发表差异点;五实验E-NACRE-1~5全带设计,三阶段对齐死线)`
`0ee217dd|2026-10-07|B3|docs(nacre): NACRE定义二次修订(用户10/7)——原生六能力目标态(原生动态权重/原生RSI自进化涡轮增压数据飞轮/原生记忆/原生JEV+assay/原生核心专家技能)+§M1原生度路线表(目标态/当前态/路线)`
`a6cea2b5|2026-10-07|B1|docs(nacre): NACRE定义扩容(用户10/7)——六组件统一智能机制(压缩×验证×因果倒置+动态权重+RSI+涡轮增压+原生记忆+JEV/assay);机制章§M1六组件现状表+对齐账追记`
`35b54439|2026-10-06|B3|docs(nacre): R272——daemon值守三件全绿(补丁A/C生效实测)+NACRE机制章v1.5主笔(对齐四议题落章:机制名+实例版本/六部件防混列/双榜/部署四门/商业接口)`
`89c5ef38|2026-10-06|B3|feat(training): A+B+C 启动——PRECOR判据档冻结(量化漂移矩阵≥99%部署门+软维度只产数)+语料管道建成(1453唯一qid基线,7B缺口1838,双触发器);发车留交接(1.7B管线复原前置)`
`f9c350dc|2026-10-06|B3|docs(nacre): R269——NACRE四议题双签闭环落定账(platform 10124+v5 10128:机制名+实例版本/防混列/双榜分层/机制章v1.5)+SLA生效对表+五函ack+组织通报函`
`811916f3|2026-10-06|B3|fix(cloud): fusion残留根因落锤——chunk_embs ndarray经or真值即抛(单测复现逐字一致),补丁C安全迭代落盘留低峰重启;caliber-bench五通道终核全净待拍;NACRE底稿抄送v5(10123)`
`ce88193c|2026-10-06|B1|docs(nacre): R265——三拍板落地:7B先攒语料3000再对拍(J3追记)+assay-bench查重红灯搁置挂对齐会(J5追记)+NACRE对齐底稿四议题(函10105)+SLA分档修正函(10104:L1 24h/L2 48h)`
`d874fe0b|2026-10-06|B3|feat: E1复算4bit对照终数——0.8173/0.8110(题级47-50%翻转),归因链闭合(交卷=bf16坐实);新实证=量化对VL判读软维度巨大损伤,部署精度纪律入NACRE`
`e2076fd9|2026-10-06|B3|feat: E1复考发车件——双包runner(v4零改动)+ER1比对器+SFTP直传链路(sha双锚634a3f72/2a705d49);判读在跑0.8s/题`
`db2573a1|2026-10-06|B2|fix(metering): E1复考档勘正——判分器实为Qwen2.5-VL-3B 4bit(v4定版,交卷同款),非1.7B LoRA;环境=交卷同构本地优先;开跑前修正,判据零放宽`
`435ce86a|2026-10-06|B1|feat: 实验B收束——r64反降(容量排除),归因终局=语料量-参数匹配;14B记档待errata扩容重评(实验C并轨P3燃料线),护14B正路=喂语料`
`dfbc5388|2026-10-06|B1|docs(soul): 14B阶梯实测——量化归因排除(bf16无回升),实验B r64在跑,B红则接语料扩容`
`6b22965c|2026-10-06|B3|feat: J3补充令——14B翻案阶梯(复算292/292逐位复现+bf16对拍实验A发车+r64重训实验B排队);用户拍14B优先,判据不变正反照报`
`7bb95475|2026-10-06|B3|chore(loop): R244——E1回放前置探测(GPU空/14B adapter在/1.7B待定位)+发车runbook三步入账`
`75e798bf|2026-10-06|B3|chore(loop): R239——NACRE白皮书v1.0成文轮账`
`e2d516b8|2026-10-06|B3|feat(soul): NACRE 白皮书 v1.0 成文——6章技术+商业计划+metis对照+组织收敛;全文证据三层标注,数字全溯源(骨架正本之成文版)`
`a022c56b|2026-10-06|B3|docs(soul): NACRE 代号用户拍板定案落地——白皮书全文替换+品类锚 judgment-native+中文备选不采用+R211`
`b870b129|2026-10-06|B3|docs(soul): 代号撞名核查定谳[NACRE干净/Gnomon降级(paypal 932star)/Tessera淘汰(tesseract 76827star)]+R210`
`ad6505f2|2026-10-06|B3|feat(soul): 创新模型代号v2批次(NACRE推荐)+Metis对照吸收(Judgment-Native品类)+R208`
`30404705|2026-10-05|B2|feat(语料v1): R169——exporter --v1 模式+v1 重导出验收全绿(空题面52→0+id全同1454+label零漂移+A型11/11全文+f15 8/8+bc1 36/36+t3 8/8+rejudge ctx 500/500);split三折继承id不变(train b1fcf208/dev a9609c9a/test aa8ed4ce);train_set_v1=84277e05e44b77c3(jsonl不入仓同v0口径,实物+sha留档manifest_v1);t3伪映射撤除(blind_pack rows正源);A型复评待GPU拍板`
`d4fe8d7c|2026-10-05|B3|feat(语料复核): R168 both_wrong 14条人工复核——两缺陷实锤:①response[:200]入库截断砍掉boxed结论段(11/14主因,gold依据不可见于判读输入)②字段映射缺口52/1454(3.6%无题面盲判,bc1/f15/t3原生结构未映射);修复建议三条带验收判据;U5判读维持有效,语料v1重导出后重对拍=14B记档具体路径`
`e3351aec|2026-10-05|B3|feat(14B·U5对账): R167分歧对账——错误方向不对称实测(14B错杀侧23例vs 1.7B错放侧10例危险侧)+both_wrong共同盲区14条(lme族聚集);判读不变(一致率口径现役胜);upgrade_path追补两条`
`a2525b4b|2026-10-05|B3|feat(14B升格执行): U1-U4全绿+U5/U6双红负结果照报(14B 0.8664<1.7B现役0.9041,保留现役记档)——核心门PASS/U7如实申报+L1四行全闭环(pusht档挡闸修复APPROVED)+L3回填收窄至v5坐标一项`
`eddd14d7|2026-10-05|B2|feat(14B升格): U1-U7训练脚本落盘(smoke同构+292条held-out同集对拍+qid零相交门)+预注册档开跑坐标回填(U1语料1162/sha16三件对上+U5复核集核对结果如实记=dev+test,勘误沉淀构成无实物不臆造)`
`03f89399|2026-10-04|B2|feat(判官升级·人类轨): calib60汇总κ脚本——Cohen's kappa双读数对表(dim2对3B/7B)+分歧题归因清单三类;假作答冒烟κ=1.0通路验证`
`dedb6fba|2026-10-04|B2|feat(判官升级7B): 验收③OOD 400题补跑闭环——三态全非零(未动172/部分226/完成2,完成帧在OOD出现反证主包0=材料属性)+pos/neg与dim1内部自洽(2完成恰对2 neg否)+dim2翻转幅度大于主包(3B正常332→7B仅5保持,OOD失配更普遍);四条预注册全闭环带注,终判仍待人类标定`
`64fdc014|2026-10-04|B2|chore(loop): R118——#2935 v5 B案处置(回函2939+端点探活未通如实记)+判官升级7B首跑验收档+XERJ recipe还账发出(1a105de8ee3db98e)`
`b98aeddc|2026-10-04|B2|feat(判官升级7B): 首跑验收——主包498题283s(dim1方差0→非零:部分356/未动142/完成0=材料p35p80无完成帧属性)+dim2系统性翻转归因(画面-进度标称一致性严格执行,判据二义点浮出=人类标定第一题)+pos/neg自洽修复;判据PROMPT零改动换模即用;验收③OOD补跑挂下窗`
`85503049|2026-10-04|B2|docs(判官升级备料): R106——E1·J2 3B→7B+/人类抽检标定预备档(六轮失败模式F1-F5+7B需求档+标定协议草案);G1/turbo触发核查均不触发;A100空闲无合格任务`
`356a93b5|2026-10-04|B3|feat(P3/E1): R96——exp2六件收割(预注册第二分支:重训无增益坐实,epochs↑有害/lr信号不显著/loss低者读数差=P3增量设计三重反向实证)+E1判读排障三连全通(v5无AutoProcessor换openpi venv/路径两代glob/replace自毁项删)后OOM排队(flywheel gen4_v1会签生产件29.7G不动)`
`9d259ced|2026-10-03|B3|feat(组织机制A1+A2落地): remote.py四命令工具(通道坑/限流退避内置)+frame_autosync.py(FRAME自动派生防停摆)+A案首吸收delta_0003(4条入燃料/6条门拒留痕=2667裁决首执行,语料池33);三信处置:E1坐标收讫/M1批次二公钥回函2691/A案回执2692;R90轮次日志`
`10e09753|2026-10-03|B3|feat(p3因果倒置线): exp1 challenger v2 全量重训实验发车(A100 1162条+champion热启动,预注册实验判据不入岗)+launch通道坑修+paper3《验证前置:因果倒置的验证机构》立项稿(六段证据映射全现成);R88轮次日志`
`3e3e207a|2026-10-03|B1|feat(L2协议会签): case_spec×verdict_schema_v2 映射表落档+verdict v2.1 加 peer_case_spec 双向引用字段+会签函发 flywheel——两schema同构实证(定义侧/结果侧),判据棘轮互认(frozen_file sha入freeze_chain)+止损线贯通(rule前置→布尔判定)+gen4_v1 出首份互操作样板;协同机制从函件约定升级为字段约束`
`387fae02|2026-10-03|B2|docs(theory): 前沿对照调研档——因果倒置四句同一性锚+学界2026四活跃点对照(LLM-judge校准/PRM过程监督/LoRA遗忘/具身验证闭环=真空位)+五条解决方案落位(转换器对齐PRM格式/jev-trust上conformal/偏差地图组织版/正交子空间双保险/五框分工)+论文谱系校准(paper3=验证前置方法制度侧);学界状态标[实测·二手],引用前读原文`
`1aaea6b0|2026-10-03|B3|feat(p3+p4): J8 热路径装载申报+P4 判据预注册(起草未发送:shadow fail-open/一致率≥90%/false-fail≤5%/时延≤50ms 三门+装载三步串行)+G1/pusht 五演签名语料 delta_0001(14 条全 independent_recompute:pass7/U5/fail2,锚件 sha256 三件套+函 2407/2422/2459/2464 锚);P3 ledger cycle1=SKIP(14<200 不攒人情;门槛现实性校准数据到手:五演=14 条/轮);ledger 用 .json 承仓 *.jsonl 忽略策略,设计档同步改`
`738e67d8|2026-10-02|B3|feat(outreach): 死线三函清+判官招募赶发——2335 三问回函(id 2339:BGE 自举 82.94% 实证/JEV choice 含 U 两层/SFT 2289 够首批);2332 判官招募 org compass issue #1 双语帖(E1 人类席 J2 23:59 死线+任务市场 ¥65/席),回执 id 2348;pub.py/dev.to 不在场管道如实报`
`ebad8d47|2026-10-02|B3|docs(report3): 配图两张——三门判分架构图(语料→判分器→三态输出+预注册判据框)与 U 态对比示意(二值错误伪装 vs 三态 U 池显式化);XML 语法验证过,图引插入总装件 §1/锚点段`
`5926c357|2026-10-01|B3|docs(research): ThinkPRM深挖档(论文三引用位)——TMLR/149引/DeepMind+UMich;六维对照表:verbalized step reward vs verbalizer三态同族异构/8K样本哲学互证/我们增量=U态校准+热路径生产/teacher独立性(可复算规则vs大模型);四条可借鉴(验证CoT可选层v0.5/步分结论分离/best-of-N判定/MC步标签候选)+边界三条(域不同/1.7B延迟预算/后续RPM-MCTS挂账增量检索)`
`52a8dbe3|2026-10-01|B3|feat(loop-r11): 1993回执(30min件已毕G1勿等)+1995流水线三问(工位对号/三件缺口表/真值层T1T2T3三级质疑=1454语料实证)+探针基线修(gh评论增量报,两次虚惊根因)`
`3c203453|2026-10-01|B3|feat(outreach+metering): 外联首转化!gtaras7/typesafe-jev Issue#2正面回应(Yes with one change of shape)——40种子CV+manifest意图+公开policy,强制caveat;我方已回(承诺48h key/本周报告,协议=corpus sha先锁+key先于模型commit+全工件);预注册立项档落(c304f878800b1fcb冻结/K1-K7判据/caveat挂顶/我方失败史披露段);40/40 CV文本抽取全绿归档;🔴设计发现:key可锚定面=仅客观字段,六判断维度大半U+flag泄漏率副读数(年龄/性别/军役泄进score=对gtaras7最有用产出);探针修漏监(gh notifications兜底,typesafe-jev#2漏看半天教训)`
`febaeace|2026-10-01|B3|feat(outreach): 两封重要回信处理——①XERJ/Ivan(参考编码语料创始人看我commit主动邀约):应下贡献三件套(带复现issues/hybrid-scoring小PR/llms.txt实测反馈)+一次性offer第三方复算其11/16vs16/16数字(生态嵌入线首弹,playbook开源贡献式营销实弹位) ②Infistar跟进函:四条款框架回复(中性位/实测先行30天J1-J7/独立性披露/资质前置三项材料,承9/30定案);台账记4/5两件`
`55f06a9c|2026-10-01|B2|docs(report3): Trust Report#3大纲+§1成文(主线回归)——判分器自纠错叙事全链(66.2%起点/三作弊通道故事/LoRA三态/88.51%读数表/U态方法论锚点);语料活水修正:E5 33条不进判分语料(门级判定≠答案判分,实测verdicts全pass,硬塞=污染——真源=unlabelled 47+errata gold+判官金标);Reddit CDP配方失败收兵(稿+五坑全留runtime/marketing/,shadow多层/MD切换清空/多实例/navigate重连/busy死通道)`
`2a77ff21|2026-10-01|B3|docs(runbook): 判分器定期重训Runbook备就(用户9/30批机制·10/1落档)——触发三条件(errata gold≥50条/双周/线上抽检退化)+固定规矩(申报→判据预注册→原样读数)+A100现成环境实测档(sha256三折对上/模型scope缓存/v5 E6共用纪律:GRPO在跑绝不抢GPU)+语料活水五源管道表+命令速查`
`4b5d503b|2026-09-30|B2|docs(goals): 判分器定期重训机制常设化(用户9/30批)——节奏=errata gold≥50条或双周一训,规矩=先申报/先判据/后动手;与v5(agent框)/flywheel(飞轮框)融合(语料活水=飞轮产出+errata gold,判分器输出=v5三门判定);A100 40G训练机备妥(.cache/gpu_a100.env,环境全套现成,torch2.6+tf4.57.6+语料+脚本)`
`8f950ce6|2026-09-30|B2|feat(p2v2): P2北极星达成——verdict-judge LoRA训练三门全绿(J1 test二值88.51%≥85%/J2 ECE 0.072≤0.10/J7 v1+22.3pt≥+10pt/J5 sha三项PASS;dev曲线0.867→0.916→0.881早停ep5无硬过拟合)——Qwen3-1.7B QLoRA r16 verbalizer三态,训练~1h;产物拉回验证(adapter 25.7MB)后实例673881用后即释(退款2.03,API层原子释放绕开CLI _redact遮罩approval_token坑);宪章J8申报函1829已发(数据+逻辑70%compass/算力30%组织);下载排障录:HF/hf-mirror大文件系统性断流→modelscope通道;P2判分器≥85%目标达成,下一步=装记忆写入热路径评估(装前另行申报)`
`51d8b62a|2026-09-30|B2|feat(outreach): GitHub+Gmail双通道外联两件——①mem0 issue#7514(双锚:三臂实证16/11/18先给+修复建议,DolphinBench判分协议公开性问+免费复算offer,同#2440模式;仓内工件先push防死链) ②TypeSafe Gmail(hello@typesafe.ai官网一手邮箱:公开分析知会+完整回应权+免费复算,M1直接转化件);LEDGER记三件待发池更新;LoRA训练HF下载中断修复(进程死75%/3 incomplete,重试x5+断点续传脚本重启,监控b028odggm);纪律:Latent Space周期内不催(9/28投稿,1-2周窗)`
`acc37f57|2026-09-30|B2|feat(p2v2+x+w42): 三线落地——①X长文稿已发(TypeSafe proof弹药,status/2105296550117458093,profile首条44秒实证;x_post.py修:tweetButtonInline才是发帖钮) ②P2v2 LoRA训练启动(实例673881 js2:15124 4090/48G空闲,transformers 4.46.3不支持Qwen3已升4.57.6,split sha三项+行数1162/143/149全对预注册;一条龙setsid后台,监控b58pxgekt) ③W42 writeback通路a执行(v5#1702纠错=端点该平台出,数据包全文发platform函1814,deadline 10/2);GOALS账本四更新(G2重放135/135闭环/flywheel GPU解/glm解/W42状态);余额红灯自证伪(PowerMoney≠Money,实测147.85到账)`
`77bafc2a|2026-09-30|B2|feat(p2v2+outreach): 用户三令落地——①LoRA训练脚本verbalizer三态版+GPU实例实测恢复(4090 48G空闲,lyg1051 js2:15124,paramiko通道)+远端pip后台部署+三折数据已上传 ②持续外联战略档(常设线:九渠道资产盘点/精准匹配三原则/首批主动出击清单=mem0 OmniMemEval复算协作+Letta Evals协议互补+上游LongMemEval合作姿态;loop常驻化+OUTREACH_LEDGER记账);zhipu coding key在位(zhipu_coding_key.env)`
`33205cc9|2026-09-30|B2|feat(p2v2): LoRA立项就绪·卡点=GPU余额——实查余额1.9元不足(4090×2-3h需3.3-5元);保留盘快照在(46实例含9/3全套环境copy,零重部署);方案=Qwen3-1.7B QLoRA r16三态verbalizer+split冻结不变+无作弊通道输入;J7新增v1/v2同split对照(v2≥66.2%+10pt);J8宪章事前申报(数据+逻辑70%/算力30%);充值10-20元即跑,全流程约3h`
`0a10d64e|2026-09-30|B1|docs(goals+mailbox): 1776宪章回函1779(无异议+verdict语料1454申报数据类资产+两建议:验证数据归入数据40%口径/入池模型版本披露可查)+GOALS晚补记账(P1达标三连/P2基线闭环/信箱1760·1763·1776全清);今日记忆提炼两条入档(judge-corpus-p2-baseline/daemon-v32-rootcure)`
`f9f5ecf1|2026-09-30|B2|feat(p2): verdict-judge基线首跑+特征证伪重设计——v1(64.9%FAIL)诊断:sample_text含judge_output=被检判分器自报作弊通道(判分器本意从工件独立判对),剔除重跑v2:J1=66.2%仍FAIL但J2 ECE=0.045 PASS+U态探索1/1命中;定谳=架构天花板(冻结bge-m3+线性头≈语义匹配,>随机50%/>多数类52%但距85%为架构差,v2路线Laya头LoRA需GPU);判据零放宽,test仅两次原则性设计差异非调参;首跑读数存档eval_report_v1_failing;P2v1地板建立`
`0c1b2070|2026-09-30|B2|feat(corpus): exporter v1.3——LME-V2 d12/d14官方harness明细入库(labelled 552→1454)——四run 902条(d12 web240/ent211+d14 web240/ent211),真值=官方answer_gold+透明eval_function机械判定(规则代码可复算,非LLM judge自报;d14复核探针三陷阱加持该层),pass345/fail557如实;is_abstention/is_unknown入artifact备abstention gate族细分;1763已ack(v5分级落地gold/silver/bronze与我们label_origin对齐)`
`078d6050|2026-09-30|B2|feat(corpus): rejudge 500题双层复算双绿→P1达标(labelled 52→552,目标500超52)——预注册判据档先行(REJUDGE_RECOMPUTE_PREREG);探针证伪两连:M2子串规则13.8%冲突全为等价改写误伤(five≠5/人称/括号三实例定性→判据档append修正M2入抽样池,J1只用零误伤M1);J1=0/85数值零冲突PASS;J2=48/50=96%隔离子进程盲判PASS(三次形态演化:32K秒退→agent自主全判盲仅声明级→隔离目录物理盲);分歧2条partial口径入勘误库;11独立incorrect含7超时一致;J6 raw原样存档;500题升labelled(label_origin=官方truth+双层复算)`
`b500bd39|2026-09-30|B2|feat(corpus+mailbox): 1760回函合流+exporter v1.2双源入库+judge自报证伪——①v5第四原语(挑战窗90天+errata登记处18890)独立验证过(open=[]协议对/challenges 2行+errata 1行逐行核)后回函1762:SLA八项并入挑战窗接受+fail/U附challenge URL+recomputer分级建议(gold/silver/bronze);②arm-a重判500题证伪:is_correct=_parse_judge(judge_raw)=judge开卷自报复写非独立真值,500/500'一致'仅同源复写→诚实进unlabelled(judge-self-reported族),升labelled条件=非实现者抽样≥10%复算——差点虚报P1达标552,红线拦下;③errata smoke件入库(smoke族,真实第三方errata才是labelled活水=P3供给线);labelled 52不变/unlabelled 547`
`4f0254a8|2026-09-30|B1|feat(corpus): exporter v1.1——T3盲评真值+e5三门判分入库(labelled 44→52/unlabelled 13→46)——T3三层样本族(交付判分vs独立盲评只读blind_pack vs复算RED勘误):5行y_circ/d_depth+3 findings系统性错误(422格式bug/标尺0-4vs1-5错位/noul误拒)=外部首单完整判绩账;e5 33题自动判分诚实进unlabelled(无人工对照不冒充真值);距500差448`
`928f9df6|2026-09-30|B2|feat(corpus): exporter v1——BC1 成绩单逐题标签入库(labelled 8→44)——v1 十八题实际被考题号取 answers 键(首版误用 decision_set 全30题含 holdout 12 未考,自查抓出错标已修+18题硬校验中止闸);truth分布 13pass+5insufficient_evidence 与审计逐题吻合(T12×2 真值错误→考生对=判分器被坏真值骗的教学金矿/T11×3+T31×2 歧义→应判U);v2 重考18/18 反向归因样本;距 P1 目标500 差456(v2 增量源:三门真题库+T3 findings)`
`7cff5988|2026-09-30|B2|feat(daemon+corpus): 双线并行落地——①v3.2根治patch四刀全下(numpy float32化(cosine np路径/encode返ndarray/entry+chunk惰性转换旧pkl)+向量预算制300k(OrderedDict访问序LRU替代MAX_PROJ=8硬逐=churn根因)+listen前置warmup后台化(load锁防并发重载)+MSG_PEEK豁免上云;单测5/5绿:cosine等价1e-6/惰性转换/预算逐出访问序/pickle往返;蓝绿部署等10/1 08:53读数后窗口) ②SSI×Jev P1语料聚合器v0(tools/verdict_corpus_exporter.py:F15两格式宽容解析compass三态=真值;labelled=8/unlabelled=13如实报数距500差492;v1 backlog=BC1 scorecard逐题标签+T3 findings+rejudge勘误);产物runtime/verdict_corpus/带manifest可溯源`
`c92d25ea|2026-09-28|B2|docs(strategy): 权重自进化环立项(用户令,三框征议)——三层(现役文件/学生qwen+LoRA本月/性格CPT远期)/五件套咬合(燃料=签名verdict语料/选择压=周榜/双通道阀门/jev小脑外置/技能事实分离)/三护栏(分离/影子考试/自动回滚)/反自指护栏升格为带裁判自进化/三段算力诚实账(从头挂M1-M3后)/Phase1五判据挂10月首圈;用户亲任L3终裁;函三框`
`cb54cc0a|2026-09-25|B3|feat(eval): 向量对拍——bge-m3 vs Qwen3-Embedding-0.6B 自家记忆语料(109档×218查询):主指标recall@5差0.46pt=平局不换,recall@1/中文切片现役反优+2.75pt;预注册判据先行,天花板效应已披露`
`346b06fe|2026-09-24|B3|chore(fuel-pool): pending→expired 归档收口——8月垂域燃料过生命周期(磁盘 expired/ 1769 文件在档,pending 旧位置 git 历史可溯);_tmp 会话清单文件随删`
`0791888a|2026-09-22|B3|docs(plans): Assay-Head立项——Jev吸收线A终局件:0.6B级Jev式判分头(三态+校准+第四输出can_judge=NC架构化);五反自指红线(只训小判分器/签名语料/自校准用自家判据/2000行+M2门槛/禁直接自评);三阶段(Phase0零样本hosted Jev本周可做→Phase1 SFT→Phase2 RLCD成本不对称→Phase3在线);语料盘点58行→攒至2000;ECE≤0.05上线门;商业闭环=判分吞吐×1000+校准报告即DCR`
`988c1782|2026-09-20|B3|docs(strategy): LE剧本解剖×AI信任基础设施路线——纠三误(赢在自动化非免费/默认态反转是浏览器做的/90天续期=连续验证)+五要件逐件映射(✓自举比LE强:回执自验证不需要跨界签名;✗两断裂:语义验证只走机械子集+无浏览器垄断渠道)+两档制商业模式(自证免费永久=基础设施/独立验证+墙+TTL续验=付费层)+Jev双角色(决策头扩大可验证面=扩张器;我们的判分器也长Jev形=吃狗粮到架构层)+最值钱收敛:LE续期循环↔订阅是同一结构(信任是连续量);五门槛现状与动作;执行序全接既有件零新实体`
`8570721f|2026-09-19|B1|feat(protocol): Assay Protocol v0 公开+独立验签 CLI——协议一页(判据注册棘轮j=(m,τ,D)/验证包/三态回执/墙纪律/验证者纪律I3盲判/L-1..L-2合分级;文本CC-BY,任何人可实现,我方=参考实现非所有者);verify_receipt.py 单文件纯python ed25519(零依赖可外部拷贝,'验证的验证免费'落地);双成绩单独立验签均VALID(两套实现互证=裁判也被验);README墙段增验签一条命令`
`bd1098b8|2026-09-18|B3|docs(benchmarks): Assay BC1出题框架v0——四维×30题:每题型绑定判法(VerifyPack check kind)+判据显式引用(criteria_ref进语料);种子全取真实史(自置标志/假绿双案/锚池偏差/47-47/skip失真等);防自证三护栏(程序化参数化/非实现者跑分/40%hold-out);λ 9/24冻结,9/27交付`
`90b54cd1|2026-09-17|B3|feat(verifypack): export 子命令——verdict 语料导出器(燃料层第一铲,SPEC §11)。一行=一条 claim-verdict(trace/claim_id/criteria_ref/payload_hash/verdict/signed_at/pubkey_fp 全锚);criteria_ref 从声明正文提取(锚引用纪律);行内零时间戳=确定性可再生(jsonl 不入仓,sha256 即锚);未验签如实标 None;TDD 四用例(签名/无签/缺回执/确定性),verifypack 61/61 绿。修 cli 缺省公钥半残洞(check 同款隐患):env 缺失时回退 .verifypack/compass.pub。首份实弹语料:c_family_b1 6 行,sig ✓,sha256 b8b617156171e528…(本地 runtime/verifypack/corpus/)`
`36d256fc|2026-09-17|B1|docs(theory): T4棘轮按platform 319精化案重写——判据三元组j=(m,τ,D),修订合法⇔ρ不降+Δτ带证据链+D只增;棘轮锁测量诚实度ρ非标准松紧τ(旧表述会误判sim50-001 v0.2→v0.3合法修订);预注册重述为冻结首轮三元组`
`9284fee5|2026-09-16|B1|docs(theory): 验证机构算子代数——三态=偏函数求值/棘轮=序/RRF 尺度不变/漂移 margin 判别/七判据分类学(纯度分级)+机构级命题 T1-T7(分离/熵零/零裁量/单调/检验/胶囊/反自指)+verdict 语料监督分布数学+代码级缺口盘点;全部锚到仓内实物函数`
`03fcc09e|2026-09-16|B3|docs(strategy): RSI 浪潮深度启示——动态模型时代验证机构论+verdict 语料涡轮论+自训判分器带牙齿方案(反自指护栏)+三机制收费映射;全挂 M1 闸门后`
`356eda0b|2026-09-09|B3|docs(plans): 夜巡轮9——2600 语料定位报告(出处=paper2 正文·记录不在活跃仓·恢复两路留拍板·定位报告已投 flywheel)`
`3e7d4a58|2026-09-09|B3|docs(plans): 夜巡轮4——C2 G1 ack(BGE 指纹实测+PROTOCOL 收录+X1-lite+2600 语料独立复核不在公开仓·认领定位)`
`eaf65c16|2026-09-04|B2|docs(营销#33): 第二帖骨架占位符全部填定案值——刀3 LoRA=parity 未采纳(ent +0.46/web -0.03 vs 门+5pt)+刀4 abstention gate 预注册拒收(误拒答 92/89·non-abst web -5题)+LME-S 回归改判 moot(LoRA 未采纳)+X 钩子填 40.0/38.4;剩 cheap-tier 可选回填+evidence 链接终审+用户拍板`
`d06e390d|2026-09-02|B3|feat(N6): CompassMemBench(命名待定)基准发布立项——判分卫生学协议 v0.1 草案(judge 预算≥16384 下限/双口径强制/成绩卡 config 节/程序化判分优先/污染声明,全部源自我们亲踩的坑)+GOAL_SSOT 立 N6 线(T0 发布 9/12 与营销帖合流·T1 四类新题型 9-10 月·T2 训练飞轮 Q4=评测自举论文骨架);查重两连:CompassBench 已被上海AI实验室占用·ATLAS 与李飞飞 World Labs 9/2 发布撞名,均弃;license 初审绿(webarena MIT/ServiceNow CC-BY-4.0 可改编带署名发布)`
`56a44b92|2026-08-31|B2|docs(N5③): README/落地页补 d13 定案口径——LME-V2 行加 LoRA 增强验证持平未采用注记·落地页对比表补 LME-V2 行(36.7/40.3,untuned 19.6/12.8)·失败实验公开句补刀3`
`32dd78f0|2026-08-31|B2|feat(刀3④): d13 judge-retry 定案——双域未过门,刀3 LoRA 路线关闭,d12 检索栈维持现役`
`b151a38b|2026-08-31|B2|feat(刀3④): d13 ent 211 题全量重跑产物拉回固化+652509 退租(退款¥19.57)——RAW ent 0.3081/web 0.283 双落 d12(0.403/0.367)·judge 风暴污染 score0=146/211 定案待离线重判·刀3 LoRA adapter(9.1MB)+训练对/脚本/日志资产入库(merge 模型 base+adapter 可复现未拉)`
`df3b7b88|2026-08-31|B3|docs(验证平台): v1 桥架构定稿(用户拍板)——两条产品线两个数据飞轮中间嫁接融合桥,替换 v0 融合表述·第一性理由=判据不可互换性(V1/V4 与数据层绑定,合池=错层召回+判据错配)·桥=防腐层:过回执/度量对表/配方知识三样,不过原始数据/管道代码/台账·SFT+RL=共同底座非桥·防混杂四机制(分仓/单向依赖/桥头分治/桥流计量)·fuel_pool 重定位=认知侧桥头非共享池`
`1cf76749|2026-08-31|B3|docs(验证平台): 统一验证合同 v0 草案——四套已有验证协议(proof-of-recall/Gate B/qc_gate/独立复算)盘点入册+五步合同 schema(CLAIM/VERIFIER四型/PREREG/DUAL-GATE/VERDICT)+缺口四条+落地路线四步·关键发现=vtf/fuel_pool 已是记忆飞轮与数据飞轮的代码层交汇点·具身 V4 不可仿真性验证器为唯一空位`
`b3c65828|2026-08-31|B2|docs(compass→flywheel): GPU 651799 退租征询回执——勿中断 d13(GPU util 0%=预期非空闲,检索为进程内 CUDA 直载 knife3 LoRA bge-m3,墙钟被 ARK API 主导)·web~02:00/ent~04:00 完成·退租等 compass 信号函`
`ced0ed4b|2026-08-30|B2|feat(N5·刀3): 训练对扩容+LoRA 训练四件套——①semantic_align(cos 判据实测被域差距压顶天花板 0.73,推翻'转述可cos对齐'假设)②llm_weak_label(doubao 绕开 embedder 域差距做弱标注,cos+lexical 双路候选)③train_lmev2_lora(peft r16 只挂 qkv 0.41% 可训·guard recall@5 每 epoch 护栏·最佳 adapter 后统一 merge,管线 10 对冒烟全通 1s/epoch)④merge_pairs(strict g3 去 eval 池+weak YES 合成)——全轨迹 1.2GB 拉回证实 subset 已全覆盖,56 对是精确对齐结构上限,扩对只能走 LLM 弱标注`
`699251ed|2026-08-30|B2|chore(vtf): gpu_ssh 新增 readfile 分支——exec 通道 base64 流下行(绕 blockelite SFTP download 怪癖),配合远端 split 分片拉回 164MB 轨迹 subset 全程 75 秒`
`ffcc5d51|2026-08-27|B3|evidence+docs: M500 全量终裁——P@5 0.888(大语料泛化成立,比 S500 只掉 9pt;ssu 0.20→0.93 全量修复;ssp 0.53 新短板);双版 README 同步`
`f8f6d10b|2026-08-27|B3|docs(ssot): 同步8/28十次增量(SFT关闭/群体自治翼唯一引擎)`
`b418e624|2026-08-26|B3|evidence: 鉴别臂裁决——S 语料上 reranker 是罪魁(no-rerank 0.867=rerank 0.833,ssu 0.60 vs 0.40 唯一翻转);500 全量已切 m3-only 重跑;M 上 rerank 去留待 M 实验定`
`025f8834|2026-08-26|B3|feat(eval): ZMM_RETRIEVE_K 候选池上限可配——K50 在 LongMemEval-S(语料~40 session/题)是无效实验,RRF 只能重排、rerank 抹掉顺序;K20 让 BM25 真正换入榜外候选`
`7a13f80f|2026-08-22|B1|feat(fuel-N2): stop hook 自动提炼燃料入池 + 周批 QC 队列卫生`
`07add59d|2026-08-22|B3|docs(broadcast): fuel-loop 部署闸门闭合通告全框 · 挂链路活合约 cnt_fuel_loop_live_20260822 (due 8/26)`
`55fb09e1|2026-08-22|B3|fix(ops): fuel-loop 探针 grounded 修订(路径/DSN/端口对齐 cloud 真实布局)`
`63face90|2026-08-09|B3|feat(ops): fuel-loop 部署验证探针(部署后端到端独立核查)`
`3fcd8b03|2026-08-07|B3|docs(收敛执法): 闭环收敛唯一闸门=fuel-loop 部署 · compass→codex outbound`
`a3242474|2026-07-21|B3|Consume platform fuel verification result`
`c7d7d620|2026-07-21|B3|docs: add V5 fuel recall replay package`
`b51f0689|2026-07-20|B3|Add fuel trace coverage probe`

## 未归类 U(80 条)

`54cbea0e|2026-10-06|feat: J6落定——10/26需求裁决预注册档(两仪配比裁决/防漂移条款/J7吸收);七窗判断全清`
`8abcbf70|2026-10-02|docs(loop): R33 账——Report#3 总装完成(9025字符,包含性自检5/5)`
`f6b00cb9|2026-10-01|chore: 收轮残留`
`8e4eb421|2026-10-01|fix(key): flag检测词根扩宽(military变体,18/40实标)`
`56633540|2026-09-27|docs(vb): 批1预注册判据档落地——冻结口径+J1-J5判据(零工具病红灯先证伪patch链)+执行坐标(patch 87行/899f2d1/五步跑法),今晚22:00窗;不给预期读数(报数纪律)`
`40090e30|2026-09-26|chore(loop): 轮22——1018 UniPat镜照三问已答(1063):v0缺口四件/标定账×注册表并轨+T7红线/命名Assay;验证基建资本定价铁证入账`
`2df14ba4|2026-09-24|chore(loop): T3 范围双确认入账——对方锁定 5 行全集/n=5 误差带/交付清单零变更`
`482d552a|2026-09-23|chore(loop): L4 ✅ GREEN+两文档小瑕修(27漏口径/三源全集 48-50)+用户面板清零`
`c7b636d6|2026-09-23|chore(loop): 轮7——C1 触达试点 3 家已发,T 表开账`
`b67ad243|2026-09-23|docs: 历史重写声明——全量署名统一为 chunxiaoxx,旧 sha 溯源指引与备份位置`
`ecb745df|2026-09-23|chore(loop): 轮2收轮——L1 ✅+日志(ddbe913)`
`66750d6e|2026-09-23|chore(loop): L1 状态列 15/30(轮1日志已在 822b514)`
`f758defa|2026-09-23|feat(loop): 组织 Loop 系统 V1 正本+LOOP_STATE 账本启动`
`f5bd8b42|2026-09-22|fix(recompute): 三份 session.jsonl 被 .gitignore *.jsonl 静默拦截——强制入库`
`81beaddb|2026-09-22|docs(loop): v4 收官——29轮(实质2+平安27);P8拆除+D2迟发观察;夜间全静默`
`da905617|2026-09-14|docs(rsi): #48 修复与重测记录——J3 全文扫描+J1 写入门 hook(插件仓 d9a47e1)·30 回填+2 规范化·重测四条全绿(J1 100%/J2 三档/J3 严格批量验证/J4 GREEN)·环 #1 闭环`
`a3705e2c|2026-08-29|docs(readme): tools 段更新——17 tools 全景+延迟口径注明(本地 vs 公网 HTTPS 实测 0.9-1.7s)+scoped-token v2.3.1 安全模型段`
`77215016|2026-08-28|fix(eval): utterance context 注入 session 日期(tr 型 e2e 0/5 根因:context 无日期可算)`
`a2527872|2026-08-28|feat(eval): --end 分片参数(500 全量 e2e 4 shards 并行)`
`7bb3e6f6|2026-08-27|feat(lmev2): compass Memory 后端适配 LongMemEval-V2(官方接口 insert/query 黑盒契约)+smoke 脚本+营销第一帖文案`
`6c4419ba|2026-08-27|feat(eval): ZMM_LOAD_RERANKER 解耦——cross-encoder 仅供 utterance context 重排,不进 session 检索排序(检索段 rerank 有害已证);context 弹药完整形态可挂`
`b0040226|2026-08-27|docs(readme): Headline 表残留 0.876 补修至 v4 口径(0.890/0.978/0.929)`
`0dbc175d|2026-08-27|docs(readme-zh): 中文版全面重构同步英文新版——三柱架构/utt SOTA 检索叙事/快速开始四路径/真账面最新口径(0.876/0.976/0.919+LOCOMO 反超)/历史折叠;修掉 v2.3 时代'-30pt 代价'旧叙事与旧 badge`
`21d617ac|2026-08-27|docs(readme): 主数字升至三型终裁口径(P@1 0.876/P@5 0.976/MRR 0.919,+10.2/+6.0/+8.5pt)+badge 97.6%`
`35ef078a|2026-08-27|evidence: S500 三型终裁——碾压再扩大(P@1 0.876/P@5 0.976/MRR 0.919,+10.2/+6.0/+8.5pt),ku 0.79→0.97 全量兑现;剩余尾巴 temporal/ssp/ssa`
`c8dba227|2026-08-27|feat(eval): LOCOMO utterance 块检索适配(ZMM_LOCOMO_UTTERANCE)——双 speaker 每 turn 锚 window-2 块,best-chunk 排 session,与 LongMemEval 同弹药逻辑`
`51409e70|2026-08-27|feat(eval): ZMM_UTTERANCE_TYPES 分型路由——CPU 预算下 utterance 只打短板型(ssu/ssp),满分型留在 session 级;块嵌入 15x 于 session 嵌入`
`f7d3b7f7|2026-08-27|feat(eval): ZMM_UTTERANCE_RETRIEVE utterance 窗口块检索——session 按 best-chunk 排名,解 ssu/ssp 深度召回(S 0.60/M 0.20 短板;答案藏在单 user turn,session 全文稀释);纯 dense,hybrid/rerank 分支隔离`
`2e6856f0|2026-08-26|feat(eval): ZMM_QUERY_INSTRUCT query 侧前缀开关——Qwen3-Embedding 换装实验用(官方检索模板自动默认;BM25/rerank 侧保持原文,前缀只进 bi-encoder)`
`0a5908c0|2026-08-26|evidence: bench_all l0 首跑记分卡(recall P@1 0.972/MRR 0.982 · drift AUC 0.9232)`
`d31acafe|2026-08-25|docs(publish): X 渠道帖稿(等新 X_OAUTH2 token)`
`f50affe0|2026-08-24|docs(broadcast): 回诊平台——云桥握手根因=顶层 _eid 非法字段,修复 fe8a0c3 已复现验证,请同步重试`
`97cd3248|2026-08-23|docs(broadcast): compass v3.0 三框升级通告——共享层已自动到位,各框仅需重启+一次 ingest 验收`
`ae520596|2026-08-23|docs(gtm): V3.1-B 第一脚博文草稿——记忆有用性对照实验对外叙事(真实数据/含两个伤人发现/n=3 诚实披露/负对照)· 红线自查过 · published:false 待用户过目`
`53e0554a|2026-08-23|release(v3.0.0): 从记忆库到进化引擎 · 版本号/CHANGELOG/继承债`
`c0f304f0|2026-08-23|docs(goal): N1/N4 状态同步实况(心跳自愈已上线·云三根因已杀)`
`7a3f927f|2026-08-22|feat(goalmode): 目标模式账本 + 每小时心跳执法(系统化持续推动)`
`9b7da650|2026-08-22|feat(exp): recall 有用性对照实验 · 首次外部证据 delta=1 + 语义 recall 复活`
`20cf11b8|2026-08-22|feat(gate-b): d2 真燃料 spec(id-preserve 语义 oracle · 4 案例含幂等/防id复用)· 三跑实证 headroom 不稳定`
`2441386f|2026-08-22|feat(gate-b): v1 真燃料 spec + thinking-block 解析修复 · 双真燃料实测均 delta=0`
`482999ec|2026-08-22|docs(task): 胶囊消费端接线任务书(Gold candidate→capsule→recall 注入+生效验证 · 对标持续学习方向的上游卡位)`
`df19d122|2026-08-22|docs(broadcast): 首次 Gold 里程碑通告全框(verify rc=0 · delta=1 · b962f52)`
`c09f9e98|2026-08-22|docs(task): 追记首次 Gold 实录(b962f52 · delta=1 · verify rc=0)`
`d685e41d|2026-08-22|docs(task): S4 收敛+Gate B 解封执行结果 · v2.4.0 · live 4 跑 0 Gold(措辞序/隐含变量契约)· 修 UA 已推`
`b0a7d08f|2026-08-22|fix(provider): _urllib_post 显式 User-Agent(GLM 代理前置 Cloudflare 拒 python-urllib 默认 UA · HTTP 403 code1010 · curl 同源实证)`
`02e37006|2026-08-22|merge: codex/compass-dogfood-mvp into compass/convergence-enforcement-20260707 (S4 收敛 · dogfood learning loop 回归主干)`
`6818aeda|2026-08-22|docs(task): 下一任务书 · S4 收敛 + Gate B 解封(递归闭环第③环第一次叩门)`
`edac1679|2026-08-22|docs(broadcast): 统筹快照 8/22 晚 · B=0→1(链路活 PASS 核销)· 各框下一件事 · 统筹基建合约已挂`
`f09ab3a1|2026-08-15|feat(loop): add bounded direct GLM transport`
`c8b5d846|2026-08-15|feat(loop): add sealed Gate B reserve suite`
`fca3d711|2026-08-15|fix(loop): stop Gate B after unusable source evidence`
`61319efe|2026-08-15|feat(loop): add bounded Gate B live evidence path`
`1e389469|2026-08-15|feat(cli): expose the Compass learning loop`
`99b42907|2026-08-15|feat(loop): add reproducible run-local learning loop`
`83f8fcea|2026-08-01|feat(s4): enforce independent verdict admission`
`f8370364|2026-08-01|fix(s4): validate persisted v2 event rows`
`29529b12|2026-08-01|feat(s4): admit verdict event envelopes`
`60f6e7bc|2026-08-15|feat(cli): add honest Compass doctor`
`4cc4ccff|2026-08-15|docs(compass): plan dogfood MVP rescue`
`ce1c7ccb|2026-08-15|docs(compass): define dogfood MVP rescue`
`01dda768|2026-08-06|docs(收敛执法): 8/7 codex 20 天全面审查 + income 停滞根因`
`26acdcde|2026-08-01|Merge pull request #52 from chunxiaoxx/codex/pr-s4-2-harness-envelope-journal`
`25dd811b|2026-08-01|fix(s4): make quarantine records append-only`
`2621ddf2|2026-07-31|feat(s4): add deterministic harness and episode reducer`
`a5999b06|2026-07-31|fix(s4): make quarantine fingerprints deterministic`
`38cda2b8|2026-07-31|fix(s4): preserve types in quarantine fingerprints`
`300f9d55|2026-07-22|docs(fde): record Phase 3 Bitable stop condition`
`41c7e7a5|2026-07-21|docs: stamp C6 recall policy evidence`
`bcaee4dc|2026-07-21|chore: add routed recall policy candidate`
`629e6f91|2026-07-21|docs: stamp C5 recall policy evidence`
`73f16179|2026-07-21|chore: feed development outcomes into recall policy gate`
`e05eef5a|2026-07-21|chore: add release recall policy preflight`
`cdd00037|2026-07-21|chore: enforce guarded lifecycle recall default`
`e3faa432|2026-07-21|chore: add paired recall policy gate`
`8fff3c0b|2026-07-21|chore: gate sparse lifecycle signals in recall eval`
`76df9297|2026-07-20|chore: solidify compass benchmark mainline`
`2fe94ce4|2026-07-20|chore: harden Compass eval entrypoint python resolver for 3.10+`
`d27ce703|2026-07-20|chore: redact exposed API keys in PR49 review artifacts`
`2fb66cc9|2026-07-17|fix(bmb): 提交前对照买方文档全面审查 + 修正 5 处(正式交付就绪)`
`145a95f9|2026-07-16|feat(bmb): BioMysteryBench P1 端到端跑通 VCF→变异临床意义模板`

## 关键词命中分布(供存疑审计)

- A: 题×118, 复算×92, 判分×86, 判读×73, judge×49, launch×19, 审计×17, 判官×14
- B: 语料×44, fuel×20, NACRE×20, 8B×14, corpus×12, LoRA×11, 1.7B×8, ORG-FUEL×7
- C: daemon×25, 值守×12, 探针×11, memx×7, 夜巡×7, GPU×6, probe×6, MCP×6
- D: outreach×32, marketing×20, README×18, 发布×14, dev.to×12, bc1×6, awesome×6, BC1×5
- E: 函×78, ssot×28, flywheel×21, ack×21, v5×10, platform×10, sync×10, 信箱×9
- F: paper×24, mem0×19, E1×19, jev×18, 基线×13, Jev×12, LME×12, PRECOR×11
- G: R###×12, anchor×5, 战略×4, 复盘×4, log×4, 教训×3, 记账×3, 拍板×2
- U: ×80