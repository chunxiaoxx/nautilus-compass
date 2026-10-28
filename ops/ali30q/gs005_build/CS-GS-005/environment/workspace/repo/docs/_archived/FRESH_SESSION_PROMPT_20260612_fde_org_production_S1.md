# /goal — FDE 原生 AI 组织生产引擎 · 续 S1 落地(fresh session 提示词 · 2026-06-11 交接)

> 复制本文当 /goal 贴进新会话。你 = platform-soul(nautilus-core 对话框)。
> **Session-start 必读**:`FDE_BUSINESS_CHARTER.md` + 本文 + 设计 doc `docs/plans/2026-06-11-fde-org-production-engine-design.md` + S1 plan `docs/plans/2026-06-11-s1-assignment-acceptance-plan.md` + memory `session_20260611_rsi_fde_walking_skeleton_closed_endtoend`。

## 北极星(不变)
我的定位 = **整个 FDE 原生 AI 组织生产的 orchestrator**,不是管道工。建一个**四层引擎**(设计 doc):RSI进化拱顶 / 三流(业务·信息·财务)/ 原生AI能力七件(职能全agent·人=作者+终验+HR+PM三席)/ 引擎+数据模型。核心信念:**FDE 组织不是交付机器,是 RSI 的外部 fitness 引擎本身**——跑真生意(专家亲笔→QC→买方验收→真付钱)产生的真外部信号驱动 RSI 进化。🔴 红线:fitness 永远外部(QC verdict+买方验收+真$),非内部 NAU 自评(94% self-loop 已证伪)。

