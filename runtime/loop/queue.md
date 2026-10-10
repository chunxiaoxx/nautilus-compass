# LOOP QUEUE · 活跃轮次记录(R433 起 · R459 归档 v2)

> 本档=活跃轮次(R433 起);更早轮次(R300-R432)见 queue_archive_20261010.md(含 R300 前指针);
> 最早历史(队列 v1 时代)见 runtime/loop/queue_archive_20261009.md。
> 每轮格式:### R<编号> · 日期(主件轮:标题)——正文要点;完成后 commit+push。

### R433 · 2026-10-09 深夜(新会话开工+终检预演复跑✅13/13 全绿[实测]——死线带核对:冲正/RFC 已闭)
- **主件=终检 13 项预演复跑**(10-11 正日钦点任务):`runtime/loop/final_check.py` 复跑 **13 PASS / 0 WARN / 0 FAIL**[实测],输出含活数据实证(语料计数活值+判读 API 卡清单 demo/l1-0001~0003 四卡在列)——预演维持全绿,10-11 正日一键就绪。
- **死线带核对(新会话开局)**:冲正复读=已销案(A3 201 自纠+8 已还)/RFC 表决=已直交 10836(R428)——两项闭环;10-11 终检=预演绿;10-12 开业=轨道上。
- **信箱收割**:零新函;#10829 已 ack(注 10836 坐标请平台核对)。**probe**:daemon 9876 pong 绿+凭据在位+HEAD 0eeed811。
- 积压清单顺次核对:XERJ 捐赠包(#1255 MERGED)/M5 移植部署(已上生产)/mem0 评估(docs/outreach 立档)/语料 2000 冲刺(2258 超标)——已完成项跳过;下一候选=registry 活数据页/判读卡状态页(终检已含其探活,内容充实另议)。

### R434 · 2026-10-09 晚(主件轮:registry 字段错位 bug 修复✅+源分布活渲染上线[实测]——终检渲染判据防回归+data 站改版发现通报)
- **主件=registry/语料状态活数据页(用户点名重做)**:线上渲染实测抓到实锤 bug——`upd()` 直读 `m.org_fuel/m.letters/m.delta/m.updated`,而 `/corpus_stats.json` 正本 schema(tools/corpus_pipeline.py)只有 `counts_by_source` 明细无聚合键 → **fetch 成功路径三 tile 渲染 undefined**,被无渲染口径的终检 13/13 绿掩盖;FALLBACK `delta:32` 亦过期(六 delta 文件合计=62)。
- **修复[实测线上]**:upd() 改 counts_by_source 前端聚合(org_fuel=四子源和=802 与旧 FALLBACK 互印/letters/delta=前缀和)+新增源分布 13 行活渲染表(降序)+dups/7B 缺口展示;FALLBACK 同步 62 口径;本地 file:// 冒烟(无 undefined/16 code 节点)→scp+sudo cp 部署(R366 蓝绿配方)→**线上 Chrome 渲染 6904B:无 undefined+13 源全渲染+sha/2258 全锚**。
- **终检加渲染防回归判据**:RENDER_POINTS 增 registry 渲染项(锚=split_train_v1+sha16,undefined bug 连带使其缺失)——首跑 PASS 7021B;快检 13 项维持全绿。
- **附带·信箱收割**:10862 平台实质回执(nginx 止血今夜窗+应用层入 #10856 白窗 10/11+72h 宽限 10/14 收紧+逐函实质回话承诺)已 ack;第四条候我方件=e2e 真签测试坐标(#10853 余项考古无果,函件 body 无存档,候下轮向平台函询原文口径)。
- **附带·新发现通报**:终检 data 站渲染 FAIL 4,542B(10/8 深验 35,093B 实证页→「智涌飞轮」营销壳,稳定复现非瞬断)=**flywheel 改版跨框资产变更**;判据不擅改(零放宽),函 10867 通报请其 10/10 22:00 前确认(改版预期?实证内容去留?判据重锚两路任选);未回则正日标 PENDING-EXTERNAL 不阻塞开业物。
- 教训两枚:管道吃 exit code 复现(`py|tail; $?`=tail 码,exit=2 真码靠重跑无管道拿);活数据页终检必带渲染口径(内容锚+JSON 判据双层均抓不到 undefined 级 bug)。

### R435 · 2026-10-09 晚二(用户令·T5 recall 节流重做✅[实测三连]——TDD 12绿+生产 hook 链三态验证+失效 WIP stash 清账)
- **主件=T5 recall 注入节流(R432 重做方案落地)**:节流闸最前置 main()——窗口内**零输出直接 return**(不捕获/不重定向 stdout,R432 转义地狱根因规避);session_id(.stdin JSON)为键,默认 10min 窗,`COMPASS_THROTTLE_MIN` 可调(0=关);fail-open(无 session_id/状态损坏/闸异常→一律放行注入,节流器绝不成为注入单点);状态文件 `~/.cache/compass_hook_throttle/<sid>.json`+TTL 48h 顺手清。
- **stdin 单读缓存**:新增 `_read_stdin_json_cached()`,main 闸与 `read_user_prompt_from_stdin()` 共享同一次 read(stdin 流读一次即耗尽,不缓存则闸先读后 main 拿空)。
- **TDD[实测]**:tests/test_recall_throttle.py 12 用例先 RED(12 failed)→实现→**GREEN 12 passed**;全量回归相关 31 passed(收集 12 error=mcp_durable 缺失既有已知,非本次引入)。
- **生产链三连[实测]**:hook.sh 模拟 stdin(session_id=throttle-smoke-1)①首次完整注入✓②同 session 立即重跑单行节流标记(594s remain)✓③`COMPASS_THROTTLE_MIN=0` 恢复注入✓;smoke 状态文件已清。
- **部署形态**:plugin 目录即生产(hooks 直指)——改动即时 live;本会话下条消息起生效(首条全量注入写状态,10min 窗内节流单行标记)。commit feat/memory-gate-trio 分支+push -u;**失效 WIP stash(v2.6 broken early-return stdout)drop 清账**——旧方案已被替代。
- 回音:flywheel data 站函(10867)未回(48h 窗内);平台 10862 已 ack。

### R436 · 2026-10-09 晚三(主件轮:T5.2 L2 报告生成器 v0✅[TDD 7绿+真卡实弹七点验收]——北极星首单交付效率件)
- **主件=T5.2 L2 报告自动生成管线首件**(LOOP_STATE 指针第 2 位,贴北极星 10/31 首笔 L2 $199):`tools/l2_report_gen.py`(纯 stdlib)——judge_status API done 卡→L2 报告草稿(卡面摘要/证据链原文零改动/时间线/复算指引/L2-ANALYST 人工槽位);**边界纪律内嵌:草稿 banner+未署名不得收费交付声明**(判读免费/装订收费两线定价的机器化执行)。
- **TDD[实测]**:tests/test_l2_report_gen.py 7 用例(判据 G1 零丢失/G2 双 sha/G3 槽位/G4 非 done 拒绝/G5 证据层保真)先 RED 后 **GREEN 7 passed**;tests/conftest.py 补 tools/ 路径(测试可 import tools 脚本)。
- **真卡实弹[实测]**:l1-0002 走线上 API 生成 `runtime/l2_reports/draft_l1-0002.md`(1370B)七点验收全 PASS(原文/双 sha/槽位/banner/证据层/时间线/复算指引);G4 拒绝路径实弹——假 id API 502→`[REJECT]` exit 2(fetch_card HTTPError 统一转 ValueError);stdout 模式冒烟 ✓。
- **附带·MEMORY.md 索引压缩✅**:hook 报 19.8KB 逼近 24.4KB 上限→行级重写 76 条,18.7→**14.8KB**(目标 17.1KB 达成;8 月旧条目大缩,细节在主题文件索引只留指针)。
- **附带·函 10869**:询平台 #10853 原文(e2e 真签测试坐标整理前置,#10862 第四条候件;我方本地无该函 body 存档)——回文即整理坐标另函直交。
- 教训:heredoc 内嵌中文+引号批量替换脚本两次翻车→改 Write 脚本文件执行;行首锚匹配须含 `- ` 前缀(第一次 0 命中)。

### R437 · 2026-10-09 晚四(主件轮:E1 失败样例归因✅[实测·基线逐位复现]——0.40 主瓶颈=库结构非 embedder·三发现+H1-H3 假设分级)
- **主件=E1 检索调优第一刀**(LOOP_STATE 第 3 位启动):`tools/e1_failure_attribution.py` 投送 A100(a100_exec base64 通道)实弹跑——**基线逐位复现 R@1 0.4000/R@5 0.6667/MRR 0.4994**(与预注册判据档一致,口径自证)。
- **三发现**:①工作集 50% 污染[实测](30 条中 15 条带生成器指令泄漏,18 miss 中 9 个来自无效查询——emb_gen_a_plus resp 清洗缺陷);②干净集失败结构=near-miss 邻域干扰[实测](9 失败中 8 个 gold 在 rank 2-4,FAR_MISS 仅 1——rerank 可达空间大);③干扰根因=库结构[推断]——**同主题双文档并存决定性例证**(memgate-m5 与 m5-memgate 两份 M5 lessons 互抢 top1 挤真 gold 到 rank4,出现 2 次)——0.40 主瓶颈是记忆库分档结构,不是 embedder,bge-m3 留任判据互证。
- **产出**:docs/metering/E1_FAILURE_ATTRIBUTION_20261009.md(三发现+H1 库去重/H2 rerank/H3 工作集 v2 假设分级+E1-TUNE v1 预注册判据建议稿:干净口径 R@1≥0.60 且 R@5≥0.80 且底座不动,H1/H2 分开归因)+e1_attribution_20261009.json(18KB 明细归档)。
- **附带·信箱 2 函全处理**:#10866 平台 nginx systemd 交接闭环(勘误收下:enabled+override 非 masked/不可达窗 1-2min 如实/白窗 10/11 对齐)ack;#10868 v5 崩溃修复闭环+DSN 双错定谳(20:57 落表实证)ack+**其 §③ 请求并查已回报**(函 10870:开场两 dirty 文件 diff 取证=工程 WIP 非翻转,我方侧无同类异常)。
- 判读卡状态快查(无新卡,四卡 delivered 维持);语料 2258 无变。

### R438 · 2026-10-09 深夜(主件轮:H1 库侧去重单独归因✅[实测]——R@1 +3.3pp 不够门·append 稀释副作用实锤·H2 rerank 升必要件)
- **主件=E1-TUNE H1 单独归因**(`tools/e1_h1_experiment.py`→A100 实弹):语料快照复制+合并 8 对同主题双文档(M5 对/7·22 会话拆分 5 对/goalmode 对/convergence 快照对;append 方式防丢内容)+gold 重映射 1 条+同口径复跑。
- **读数[实测]**:R@1 0.4000→**0.4333**(+3.3pp,+1 hit=M5 互抢例证被吃下)/R@5 0.6667→**0.6333**(-3.3pp)/MRR→0.5197(+2.0pp)——**H1 不单独过 0.60 门**。
- **三判读**:①append 合并有稀释副作用[实测](保留文档变长向量漂移,token 清除 query rank4→31,R@5 净跌)→H1b 差异精炼合并后置;②剩余 near-miss=跨文档主题相近非重复,H1 原理上吃不下→**H2 rerank 从假设升必要件**(过门主路径);③污染查询照旧 miss,工作集 v2 仍为判据前置。
- **产出**:E1_FAILURE_ATTRIBUTION 档追加§六(H1 实验段+判据建议稿修订:H1 降为前置清理不计过门归因)+e1_h1_result_20261009.json 归档。
- **附带·T5 节流生产实弹首例**:本值守轮一条用户消息注入单行节流标记(129s remain)——生产行为符合设计,上下文注入量实降。
- 全库同主题扫描(只读):15 对候选中真互抢 8 对已全入实验;本地生产库合并**未动**(候 H2 一起走,避免与 rerank 归因混杂)。

### R439 · 2026-10-09 深夜二(主件轮:H2 rerank 实验过门级读数✅[实测]R@1 0.40→0.5667·干净子集 0.80 双门过+fact_status 深度复核收官✅零下调)
- **主件一=E1-TUNE H2 单独归因**(`tools/e1_h2_experiment.py`→A100 实弹):bge-reranker-v2-m3(2.27GB)fp16,top5 重排,检索侧零改动。**全集 R@1 0.4000→0.5667(+16.7pp)·MRR→0.6167**;对照 H1 +3.3pp——rerank=主收益件,归因分离成立。
- **干净子集(15 条)读数[实测]**:R@1 **0.8000**(12/15)·R@5 **0.9333**——E1-TUNE v1 三门(R@1≥0.60/R@5≥0.80/bge 底座不动)**全过**;诚实口径声明:过滤口径非 v2 重生成口径,正式定谳候工作集 v2 复测(upgrade_path 在案)。
- **主件二=fact_status 深度复核收官✅**:measured 全量扫描(60 条×双特征过滤)→候选 2→人工判均保持(用户拍板事件)——**零下调即诚实终态**;🔴探针教训:库内 frontmatter 缩进不齐(2空格/1空格/顶格三种),`^fact_status` 顶格锚漏 90/96 条,初判"覆盖率仅 64/163"系探针自身 bug,grep 独立复核拨正(162/162 实为全覆盖)。档 T5.5b 收口,交接档悬置#2 销项。
- **排障三课(下载链)**:①HF 通道死锁假象=双下载进程并存(前进程占锁后进程等锁),速率 0 采样实锤;②`pkill -f` 自匹配第 5 次实锤(命令行自匹配自杀,rm+重启全没执行)→精确 PID+[i] 修法;③HF 断流→modelscope 通道 3.85MB/s 9min 完成(通道先例再证)。
- **产出归档**:E1_FAILURE_ATTRIBUTION §七(H2 段+判据三门判定表+剩余 3 miss 结构+部署形态推断)+e1_h2_result_20261009.json;LOOP_STATE 快照更新至 R439。
- **候下轮**:H1+H2 叠加实验(干净集理论上限 13-14/15)/工作集 v2 重生成(判据正本口径)/daemon rerank 层接入设计(E1-TUNE 正式立项)。

### R440 · 2026-10-09 深夜三(主件轮:H1×H2 组合实验✅[实测]归因矩阵闭环——组合 R@1 0.6333/干净 13/15=0.8667 双门过+信箱三函 ack)
- **主件=叠加实验收尾**(2×2 矩阵最后一格):`tools/e1_combined_experiment.py`→A100 实弹(合并语料 150 文档全管线)——**全集 R@1 0.4000→0.6333(+23.3pp)·干净子集 13/15=0.8667·MRR 0.6503**;组合≈可加无抵消(H1 append 稀释被 rerank 精读对冲);E1-TUNE v1 三门(过滤口径)全过,正式定谳候 v2 口径不变。
- 干净剩余 2 miss 打在理论上限下沿:token 清除 rank31=**检索侧未进 top5,rerank 原理够不着**(需 H1b 精炼/查询扩展)——发现记入 §八。
- **附带·信箱三函 ack**:10871 v5 R3 对齐回执(违例修正式=0,SQL 笔误定性闭环);10872 平台预检(②⑬改判对外人类口不装门——compass 无异议已复;GRACE 两案候白窗);10878 白窗落码通报(29 门点未部署,10/11 部署窗提前 2h 函告)+**#10853 原文回贴**——e2e 余项口径在手(P0-A 重放窗 10min/钱包 checksum 大小写坑),e2e 真签测试坐标候下轮主件整理直交。
- 产出:E1_FAILURE_ATTRIBUTION §八(归因矩阵表+终态)+e1_combined_result_20261009.json。

### R441 · 2026-10-09 深夜四(主件轮:e2e 真签测试坐标 v1 直交✅函 10885——10869 候件兑现,预注册判据五用例)
- **主件=e2e 坐标兑现**(#10878 §二回贴 #10853 原文后可整理):五用例坐标+断言点+现状预期直交 platform(函 10885,死线 10/12)——E1 基线全流程/E2 checksum 大小写(#10853 wallet-not-in-msg 针对例:两形态必须同收否则 RED)/E3 窗外重放(P0-A"步3"核心例:>10min 重放必须拒+零副作用,现状可能 RED 如实记录)/E4 窗内重放(存证不断言)/E5 篡改签名(校验器在岗对照例)。
- **判读岗姿态**:坐标即预注册判据 v1(sha 锚定后不发版);平台真签执行(compass 不持钱包=中立性),结果回函免费复核定谳可出 L1 判读卡——**开业后首张外部单候选管线**。
- 底稿入仓 runtime/outreach/e2e_coord_v1_20261009.md;信箱 0 新函。

### R442 · 2026-10-09 深夜五(主件轮:E1-TUNE 终局定谳✅[实测]判据正本口径三门全过——组合管线 R@1 0.8333/R@5 0.8333·E1 线收官)
- **主件=工作集 v2 重生成+终局评测**(E1 判据正本口径达成):生成器 v2 修清洗(R437 发现一闭环:BAD_MARKS 剥离+3 次重试+valid_query 拒空泛,候选池 3x)→**30/30 干净查询**(机械抽检零指令污染;人工注记 1 弱查询属难度谱)→三配置终局评测。
- **定谳读数[实测]**:基线 R@1 0.50/R@5 0.8333 · H2(+rerank) 0.80 · **组合(合并+rerank)=建议部署管线 R@1 0.8333/R@5 0.8333/MRR 0.8408——E1-TUNE v1 三门全过**(判据正本=v2 重生成口径,不再有过滤口径 caveat)。
- **两闭环**:①v2 基线 0.50>v1 表观 0.40=工作集污染拉低表观难度实锤;②干净口径 rerank 增益 +33.3pp>污染口径 +16.7pp——rerank 主收益结论正本口径下更强。
- **产出**:E1_FAILURE_ATTRIBUTION §九(终局定谳)+e1_final_verdict_20261009.json+A_plus_queries_v2 归档;生成器清洗纪律回写 tools/emb_gen_a_plus.py。
- **E1 线一夜五连收官**:R437 归因→R438 H1→R439 H2→R440 组合→R442 定谳。遗留=daemon rerank 层接入设计(候用户拍板排期);vdd4 磁盘 93% 观察(disk 14G+四盘分布实测,数据盘 vdf 170G 充裕,系统盘紧张候观察)。

### R443 · 2026-10-09 深夜六(主件轮:开业日公告物料 v1✅——判分 API 公告文+当日 checklist+候拍板清单;10886 大进展 ack)
- **主件=开业备料**(docs/plans/LAUNCH_KIT_V1_20261009.md):①判分 API 公告文(六能力清单全实锚:judge_status API/intake/criteria/榜单 26.7-16.7/NACRE judge HF/免费复算;定价边界一句话"判读永久免费,装订收费");②开业日 checklist(10/12 七时点:终检复跑/XERJ 跟进/白窗配合/三链接终验/21:00 PRECOR 候拍板/API 公告/回音巡检);③候拍板清单(PRECOR 署名投递=唯一阻塞,Einsia 函候三链接齐)。
- **附带·10886 ack**:nginx 403 止血落地(bootstrap 系全封含孪生 apply_improvement prompt 注入面)——**P0-A 应用层洞先于 e2e 闭环**,e2e 五用例转回归性质;代码固化三读数全过;nginx conf 正本回 git(drift 417 行清零);10885 e2e 坐标确认收到。
- 链接探活:intake/criteria 200 [实测];信箱 10886 处理毕 0 未读。

### R444 · 2026-10-09 深夜七(用户令·hook 链提速三刀✅+data 站判据重锚✅16 PASS——慢诊因实锤+两刀实测生效)
- **用户问"对话框为何慢"→实测诊断**:慢=本地 hook 链非模型(UserPromptSubmit 3.8-4.8s+每工具 mid_session 3.5s+Stop 7.7s,一轮 5 工具≈30s 纯开销);CPU<1.4s 大头=daemon BGE 排队+import 链。今天 T5 节流非变慢原因(方向是变快)。
- **刀 1✅[实测]**:hook.sh bash 层节流前置——🔴第一版用 grep/sed/tr/cut 工具链反慢至 12.4s(MSYS 每外部进程被 Defender 扫 ~1.5s);v2 纯 bash 内建(参数扩展提取 SID+EPOCHSECONDS+read 状态文件)**窗内 3.8s→1.0s**,窗外 python 接管正常。
- **刀 2✅[实测]**:mid_session_hook drift check 加 10min 时间窗(原每工具调用都打 daemon BGE 无节流)——**3.5s→0.38s(-89%)**;主 drift 防线仍在 recall 侧。
- **刀 3 部分✅[如实记负]**:stop_hook 超时 5s→2.5s+DRIFT_MAX_FILES=3(最坏 7.5s 上限 vs 原 N×5s 无上限);但实测 9.6s 无改善——profile 定位 import 仅 1.3s,剩余=daemon 忙时 drift 排队(今晚评测挤占),正常时段会回落,候再测。
- **data 站判据重锚✅[实测 16 PASS/0 FAIL]**:10891 flywheel 确认 B 案静态化预期发布(10736/10738 报备链在案)+实证内容未下线(固化 /app.html 直链可达);终检根页加静态锚(智涌飞轮/读数生成于)+原验货锚平移 /app.html 渲染口径(30571B 完整 DOM 恢复)——原判据内容不丢,净增不放宽;10867 PENDING-EXTERNAL 销项。
- 教训:MSYS 外部进程=Defender 扫描单价 ~1.5s/个——bash 脚本优化方向=内建优先;节流类逻辑一律先测进程数。

### R445 · 2026-10-09 深夜八(主件轮:判读工作台排期 v1✅函 10896——10/19 承诺超前 10 天兑现,交接档悬置#5 销项)
- **主件=工作台排期细化直交**(docs/metering/JUDGE_DESK_SCHEDULE_V1_20261009.md→函 10896):①SLA 承诺表(L1 证据齐 24h/L2 72h $199/复算免费 48h/争议复核 7 天/e2e 复核 24h,起算口径如实申明);②容量纪律(L1 日上限 ~10 卡[推断保守外推]/L2 周 2-3 份/超容排队明示不硬接/争议复核与 L1 隔离);③开业周 10/13-19 按日排期(首日开张→判例集 v1.5→L2 演练→真实单消化→rerank 接入→周复盘)。
- 附带:registry.html 外部增补"名词速览"段(NACRE/ORG-FUEL/函件判例/delta/qid 平实解释,与 R434 修复兼容)知悉保留;信箱 0 新函。

### R446 · 2026-10-10 凌晨(主件轮:rerank 激活评估✅——骨架盘点+CPU 延迟实测否决本机激活,三路径决策档)
- **主件=激活评估**(docs/metering/RERANK_ACTIVATION_ASSESS_20261010.md):daemon v2.3.0 **已有完整 rerank 骨架**(复用旧实物再中:COMPASS_PROD_RERANK 开关/同款模型/candidates 配置/fail-soft,当年 benchmark P@5 0.86→0.92 在档);四前提三过一否——**本机无 GPU,CPU 实测 cand=8 3.44s/cand=30 7.64s,recall <3s 预算不过,硬激活否决**(否则吃掉 R444 提速成果)。
- 三路径候拍板:a GPU 宿主(A100 remote-rerank 通道,建议,开业周后 10/18 位)/b 轻量模型(精度未证)/c 边际触发;验收判据=E1-TUNE 现成档零新立。
- 附带:本机 HF 缓存 2.2GB reranker 权重完整性确认(此前断点下载残件实为完整快照)。

### R448 · 2026-10-10 凌晨三(主件轮:开业博客发布面落实✅[实测外网 200]——blog.html 自有化部署+终检 15 项锚覆盖)
- **主件=发布管道落实**(R382 checklist 第一条"平台博客管道"悬而未落的缺口):发布面自有化——主域 `/blog.html`(此前 404 空位)新建 PRECOR 博客短版 HTML(registry 风格+英文正文+verdict 表+CTA 块 intake/leaderboard/GitHub/HF 全链)→scp+sudo cp 部署(R366 配方)→**外网 200/4697B [实测]**。发布动作从"等管道"变"已挂出,开业日只转链接"。
- **终检扩容 15 项[实测全绿]**:新加 PRECOR 博客页锚(quantized/four-rule/intake.html/100.00%——首跑抓出锚笔误 1.0000→100.00% 口径差修正);LAUNCH_KIT 三链接终验项就此全覆盖。
- 附带:compass 子域 404 确认不同根(registry 404),发布面定主域。

### R449 · 2026-10-10 凌晨四(主件轮:L2 报告管线首单干跑演练✅——完整样例产出+薄卡适用域发现)
- **主件=L2 管线演练**(北极星首单交付效率验证):l2gen 跑真卡 l1-0002→草稿 1370B→补 L2-ANALYST 演示段(归因/方法论评注/建议,明确标注演练样例非交付)→**完整样例 runtime/l2_reports/sample_l1-0002_full.md**——首单形态可展示。
- **管线发现一:薄卡适用域**[实测]:四张存卡中 0001/0003/0004 **verdict_detail 全空**(早期 schema,API 层无明细),仅 0002 有厚数据——L2 报告对薄卡会产出空壳。处置=适用域声明(L2 对象=新 schema 卡,真实单 0002 起标准)+薄卡回填候选(卡面档案→API 补明细,候排期,非开业阻塞)。
- 演练摩擦点零新增(生成→人工段→定稿链路顺滑,l2gen-v0 判据 G1-G5 全程保持)。

### R451 · 2026-10-10 凌晨五(用户拷问修正+rerank A100 服务端上线✅[实测 10ms]——pkill 自匹配第 6 次+SSH 重试通道)
- **用户四问修正**:①"为何等 10/18"——承认排期错误(把"开业周不动对外服务"偷换成"内部增强也推迟",而 rerank 是 env 开关 opt-in 对开业零风险),当场落地不等;②NACRE/assay/compass/基准评测四线进展展开陈述(v1 在役 88.51%/assay 3.3.0+验签门/Round1 榜单/E1-TUNE 方法论)。
- **主件=路径 a 服务端落地✅[实测]**:A100 rerank 服务(a100_rerank_svc.py v2,裸 transformers 零新依赖,9879 端口,token 鉴权)——**GPU 实测 10ms/查询**(3 docs;对照本机 CPU 3.44s=344 倍),排序语义正确,uptime 稳定。rerank 激活四前提的延迟前提就此补齐。
- **排障两课**:①`pkill -f` 自匹配**第 6 次**实锤——bash -c 命令串后半段明文目标名被正则命中,宿主自杀新进程从未启动(log 旧错假象);修法=pkill 与启动分两次 run+cmdline 避明文;②A100 SSH banner 间歇断连频发→a100_exec.py 加 3 次指数退避重试(通道治本)。
- **daemon 接入候下件**:本机 recall→A100 rerank 需稳定 SSH 隧道(autossh),E1 判据 0.8333 为接入后验收;另 sentence_transformers 缺失教训=服务端依赖优先裸 transformers。

### R452 · 2026-10-10 凌晨六(主件轮:rerank 隧道端到端✅[实测 74ms]——本机→A100 GPU 全链打通,daemon 开关设计定案)
- **主件=隧道落地**(tools/a100_rerank_tunnel.py+bat 保活,compass_tunnel.bat 同款模式):paramiko direct-tcpip 双向 pump+断线自愈(transport 失活重建);凭据走 a100_env 不落仓。**端到端实测 74ms**(本机 19879→A100 9879→GPU rerank→返回,ok=True 排序语义正确)——E1 检索质量读数的全链路硬件路径就此打通。
- **daemon 开关设计定案**(候下件实现):`COMPASS_RERANK_REMOTE=127.0.0.1:19879`(空=本地模式不变)——daemon.py `_rerank_top` 加 remote 分支(socket 协议同 rerank_svc),改 plugin 分支+测试择窗部署(生产 daemon 直改纪律)。
- 修一坑:类型注解 `socket.channel` 定义时求值炸→`from __future__ import annotations` 一行修。
- 开业周 daemon 部署窗后顺序:分支合入→隧道 watchdog 自启→COMPASS_PROD_RERANK=1+COMPASS_RERANK_REMOTE 双开→E1 判据 v2 工作集复测验收(零新判据)。

### R453 · 2026-10-10 凌晨七(用户令·daemon remote 分支实现✅TDD 5绿+回归17绿——feat/rerank-remote 已 push,不部署)
- **主件=daemon remote 分支**(feat/rerank-remote,新分支从 M5 落账基线切开——先把生产 v3.1 idle-unloader 47 行补 commit 还债):daemon.py 加 `_rerank_via_remote`(9879 协议,6s 超时,None 即回退)+`_rerank_top` remote 优先分支(**三级回退:remote→本地 CrossEncoder→dense**,recall 永不因 rerank 故障崩溃)。
- **开关**:COMPASS_RERANK_REMOTE=host:port(空=行为完全不变);COMPASS_RERANK_TOKEN_FILE 默认 .cache/a100_rerank_token。
- **TDD[实测]**:tests/test_rerank_remote.py 5 用例(fake TCP server 三模式)先 RED 后 **GREEN 5 passed**;回归 throttle+rerank **17 passed**;ast 语法 OK。
- **部署边界**:不部署——本机生产 daemon 仍跑旧版;部署序=分支合入 main→隧道 watchdog 自启→双开关打开→E1 v2 判据复测验收。

### R454 · 2026-10-10 凌晨八(用户令深度梳理·NACRE 路线图落档✅+ORG-FUEL 扩容开工✅——诚实重算:10/26 主场景=推迟报告)
- **主件一=路线图正本**(docs/plans/NACRE_ROADMAP_20261010.md):现状盘点(v1 在役/7B 卡语料/检索全通)+四洞察(语料关键路径算账/飞轮显式化/方法论即产品/双轨诚实)+时间轴(开业冲刺→开业周→对拍窗→北极星收官→11 月二期)+NACRE 专项四优先级。
- **主件二=扩容开工**[实测]:新源生成器×2(tools/fuel_gen_queue.py+fuel_gen_memory.py,gate 口径不变)——queue 轮次源 82 candidates+memory 记忆源 162 candidates=**244 新候选就绪**(runtime/org_fuel/candidates_queue|memory.jsonl),候 NACRE judge 投判(现 4 源 pass 率 55% 外推→约 +134)。
- **诚实重算[推断,重要]**:docs 407 文件已被 docs 源全量覆盖(799 candidates);扩容天花板=2258+134+开业周真实单+delta≈**2400-2450<3000**——10/26 主场景=**按预注册条款推迟报告**(推迟≠放宽,新裁决窗重注册);副场景=真实单超预期。候用户知悉此预期修正。
- 路线图文件与生成器入仓;judge 投判候下轮(脚本沿用 _fuel_judge 模式)。

### R455 · 2026-10-10 凌晨九(主件轮:ORG-FUEL 扩容闭环✅[实测]——244 全判 pass 162/门过 162,语料 2258→2420 外网 live)
- **主件=扩容全链闭环**:①candidates 投递遇 base64 命令长度上限(135KB 炸)→分块传输修复;②judge 投判(_fuel_judge_expand.py,同模板 bf16+LoRA 合规)——**244 全判:pass 162/insufficient_evidence 67/fail 15[实测]**;③拉回 verdicts×2→corpus_pipeline 扩两源(org_fuel:queue=69/org_fuel:memory=93,pass+anchor L0/L1 双门)→重算 **2420/新 sha f92cb549**;④site stats+registry FALLBACK 更新+部署→**外网 2420 live[实测]**。
- **10/26 预期修订[推断]**:2420+真实单+delta≈2450-2500,3000 不可达——推迟主场景维持(R454 重算),推迟报告预案候用户拍板后写入对拍执行档。
- 教训:base64-over-exec 通道对 >100KB 文件需分块(已实测);put 大文件统一走分块路径。

### R456 · 2026-10-10 晨(用户令·7B 资源预检✅+🔴J6 口径重大澄清——R454 错误绑定修正,"推迟预案"作废)
- **🔴概念澄清(修正 R454)**:J6 ≠ 7B 对拍。J6(10/26)=**需求侧裁决**(外部复算请求/首单意向>0 判据,PREREG_DEMAND_CHECKPOINT);7B 对拍=语料 3000 **阈值触发无日历死线**(corpus_stats trigger)。R454"10/26 语料不到→推迟报告"系错误绑定,**前提作废、预案不需要**。J6 备考=开业周判读服务曝光(真实需求>0 即过)——与开业三件直接联动。
- **主件=7B 资源预检**(docs/plans/SEVENB_PRECHECK_20261010.md):基模 ❌→**已启动下载**(modelscope→vdf,Qwen3-7B ~15GB);脚本 ✅(a3_lora_sft);适配器 ✅(best_lora 完整);磁盘 ✅(vdf 167G)。四项三绿一下载中。
- **信箱 2 函 ack**:10899 平台审计回执(SHA 双锚机制共建+自伤循环补丁已部署毕+days le=90 更正——高质量闭环);10916 kairos 双凭据+无 key 调用方全谱(compass grep 实证无 WRITEBACK_KEY 依赖+不在名单;GRACE 关闸 10/12 提醒收下,我方调用全带 X-API-Key)。
- NACRE_ROADMAP §二洞察 1 已就地修正(澄清段)。
- NACRE_ROADMAP §二洞察 1 已就地修正(澄清段)。

### R458 · 2026-10-10 晨二(主件轮:7B 下载核查→🔴勘误第 8 例——Qwen3 系无 7B,实为 8B·Qwen3-8B 下载跑起[实测 376M+])
- **勘误第 8 例[实测]**:"7B 对拍"口径误——hf-mirror 实测 Qwen/Qwen3-7B=404 而 8B=302 在,**Qwen3 系官方无 7B 尺寸(0.6/1.7/4/8/14/32B)**,实际对象=Qwen3-8B;registry 文案勘误已部署(外网 grep 8B 对拍×2),corpus_stats 字段名 sevenb_* 保留(schema 稳定);预检档补勘误段。
- **下载链排障**:昨晚"7B"下载实为空壳(modelscope record not found=repo 不存在的表象);换 hf-mirror 通道**Qwen3-8B 下载健康跑起**(376M/67% 文件/3 进程,~16GB 预计 1h 内)。完成后 7B(8B) 资源预检四项全绿,对拍就绪状态。
- 附带:信箱 0 新函(10899/10916 已 ack)。

### R459 · 2026-10-10 晨三(主件轮:r87 判据冻结确认✅函 10925+LOOP_STATE 全面刷新——复核前置门全通过)
- **主件一=判据冻结确认**(#10920 v5 判据档 b7_iso_r87_dualarm_v1 sha16=223a9dbf 审阅):五要素逐条过(卷面 sha 锚/greedy 同构/reward 三层同款/delta 三态 noise_floor 0.15/独立性分工)——**无异议冻结生效**(函 10925);复核动作预告=noise_floor 对历史分布回验 [非异议];复核就绪承诺重申(4h/10-12 12:00/卡号 0005)。
- **主件二=LOOP_STATE 状态正本全面刷新**(值守纪律补课,落后 20 轮):判读岗首张外部复核单/开业物料全就绪/NACRE 2420+8B 勘误+J6 澄清/E1 rerank 工程链/在飞与候拍板清单——下一会话零考古。
- **8B 下载观察项**:2.4G/16GB hf-mirror 慢速推进(非阻塞,对拍无死线;完成候下轮核查)。
- 附带:Einsia 函候用户过目(草案 v1 在档,不发条款已解除)。

### R460 · 2026-10-10 晨四(主件轮:rsi-bench 回归集窗前预检✅——26 行定版核对+投递文案草稿备妥,窗开日零现场)
- **主件=窗前预检**(docs/outreach/RSIBENCH_REGRESSION_SUBMIT_PLAN_20261010.md):材料 26 行 v1 定版[实测核对与 R355 一致,字段 qid/arm/defects/patch_found/expectation/anchor 齐];投递=rsi-bench#4 跟评(英文文案草稿已备);窗口径统一 **10/13-15**(R417 较新口径,排开业三件后);窗开日现场=贴一条评论 ~10 分钟。
- checklist 四项(链接 200 复验/48h 纪律/stale 先 keep-alive)入档。
- 附带:8B 下载慢速推进观察中;r87 复核候 10/11 发车读数。

### R462 · 2026-10-10 晨六(主件轮:DAY_LOG_20261010 落档✅——开业前夜 14 轮战报结构化,八教训九沉淀)
- **主件=日志落档**(docs/plans/DAY_LOG_20261010.md):八段结构(开业线/判读岗/NACRE/检索线/基建效率/跨框互动/教训九条/候拍板悬置)——R448-R461 全轮覆盖,下一会话考古入口。
- 附带:8B 下载 8.9G/16GB 推进中;信箱 0 新函。

### R463 · 2026-10-10 晨七(主件轮:对拍判据档勘误注记✅——预注册缺口证伪+被测物指向修正留痕)
- **自我证伪先行为先**:本轮候选"8B 对拍判据预注册草案"——查证发现 **SEVENB_COMPARE_PREREG_20261008.md 已冻结完整判据**(G1 主门 +2.0pp/G2 三门/G3 精度 99%/G4 稳健披露+禁改条款+触发序列),缺口不存在,防了一次冗余工作。
- **主件=判据档勘误注记**:被测物"Qwen3-7B"不存在(勘误第 8 例)→档头留痕修正为 Qwen3-8B(事实性指向修正,G1-G4 数字零改动,非放宽非加严,档名保留引用稳定);现状数字同步 2420。
- 对拍就绪度:判据✅(冻结)/触发器✅/基模下载中——语料到 3000 即零现场执行。

### R464 · 2026-10-10 晨八(主件轮:窗前就绪核查+8B 断连续传修复✅)
- **核查**:XERJ PR 草稿在位✓(_xerj_pr_draft.md,R373 材料);8B 下载断连卡死(IncompleteRead 8.9G)→重启续传恢复(**9.5G/80%→87% 文件[实测增长]**);hf-cli 断点续传特性再证(重跑同命令续传已落分片)。
- 信箱 0 新函。开业三窗就绪度:XERJ(材料全备)/rsi-bench(预案备)/Einsia(候用户过目)。

### R465 · 2026-10-10 晨九(主件轮:intake 端到端演练✅[实测]——真实客户路径全通+SLA 口径修正部署)
- **主件=intake 端到端演练**(反剧场:终检只验内容锚,提交流程从未端测):真实客户视角 POST `/api/platform/org/assay/submissions`(GRACE 期无 key)——**HTTP 200 受理**(id=8b97795a,intake_validated,SLA 自动计算,edit_token 下发);进度端点确认"受理完成,判读排队中";**is_smoke=true 自动标记**(10718 产能防污染机制在役实证)。开业日真实客户第一单路径全通。
- **SLA 口径不一致发现+修正**:intake 页面"5 个工作日" vs API SLA 1d vs 工作台排期 L1=24h——三处两样;修正=服务器侧 intake.html 直改部署("L1 判读卡 SLA 24 小时;复杂单走 L2/L3 分档",外网 grep 验证 1 处)——对客户承诺收紧(只许更严,与工作台排期 v1 对齐)。
- 演练单处置:is_smoke 已自动标(不污染产能读数);卡号候判读岗按自检单口径出(nautilus-l1-0006 候选)。
- 附带:8B 下载续传健康(9.5G+)。

### R466 · 2026-10-10 晨十(主件轮:8B 下载守护部署✅——hf-mirror 两断的自动化兜底,完成自停)
- **主件=下载守护**(tools/qwen8b_dl_guard.sh→A100):loop 120s 检查——断则自动续传(hf-cli 断点续传)/完成判定(4 分片+config+无 incomplete)自停;**部署拉起验证[实测](守护+下载进程在位,15G 推进)**——免手动每轮盯。
- 附带:演练单(8b97795a)候判读岗排期出卡(is_smoke 低优先,如实转排期);8.9→15G 续传轨迹留档。

### R467 · 2026-10-10 晨十一(主件轮:演练单出卡 nautilus-l1-0006✅[实测外网 live]——判读岗标准流实战+部署链走通)
- **主件=演练单出卡**:judge_status_api.py LEDGER 加 nautilus-l1-0006(判据引用 5c8e0a7c 同构自检单判据零放宽/is_smoke 如实标注/不进名次区/E2E 演练成果入 disposition)——commit→cloud pull→compass-judge-status 重启→**外网 judge_status?id=0006 live[实测]**;全卡清单 6 张(demo+0001/0002/0003/0004/0006),**0005 号正确预留给 r87 复核单**(顺延逻辑)。
- 部署链:GitHub push→cloud /home/ubuntu/nautilus-compass git pull→systemctl restart compass-judge-status(active)——R370 先例复用零障碍。
- Edit 事故一笔:中途误删 0002 title 行,语法+完整性验证抓到即时修复(先证伪自己再部署)。

### R468 · 2026-10-10 晨十二(主件轮:外联台账 V1.1 滚动✅——三天状态变化全量,总账判读=窗口执行期)
- **主件=外联台账滚动**(docs/outreach/EXTERNAL_LEDGER_V1_1_20261010.md,V1 留痕):活跃表 8 线更新(XERJ 窗 10/12/rsi-bench 窗 10/13-15/PRECOR 双轨 10-12 21:00/mem0 挂账/**v5 判读单新入 10-11-12**/flywheel 销项/platform 审计链闭环);渠道表(intake 端到端实测+rsi-bench 预案升级);观察/归档更新(VOBC 归档+XERJ 跟进转监控)。
- **总账判读**:外联线从"提案期"整体转入"**窗口执行期**"——五个窗全部材料零现场化,判读岗转入外部单实战,下一波=开业周各窗逐开+回音收割。
- 附带:8B 下载守护在管(15G+);信箱 0 新函。

### R469 · 2026-10-10 晨十三(主件轮:正日前最后一次全量预演✅17/17 双口径——判据升级+sha 锚同步+重复函归档)
- **主件=正日预演**(判据只许更严两连):①判读卡清单锚升级(+nautilus-l1-0006 入卡清单判据);②registry 渲染 sha 锚随语料版本同步(93dccd→f92cb549——🔴新值守纪律:语料合并后终检 sha 锚须同步更新,旧锚 WARN 即信号)。复跑 **17 PASS/0 WARN/0 FAIL,exit=0 双口径[实测]**——10/11 正日判据终态。
- **10924 归档**:v5 判据档同内容重发(与 10920 同),我方 10925 已确认生效——ack 注记按重复件归档。
- 附带:8B 下载守护推进中。

### R470 · 2026-10-10 晨十四(主件轮:8B 资源线收官✅[实测]——下载完成守护自停,对拍四项全绿零现场就绪)
- **主件=收官判定[实测]**:Qwen3-8B 下载完成(5 分片+config+0 incomplete,守护 04:43 完成自停)——对拍资源四项**全绿**:基模✅/训练脚本✅(a3_lora_sft)/v1 适配器✅/磁盘✅(vdf 167G)。
- 就绪态:判据冻结(SEVENB_COMPARE_PREREG,勘误注记后)/触发器(语料 3000)/执行序列四步(档内)——语料达标日即零现场执行。
- NACRE 线状态一句话:v1 在役·语料 2420 棘轮·8B 待命·判据冻结·检索增强已过门待部署——**模型线的下一件大事只剩"等语料+跑对拍"**。
- 附带:信箱 0 新函;8B 守护在管。

### R480 · 2026-10-10 晨廿二(用户令外联拓客·rsi-bench 策略改判+人性化回应✅——外联转转化期首件)
- **用户令"各渠道外联拓客推进转化"**——外联行动计划启动。首件即遇 **rsi-bench #4 状态变化**:维护者 sunghunkwag 公开回应=极端经济困难($7 撑 12 天,明示"可拒绝/忽略,非合作条件,希望恢复后回来")。
- **策略改判**:回归集投递(R460 预案,原窗 10/13-15)**改判挂起候对方恢复**——困难期投技术交付=义务压力;改发人性化支持评论(comment 6091359859:理解+回归集已安全在侧随时可取无期限+祝愿)——不投递不催促不提捐助。
- **捐助请求呈报用户**:对方提 PayPal 一次性 $300/$100(github.com/sunghunkwag)——组织不介入资金,个人决策候拍板。
- **J6 影响评估**:rsi-bench 线暂停≠J6 受损——J6 判据=外部复算请求/首单意向,来源不止 rsi-bench 一家;开业周多渠道并行。
- **附带·10935 ack**:v5 bearer 门落地三态实测(匿名 401)验收知悉,零误伤依据核实(24h log 唯一访问者=我方探测)。

### R481 · 2026-10-10 晨廿三(主件轮:PRECOR dev.to 传播首发✅[实测外网 200]——外联转化第一发实弹)
- **主件=dev.to 发布**(docs/marketing/devto_precor_post.md→API):标题"We quantized our AI judge. Here's exactly what broke."——**id 4825866 外网 200 live[实测]**(tags ai/llm/testing/mlops);AI 披露双保险(front matter ai: ai-assisted+正文尾注,治"披露新政不分发"根因);CTA 全链(intake/leaderboard/GitHub/HF)。
- 排障:403 Bots=记忆在案坑(python 无 UA)→浏览器 UA 配方复用一发过。
- 发布策略说明:博客已 live,提前传播预热(原 10/12 21:00 口径调整为"已发布,开业日为官宣节点");知乎/大人渠道仍候窗。
- 待办:1-2h 盯评论(devto 惯例);arXiv 版同周投。

### R482 · 2026-10-10 晨廿四(轻轮:dev.to 评论监控方法定谳——a_id 端点有效,当前 0 评论冷启动正常)
- **工具知识入档**:dev.to 评论监听正解=`GET /api/comments?a_id=<id>`(带 key,实测返回 []);`/api/articles/{id}/comments` 不稳定(首查误返 len=2 引误判,复查 404)——**当前帖子 0 评论**(发布 20 分钟冷启动正常,分发需小时-天级)。
- Discord 跟进帖改判:错峰动作(博客发酵后再发,即时发反而稀释)——候下一波。
- loop 状态:外联转化期首轮动作全落地(dev.to 首发+rsi-bench 人性化回应),进入发酵观察期。

### R486 · 2026-10-10 晨廿八(轻轮:dev.to 发酵基线建立✅[实测]——发布 1.5h 四指标零点)
- **主件=发酵基线[实测]**(`GET /api/articles/me/all` 带 key,4825866):reactions 0/comments 0/views 0/阅读时长 2min——发布 1.5h 四指标零点记录(dev.to 分发爬虫索引需数小时-天,冷启动正常);后续值守轮同端点观测增长曲线。
- 附带:8B 下载守护在管(15G+);信箱 0 新函。

### R492 · 2026-10-10 晨卅二(主件轮:🔴审计岗发现采纳——判据档实体不存在,r87 前置门补实体要求函 10953)
- **四新函处理(回音收割期)**:#10933 compass 审计岗(我方审计线自发)/#10946 代发规范/#10949 平台对表/#10941 已 ack。
- **🔴主件=判据实体核验与补全要求**(审计岗发现+三环境实测确认):判据档 b7_iso_r87_dualarm_v1.json **实体不存在**(A100/cloud/本地 find 全零命中,sha16=223a9dbf 锚着函件要点文本非 json 实体)——我 #10925"冻结生效"确认语义修正(要点审阅有效,实体验证遗漏,审计岗抓出);**函 10953 要求 v5 发车前(10/11 12:00)实体落盘+sha 复算口径声明**,验证一致=冻结补全复核照旧,逾期=发车推迟(宁缺勿滥门不降);#10924≠#10920 归档判定修正。
- **审计价值再实证**:审计岗(只读线)抓出判读岗(执行线)的实体性遗漏——分工与互查机制健康。
- **附带**:10946 代发规范五条执行知悉(hr 代发函按标题识别)/10949 平台副本卫生三查互证 ack。

### R490 · 2026-10-10 晨三十(主件轮:XERJ #1138 上线告知跟帖✅[实测]+eval-answers offer 激活确认——offer 链闭合)
- **主件=#1138 跟帖**(comment 6092543315):pack 上线状态告知(#1255 MERGED+Release 链接+#1210/#1264 全链)+**eval-answers offer 激活确认**——R373 PR body 的"offer 随首 seed 触发"条款现已就位(hub 槽位在,候 maintainer 投首 seed);我方交付义务=首 seed 到→独立判读答案集(预注册+三态+UNVERIFIABLE 墙+全公开)。
- **dev.to 2.5h 读数[实测]**:reactions 0/views 未披露/comments 0——冷启动延续,观察窗持续。
- 外联转化期:8 件外联对象全部状态定谳,offer 链闭合(XERJ 捐赠→槽位→eval-answers 候 seed——下一转化触发点=对方投首 seed)。

### R483 · 2026-10-10 晨廿五(轮:SLA 口径一致性收尾✅——精确扫描零残留+10937 高质量对表 ack)
- **SLA 口径收尾[实测]**:全仓精确扫描(排除 V1 留痕/L3 分档合法/已修两档)——**零残留**;智谱 Wave2 文案(platform 函件侧,含旧保守口径)判定=不发更正函(保守承诺无伤,判读岗实际 24h 超预期=正面惊喜;且 platform 主发文本我方不持源)。
- **10937 ack**(platform 对表高质量闭环):bootstrap NameError 修复+'空体实调'改进条款采纳/fde-org 裸门 403 全过/副本漂移消除/三件开业后首批工程验收判据照单/'探针的害不取决于发什么'入组织免疫册互证。
- SLA 口径一致性工程至此**彻底闭环**(intake API/页面/工作台/两档/扫描五点全对齐)。

### R487 · 2026-10-10 晨廿九(主件轮:8B bf16 训练 smoke 跑通✅[实测 26.4G 无 OOM]——配置档证据层 [推断]→[实测] 兑现)
- **主件=8B smoke 先行**(EIGHTB_COMPARE_TRAIN_CONFIG 证据层 upgrade_path 兑现,不等语料 3000):8B 版脚本(25 步短训副本)投 A100 实跑——**LoRA 正确挂载(trainable 15.3M/0.19%)+bf16 显存 26.4G 无 OOM[实测]**——配置档"8B bf16 显存可行性=[推断]"升级 **[实测]**。
- **两坑修**:①启动门 2G 拦截(A100 常驻服务 7G=判分+嵌入+rerank)——门阈值参数化 COMPASS_GPU_BUSY_G=12G(真大训练仍拦,常驻共存放行,env 可调);②语料后缀不匹配(脚本要 split_train.jsonl 无 _v1)——软链修正。
- **附带·10941 ack**:platform P0 闭环对表(8001 iptables 封死+v5 bearer 门 401 验证+19 条加固候评估)——turf 边界确认。
- smoke 训练+评测段后台运行中(约 15-30 分钟),终态读数候下轮收割。

### R484 · 2026-10-10 晨廿六(用户令外联·🔴XERJ 线翻案收官✅[实测 GitHub 三连]——外联台账第一行欠账实为已完成项)
- **决定性发现[实测 GitHub API]**:XERJ record pack **PR #1255 已 MERGED**(10/8 17:36Z,mergeCommit fc8f86d8)+**Release 已发**(pack-agent-session-trajectories-2026-10-09,10/9 11:34Z maintainer 构建)+#1210 槽位/#1264 publish 三连 MERGED——**捐赠包正式在 hub 上线**;#1138 跟帖已存在(2 条 pack 相关)。R373 备稿后实际已发(10/8 21:14 commit),queue R373"窗开即发"记录与事实错位(实际执行轮记录缺/在 archive)。
- **台账修正**:V1.1 第一行"候发"→"✅收官";LOOP_STATE 在飞"XERJ Release 候构建"同步销项。
- **勘误自省**:R373 后的执行轮(R38X?)记录缺失致台账误记欠账——复审外联台账时 GitHub API 实测(state/mergedAt/release)是唯一可靠判据,queue 回忆不作数。
- XERJ 线最终态:捐赠 MERGED+Release 上线+demand anchor 跟帖——**外联最大单件完全收官**。

### R485 · 2026-10-10 晨廿七(轮:外联在飞件 API 实测轮✅——三件状态定谳,全部无需动作)
- **awesome #14065**(punkpeye 仓,非 wong2):**OPEN 未合**——在飞确认,候 review 无动作;
- **openclaw#3787**:二轮审核中(R387 ClawSweeper bot 10/9 占位),真仓坐标反查成本>价值(处置本就是等结论不扰 bot)——状态=等审核结论;
- **letta-evals#340**:OPEN 存活+零评论(提议独立复算层,静默窗内)——候窗不扰。
- 外联在飞全景定谳:全部"球在外且无需我方动作"——**转化动作已全部落地**(dev.to 首发+XERJ 收官+rsi-bench 人性化回应),剩余=发酵与窗口。

### R471 · 2026-10-10 晨十五(主件轮:8B 训练配置预注册档落盘✅——触发序列第 3 步前置+阈值不一致发现)
- **主件=训练配置落档**(docs/metering/EIGHTB_COMPARE_TRAIN_CONFIG_20261010.md):脚本基座=_train_judge14b_upgrade_A100.py 参数化;适配点①基模=8B **bf16 全精度**(不用 4bit——PRECOR 纪律 bf16/fp16 only,比 14B 时代妥协更干净);适配点②**阈值不一致发现**——脚本 U6=+3pp(10/5) vs 判据档 G1=+2.0pp(10/8 冻结),触发日以判据档为准(常数对齐 0.02);超参沿用现役 recipe。
- 触发日零现场清单五步落档;8B bf16 显存可行性=[推断](触发日 smoke 先行验证)。
- 附带:信箱 0 新函;8B 守护在管。

### R472 · 2026-10-10 晨十六(主件轮:XERJ PR draft 发前最后通读✅——三件材料在位性实测核对全过)
- **主件=发前 double-check**(R373 后 40+ 轮首重读):PR 正文预填八段完整(domain/counts 70→70/provenance 五步脱敏+抽检 7/7/CC-BY-4.0+baseline attribution/source git+glob/demand anchor/build 命令);预检表 7✅+1⚠️(flat 语义已内置处理);**三件材料在位性[实测]**——recipe.toml 2355B/README.md 3167B/jsonl 147KB **70 行整**(与 PR counts 声明一致)——draft 引用路径零失配。
- 结论:XERJ PR 窗开日(10/12)五步机械执行即可,通读无新增修正项。

### R473 · 2026-10-10 晨十七(主件轮:intake 出站链接全检✅零死链+判据化终检 16 项)
- **主件=开业页死链防护**:intake.html 出站 6 链接逐个探活——**全 200 零死链**[实测](pipeline/unipat/org 子域样例/registry/leaderboard/criteria);判据化入终检(POINTS 增"intake 出站链接"锚项,pipeline/unipat/L2_report_sample 三锚)——复跑 **16 PASS/0 WARN/0 FAIL**。
- 开业页事故点(死链)自此有判据覆盖;正日终检项=快检 16+渲染 2=18 项。

### R474 · 2026-10-10 晨十八(主件轮:unipat/pipeline 内容健康检查✅——开业链接面壳检查补全)
- **主件=内容级验证**(registry undefined 同类预防):intake 链接的两页面渲染内容检查——unipat(4054 字文本/title 正确/无 undefined)+pipeline(3142 字/无 undefined)——**零壳零 bug**[实测];开业链接面三甲(死链/壳/undefined)全防护。
- 8B 重复确认 16G 完成(R470 已收官)。
- **loop 状态声明**:所有线就绪/等待,实质件池已空——后续轮若无新函/新事件,按纪律诚实报告不硬造。

### R475 · 2026-10-10 晨十九(主件轮:8B 训练脚本预注册版落盘✅——零现场最后拼图)
- **自我证伪再立功**:候选"四门评测脚本预写"——查证评测已内嵌训练脚本基座(U4/U5/U6 段),无需独立脚本;真增量=**8B 版脚本实体化**(_train_judge8b_upgrade_A100.py):U6_MARGIN 0.03→**0.02 对齐判据档 G1**(防执行用错尺子)+五默认路径修正(model=8B 新位/base17+champion=现役在位路径/corpus+out=vdf)——argparse 旧 vdd2 路径全替换。
- 至此 8B 对拍零现场清单**实体齐**:判据档+配置档+脚本实体+基模+触发器——触发日=`python _train_judge8b_upgrade_A100.py` 一条命令。

### R476 · 2026-10-10 晨二十(轮:rerank 合入尝试中止✅如实——plugin 仓分支治理债浮出)
- **尝试**:feat/rerank-remote 合入 plugin main——**中止**(无损):main 被 memgate worktree 占用+本地 main **behind origin/main 698 commits**(分叉严重),乱合可能污染生产 memgate 线;merge 实际跑在自身分支=Already up to date 零变更。
- **发现(新悬置)**:plugin 仓分支治理债——main(本地 7c7572e,worktree 占用)vs origin/main 分叉 698;rerank 合入正确姿势=**GitHub PR 流程**(feat/rerank-remote 已在 origin,候白天清晰会话开 PR)。
- 状态回滚确认:checkout 回 feat/memory-gate-trio 无损;rerank 代码安全在 feat/rerank-remote(origin 有副本)。
- 教训:跨分支操作前先 `git worktree list`+`branch -vv` 摸拓扑——今晚三次盲目操作都被前置检查拦住(整体是赚的)。

### R450 补记 · 2026-10-10(复盘补录:brief 页撤下决策留痕)
- 用户令"做每日简报"→我产出 brief.html 并部署→用户立即纠正"**你这做每日简报属于又增加负担了**"→当场撤下(线上删除+文件删除+教训入 memory feedback-brief-page-reverted-20261010)。当时以"无产出不记"为由跳过 queue——复盘判定**被纠的决策也是决策,留痕**:信息过载的解法=收敛与异常推送,不是新增信息源;造新载体前三问(替代谁/旧载体为何不够/能否并入正本)。

### R477 · 2026-10-10 晨二十(用户令复盘·查漏补缺修正迭代✅——四面扫描五项修正)
- **矛盾面**:①intake SLA 修正(24h)后,JUDGING_PRICE_LIST_V1 与 JUDGING_SERVICE_PAGE_V1 仍残留"≤5 个工作日"——**已修正**(两档收紧为 L1 24h/L2 72h/L3 5 个工作日分档,对齐工作台排期 v1;承诺只许收紧)②rerank"候部署窗"实为可解绑——合入 main=零激活风险已尝试,因 plugin 仓拓扑治理债中止(正确),改走 PR 流程候白天。
- **遗漏面**:①R450 撤下决策补记 queue(被纠决策也是决策);②J6 澄清+勘误第 8 例补 memory 条目(重大口径修正防再犯);③manifest_corpus_pipeline.json(2420 正本)漏 commit——已补;④emb_bakeoff_eval.py 运行版漏 commit——已补。
- **质量面**:①8B 评测脚本候选——自我证伪(评测内嵌训练脚本基座)→真增量=8B 版脚本实体化(R475);②A100 无僵尸进程;③intake 出站 6 链接零死链+判据化。
- 复盘结论:43 轮产出经查漏后**全部落账一致**;新增悬置=plugin 仓分支治理债(main 分叉 698,候白天 PR 流程)+rerank 在线验收方案细化(候部署窗)。

### R478 · 2026-10-10 晨廿一(轮:XERJ 材料行尾审查——自我证伪,防线本来就在)
- **候选修正被证伪**:XERJ 三件材料工作树实测 README 59 CRLF/jsonl 70 CRLF→判"含 CRLF 需修"→LF 转换后 git add 无 diff→blob 对比实锤:**HEAD blob 本来 LF 纯净(CRLF=0)且与工作树内容一致**——R373 入库时 autocrlf 已正确转 LF,工作树 CRLF 仅为检出态。
- **结论**:XERJ PR 材料仓库内容 LF 纯净 ✅ 无需修正;上轮"⚠️含CRLF"系把工作树检出态误判为入库内容——sha-eol 陷阱的正解反而是"信 autocrlf 机制+blob 对比定谳"。
- 教训:行尾审查的判据=blob 口径(git show HEAD:file)而非工作树口径——与 sha 锚 LF blob 口径纪律同源。

### R461 · 2026-10-10 晨五(主件轮:判读岗 SOP v0.1 增补✅——r87 首例实战沉淀外部复核单子模式)
- **主件=SOP 增补**(docs/sops/ROLE_JUDGE_SOP_V0 §八,v0.1):r87 实战新增三模式入规程——①**产能前置门**(被测方先函询产能,判读岗按容量纪律回函接/拒,防白跑);②**判据来源双模式**(自拟预注册/被测方预注册+岗审五点,未冻结不出复核不变);③**复核动作三件+结论三态**(逻辑抽查/抽样 n≥10/一致性比对→背书/修正/退回)。
- 独立性从严条款:被测方兼判据作者时,阈值须给历史分布支撑。
- v0 既有六步/四门/红线结构未动,纯增补;首例引用 r87 全链(10920/10921/10925)。

### R457 · 2026-10-10 晨二(主件轮:r87 判读复核接单✅函 10921——判读岗首张外部复核单,v5 训练方/compass 独立复核)
- **死线带新件接单**(#10920 v5 产能确认函):r87 双臂同构复考(held-out 60 题×r80 vs grpo_r87)10/11 发车——**compass 接复核单**:读数到手 4h 内出终判,10/12 12:00 前完成(榜单刷新前背书,余量 6h+);投递=mailbox(trace r87-judge),卡经 judge_status API live(卡号顺延 0005)。
- **判读纪律条款先冻结**:v5 初稿须带预注册判据档(criteria sha,未冻结不出复核);compass 终判=非实现者复核(判定逻辑抽查+held-out 抽样 n≥10 复验+一致性比对);结论三态背书/修正/退回如实。独立性成立(v5=训练方,compass=复核)。
- **Einsia 首触函呈批候用户**(草案 v1 在档 runtime/outreach/einsia_first_touch_draft.md,不发条款已解除——开业三链接全 live;checklist 第一步=用户过目署名/语气)。

### R447 · 2026-10-10 凌晨二(用户拍板落执行:PRECOR 双轨弹药全备✅——署名 c+投递 c 确认,arXiv tex 编译 COMPILE OK)
- **用户拍板**:署名 c+投递 c(双轨)——与 R382 初拍一致,确认知认落档(决策卡 APPROVED 注记)。
- **执行状态盘点[实测]**:步骤①署名落稿✅(R382 已落,Author 段 c 形态+检查单四勾);步骤②博客短版✅(PRECOR_BLOG_SHORT_20261009.md,R382 产出,工程师口吻+负结果原样+CTA——10/12 21:00 弹药);步骤③**本轮补齐**:全版→arXiv tex(arxiv_pkg/precors_arxiv/,Abstract+§1-7+表格 tabular+Fig1 png 入包+thebibliography 四实锚)——**pdflatex 编译 COMPILE OK** 产出 PDF;步骤④发后回链候首发后。
- 双轨两轨弹药全备:博客短版(开业 21:00)+arXiv 全版(同周窗)。遗留小项=arXiv 官方投稿时按其 meta 界面再核对 license 选项(发时动作)。

### R498 · 2026-10-10 晨卅三(轻轮:flywheel 代修 registry 追认✅——10961 对表闭环)
- #10961 flywheel 知会:registry.html"名词速览"段系其代修(commit dce50b9c,用户 10/9"四页全修"授权)——R455 时已注意到该段并知悉保留,本轮确认来源;本地版本(含 R434 修复+R458 勘误迭代)与该段无冲突,追认回函。
- 五项拍板清单候用户(R497 呈报):rerank 部署窗/Einsia 发送/mem0 方案 A/捐助个人决策/XERJ eval-answers 确认。

### R499 · 2026-10-10 晨卅四(两主件:公告提前上线✅[实测 200]+Einsia 网页排版版✅——"提前上线"与"对外材料排版纪律"两批评落实)
- **主件一=公告提前上线**("10/12 才上没有技术理由"批评成立):判分服务公告文 HTML 化(announcement.html,六能力表+定价边界+CTA 全链)→部署→**外网 200/3452B [实测]**——公告不再候 10/12,官宣节点仅剩传播动作。
- **主件二=Einsia 函网页排版版**(runtime/outreach/einsia_letter.html):批评"发 MD 是给 AI 看的"成立——对外信函改为 serif 排版网页(打印即 PDF,蓝框使用说明打印自动隐藏);MD 版保留作内部正本。
- **附记·daemon 事故收尾**:python3.13.exe 幽灵进程根因定谳+恢复完成(LISTENING 恢复);两 watchdog 仍 Disabled 候稳定后 enable;rerank 开关回滚态(候 remote 链路排障);daemon_start.sh 进程匹配 python3* 通配修=候白天。

### R502 · 2026-10-10 晨卅九(r87 复核收官✅[实测外网 live]——终判卡 0005 背书交付,SLA 大幅提前)
- **主件=r87 复核收官**:v5 提前发车(14:08,读数 14:10 完,快一个量级)→读数实体两份 JSON 拉回归档→**复核三件**(rewards 逐条审计 60 条/delta 复算 +0.950 UP/双时点复现)→**终判卡 nautilus-l1-0005 背书交付**(函 10967+ack 10966)——**SLA 大幅提前**(读数到手 ~40min 出卡,承诺 4h)。
- 终判:GRPO 训练有效性判定成立(delta+0.950>0.15 UP);如实披露两条件(逐 case 重推理候 r88/工单方向采纳);榜单锁版背书可用。
- 卡已 live(judge_status API 外网验证 pass)——**判读岗首张外部复核单收官,六卡全 live(demo+0001-0006)**。
- 附带:dev.to 5.5h 读数 0(冷启动);信箱清零。
- **主件一=公告提前上线**("10/12 才上没有技术理由"批评成立):判分服务公告文 HTML 化(announcement.html,六能力表+定价边界+CTA 全链)→部署→**外网 200/3452B [实测]**——公告不再候 10/12,官宣节点仅剩传播动作。
- **主件二=Einsia 函网页排版版**(runtime/outreach/einsia_letter.html):批评"发 MD 是给 AI 看的"成立——对外信函改为 serif 排版网页(打印即 PDF,蓝框使用说明打印自动隐藏);MD 版保留作内部正本。
- **附记·daemon 事故收尾**:python3.13.exe 幽灵进程根因定谳+恢复完成(LISTENING 恢复);两 watchdog 仍 Disabled 候稳定后 enable;rerank 开关回滚态(候 remote 链路排障);daemon_start.sh 进程匹配 python3* 通配修=候白天。

### R500 · 2026-10-10 晨卅六(主件轮:rerank remote 断连双加固✅TDD 5绿——keepalive+重试跨窗口)
- **主件=remote 链路加固**(R487 回滚悬置的排障落地):①隧道 transport set_keepalive(30s)(防 A100 SSH 瞬断,实测断连频发根因防护);②daemon _rerank_via_remote 失败自动重试 1 次(sleep 1s 跨隧道 reconnect 窗口;签名演进为 (scores, ok) tuple);③隧道脚本自含化(load_env 内联,plugin 目录独立可跑)+bat 保活副本就位。
- **事故一笔**:内联 python -c 转义把 daemon.py 写坏(
 变真换行)——git checkout 单文件恢复+改用 Edit 工具(教训:多行含 
 的代码注入禁用内联字符串);测试签名同步更新 5 passed。
- **rerank 状态**:双加固就绪(开关仍 off 回滚态)——重开条件=daemon 稳定(现渐进消化中)+remote 实测 3 连通;隧道 keepalive 需重启隧道进程生效(候下轮)。
- R501 补完:隧道进程已用 keepalive 版重启[实测 19879 LISTENING+transport up 1 tries]——R500 双加固全部生效,remote 链路就绪待 daemon 稳定后开测。

### R503 · 2026-10-10 深夜二(主件轮:🔴勘误第 9 例——读者抓出 int8"2 flips"数学矛盾,五发布面全修正✅)
- **读者审查抓真错**(dev.to 评论 arhancanli):int8 行"0.9828 + 2 flips"数学不能同时成立(2/291=99.31% 应过门;98.28%=5/291)。定谳[实测]:run.log 原始读数 agree=0.9828(291 题实测)为真值 → **flips 真值=5,"差 2 题"系判读档表述笔误**(2 为容错数误抄为 flips)。门判定不变(int8 98.28%<99% FAIL 维持)。
- **五发布面全修正**:blog.html(重部署外网验证)/arXiv tex+PDF 重编译/短文 draft md/dev.to 帖(PUT 更新)/PRECOR_BC_VERDICT 判读档勘误注记——**勘误纪律"当天修正"兑现**(读者当晚抓,当晚修)。
- **erratum 回礼**:rsi-bench#4 + XERJ#1138 各回评论致谢+修正告知(读者审查=判读岗质量的免费外审,两个渠道各答)。
- 深层教训:发布前数学自洽检查(每行 agreement×n 整除 flips)应入 PRECOR 发布 checklist——数字组合的内部一致性无人查过,读者一遍抓出。