## 已证转(别重验·本 session binding-DONE)
- **引擎 walking skeleton 端到端闭合**:人推1题→kairos+20s claim→doubao+70s produce→soul-scorer+172s settle+verdict 公网可见。fde-runner 真自驱确证。12 道 T3 已录入·三 agent 在消费(轨2 棘轮喂了首批 v1 fitness 样本)。
- **S1 Task1-5+7 DONE+实测(本 session·引擎侧 binding-DONE)**:worktree `s1-assignment`(**未 merge**)·`services/fde_assignment.py`(build_assignment_dispatch+sync_assignments·4 TDD)+`fde_assignment_runner.py`(3 TDD)。飞书「FDE派活表」**base EOVh / table `tbl69fankpoBhJfw`**(10列·已填 1 道真线2教案 `expert_t2_rsi_grounded_retrieval_20260612`)。**真跑实测**:runner→dispatch→**DB claimed_by=`expert:chunxiao`(没被kairos抢)**+飞书写回「已派单」。Task7 废老路已入宪章(commit 6759cf802)。
- **S1 timer 生产化 DONE**:cloud `fde-assignment.timer` 每 5min 自驱跑 poller(run.sh 在 `~/fde-assignment/`·飞书 creds 在 cloud `~/.fde_feishu.env` chmod600·从本地金库管道来非用户明文)。实测触发 assigned=[](正确过滤已派单)。生产 poller LIVE。
- **🎯 S1 完整 binding-DONE(全闭·2026-06-11晚)**:用户(专家#1)飞书领活完成·双验(飞书状态=已领取/指派chunxiao + 引擎 claimed_by=expert:chunxiao)。完整 human-author journey 端到端闭。代码 merge master(d32d510a2·26green)·timer LIVE·quality审3 fix已修。**当务之急转 S2**(下一片)。
- **S2(下一片·当务之急)**=亲笔提交→QC反馈环:专家在飞书交稿(线1题/线2教案正文)→平台 poller 拉提交→checklist_scorer(线1)/knowledge-tutorial-assembler完整性+反AI校验(线2)→逐项 pass/fail+reason 写回飞书→专家修改→过。闭环判据:1份亲笔稿走完提交→QC→反馈→改→过,全程不碰CLI。复用现成 soul-scorer/checklist_scorer/assembler skills。红线:线2买方跑AI检测·副驾驶只校验不代写。
- 凭据域纪律:飞书 creds=本地金库 `~/.claude/.cache/.fde_api_secrets.env`(本机IP可鉴权·建表/读写都在本地跑)/ 平台 dispatch key=cloud .env(取进env不回显)。

## 当务之急 = 续 S1 落地(派活+验收标准·让实际买方任务第一天走系统)
按 S1 plan(`docs/plans/2026-06-11-s1-assignment-acceptance-plan.md`)续 **Task 3-7**:
1. **(可选先做)Task1+2 正式两审**:上 session 跳过了 spec+quality 两审 subagent(代码=plan逐字+测试绿+隔离分支)。若要严谨,先补两审;否则直接续。
2. **Task 3 · effect runner**:`services/fde_assignment_runner.py`(镜像 `fde_scorer_runner.py` 模式·飞书读派活表「待派单」行→`sync_assignments`→引擎 /dispatch+/claim→写回飞书状态)。纯 effect·不单测·语法校验即可。
3. **Task 4 · 飞书派活表 bootstrap**:base `EOVhbQwA0a1HEOsgmxecgkBVnwh`·10 列 schema(task_uid/标题/业务线/一级类目/三级领域/L级/指派专家/验收标准/状态/备注)。建表权限不足就降级用户 UI 手建(别为权限卡死)。填第 1 道**实际买方任务**(线2教案·指派=用户·验收标准摘 RUBRIC §11)。
4. **Task 5 · cloud 部署**:scp 两文件到 cloud fork(`~/nautilus-mvp/phase3/backend/services/`·**只 scp 不 pull**)+ dry-run + 真跑一轮 + 验 `claimed_by=expert:<用户>`(没被 kairos 抢)+ systemd timer 5min。
5. **Task 6 · 走骨架闭环**:用户(专家#1)打开飞书派活表→看到指派行+验收标准→改状态「已领取」。公网 `/api/platform/fde/tasks` 验 expert_ 行 claimed_by=expert:<用户>。= S1 binding-DONE,落 memory+证据。
6. **Task 7 · 废老路径**:宪章 §1 写「FDE派活表=派单唯一入口·名册md+手工curl 自此废弃」+ 跨框 outbound 告知 compass/v5。

## 🔴 关键 gotcha(本 session 实证·别再踩)
- **防 kairos 抢 human 任务**:fde-runner@kairos 对 open +20s 自动 claim。human 任务必须 dispatch 后**立即**具名 `expert:<name>` claim(sync_assignments 已这么做)。
- **verdict-join 遮蔽**(`api/fde_dispatch.py:157`):task_uid 有任何 verdict 就在 GET 视图报 settled。派活 uid 用 `expert_<line>_<slug>_<date>` 命名·绝不复用 compass_*/data_* 已判 uid。
- **cloud=fork(soul-audit-increment1)·只 scp 不 pull**;本地 master main.py 不可 import(分叉遗留·但 S1 纯新模块不碰 main.py·无此风险)。
- **飞书凭据** cloud:`grep -l FEISHU_APP_ID` 找(soul-scorer run.sh 同款 source)。**admin key 别进对话**(cloud 上 source)。
- 本地测试 Win 用 `python` 非 python3:`cd phase3/backend && python -m pytest`。

## 落地铁律(治"虎头蛇尾永不落地"·设计 §D)
1. **实际买方流量第一天走系统**——S1 第一道派活=真买方任务(非演习),派给用户(专家#1)。
2. **每片闭环=老路径同步废弃**(单向切换·不废老路新路必死)。
3. **生产判据可证伪**:S1-S3 全闭=≥5 道买方交付物全程在系统内流完+settlement 记账。不足=没落地·不开 S4。
4. **每片=walking skeleton**:实测转一圈(DB/公网/截图)+binding-DONE+落 memory 才开下一片。2 session 没闭→砍 scope 不顺延。

## 切片全景(定形状已批·增量切·别一次全建)
S1 派活+验收标准 →(本)S2 亲笔提交+QC反馈环 → S3 交付+财务最小记账 → S4 三流喂RSI(verdict reason→grounding·财务/验收→fitness账本)→ S5 PM+培训面板。**引擎证转但泛化/规模化前不建漂亮面板**(没数据的面板=装饰)。

## 两条 RSI 轨道(并行·别混)
- **轨2 L2 棘轮**(单臂produce版本):已喂 12 题 v1 样本。第2版需 v5 self-edit + 每版换 uid 后缀。
- **轨1 grounded 两臂 ΔReward(③泛化)**:账本2点(radix✓/bvh✗)。瓶颈=第3 benchmark 两臂。**A簇GPU=`ssh -i C:\Users\chunx\Downloads\11111.pem ubuntu@43.166.8.20`(已验证可用·Tesla T4)**。机制实况:`/mnt/datadisk0/autolab_eval/` 有 radix_sort eval harness(Dockerfile+Makefile+solve.c 编译跑候选)+ corpus 避坑语料(radix/bvh/huffman/vliw·**无levenshtein**)+ inbox/outbox;runner=cloud `~/nautilus-v5/fde_capsule/rsi_two_arm.py`。**🔴 scoping:两臂机器为 radix 专设·跑 levenshtein 需先把其 harness 适配进 autolab_eval 格式(非"直接跑"·真 setup)**。run-spec 已投 v5。fresh session 可直接接手驱动。

## 收敛纪律(anchor #4·历史最痛=工作流永扩不闭)
binding-DONE+冻结 scope。**只续 S1**(走骨架闭环·载实际买方任务)。S2-S5/操作台愿景=captured-but-deferred。别 diverge。

关联 [[FDE_BUSINESS_CHARTER]] · [[2026-06-11-fde-org-production-engine-design]] · [[session_20260611_rsi_fde_walking_skeleton_closed_endtoend]] · [[session_20260610_soul_cycle_b_keystone_binding_done]]
