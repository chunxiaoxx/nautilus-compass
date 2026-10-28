# /goal — S2 亲笔提交→QC 反馈环(fresh session 提示词 · 2026-06-11 交接)

> 复制本文当 /goal 贴进新会话。你 = platform-soul(nautilus-core 对话框)。
> **Session-start 必读**:`FDE_BUSINESS_CHARTER.md` + 本文 + 设计 `docs/plans/2026-06-11-fde-org-production-engine-design.md`(§B 切片) + S1 plan `docs/plans/2026-06-11-s1-assignment-acceptance-plan.md`(同款范式) + memory `session_20260611_rsi_fde_walking_skeleton_closed_endtoend` + `reference_fde_workplan_playbook_artifacts_20260611`。

## 北极星(不变)
我 = 整个 FDE 原生 AI 组织生产 orchestrator。四层引擎(RSI拱顶/三流/七件agent职能/引擎+数据模型)。FDE 组织 = RSI 外部 fitness 引擎本身。🔴 fitness 永远外部(QC verdict+买方验收+真$),非内部 NAU。提质增效不替代:agent 做量+结构+QC,人(专家)做不可替代的真场景作者+终验。

## 已证转(别重验·6/11 binding-DONE)
- 引擎 walking skeleton 端到端闭合;**S1 派活+验收标准 完整闭环**(飞书派活表 `tbl69fankpoBhJfw`→poller `fde-assignment.timer` 每5min自驱→具名 claim→专家飞书领活·双验 claimed_by=expert:chunxiao + 飞书状态已领取)。代码 merge master(d32d510a2·26 green)。
- 当前在产真任务:`expert_t2_rsi_grounded_retrieval_20260612`(线2 教案·指派 chunxiao·状态=已领取·等亲笔)。

## 当务之急 = S2「亲笔提交→QC 反馈环」(全力推进·走骨架闭环)
专家交稿 → 平台 poller 拉提交 → QC 判 → 逐项 pass/fail+reason 写回飞书 → 专家改 → 过。**复用现成、surgical、TDD、接在已证转引擎上**。

**实现要点(参 S1 范式·`services/fde_assignment*.py` + cloud effect runner + systemd timer)**:
1. **飞书派活表加列**:「提交内容」(专家粘稿/附件链接)+ 状态值「已提交→QC中→已通过/已打回」+「QC反馈」列(逐项 pass/fail+reason 写这)。base `EOVhbQwA0a1HEOsgmxecgkBVnwh` / table `tbl69fankpoBhJfw`。
2. **纯核心**(`services/fde_qc_feedback.py`·TDD):读「已提交」行→取稿+task描述→调 QC→产 {overall_pass, items:[{id,pass,reason}]}→格式化成飞书回写文本。
3. **QC 判分(复用·别重造)**:线1 题=`harness/checklist_scorer.py`(checklist-from-task 先生成 checklist);线2 教案=`knowledge-tutorial-assembler` skill 的完整性+🔴反 AI 味校验。判分跑哪、LLM judge 怎么接,参 soul-scorer(`fde_scorer_runner.py` 范式·MiniMax/urllib judge·secrets 本地金库)。
4. **effect runner**(`services/fde_qc_feedback_runner.py`·镜像 `fde_assignment_runner.py`):飞书读「已提交」→QC→写回「QC反馈」列+状态→(过=已通过/不过=已打回带 reason)。
5. **部署**:scp cloud fork(只 scp 不 pull)+ systemd timer(或并进 fde-assignment.timer)。

**闭环判据(走骨架·binding-DONE)**:1 份**专家亲笔稿**(用户在飞书「提交内容」粘一段真草稿)→ 系统 QC → 逐项 pass/fail+reason 写回飞书 → 用户按 reason 改 → 再提交 → 过。全程不碰 CLI。⚠️ 同 S1:**最后"专家亲笔+改"那步需用户**(我不冒充·人是作者红线)——我把引擎侧(读提交→QC→写回反馈)做到 binding-DONE,留用户交稿+改。

## 🔴 红线 / gotcha(实证·别再踩)
- **线2 反 AI 红线**:买方跑 AI 检测·副驾驶 skills 只校验/查 AI 味·**绝不代写正文**。QC 反馈是"指出哪不达标",不是替写。
- **凭据域**:飞书 creds=本地金库 `~/.claude/.cache/.fde_api_secrets.env`(FEISHU_APP_ID/SECRET·本机鉴权)/ 平台 key=cloud .env(取进 env 不回显)/ cloud timer 飞书 creds 在 cloud `~/.fde_feishu.env`(chmod600·从本地金库管道来)。
- **verdict-join 遮蔽**(`api/fde_dispatch.py:157`):task_uid 有 verdict 即视图报 settled。QC 写 verdict 走 `fde_verdicts`(source=soul)·human-author 行 task_uid `expert_*`。
- **cloud=fork(soul-audit-increment1)·只 scp 不 pull**·本地 Win 测试用 `python` 非 python3。
- **防抢单**:human 行已被 `expert:` 占座·S2 不碰 claim(只读提交+写反馈)。
- QC effect runner 的 `_http` 要捕 HTTPError 返 envelope(S1 C1 教训·别让网络错误误判)。

## 落地铁律(治虎头蛇尾·设计 §D)
实际买方流量第一天走系统(用户那道真教案就是第一份)· 每片闭环=老路径废弃(QC 反馈不走微信/文件·只走飞书)· S1-S3 全闭判据=≥5 道买方交付物全程系统内流完+settlement 记账 · 每片 walking skeleton binding-DONE 才开下一片 · 2 session 没闭→砍 scope。

## 收敛纪律(anchor #4)
binding-DONE+冻结 scope。**只做 S2**(提交→QC→反馈环)。S3(交付+财务)/S4(三流喂RSI)/S5(PM+培训面板)= captured-but-deferred。别 diverge。

## 跨框 / 并行(背景·非本片主线)
- 轨1 RSI grounded 两臂(③泛化):A 簇 GPU `ssh -i C:\Users\chunx\Downloads\11111.pem ubuntu@43.166.8.20`(已验证·Tesla T4)·levenshtein 需先适配 harness 进 autolab_eval 格式·run-spec 已投 v5。
- 轨2 L2 棘轮:已喂 12 题 v1 样本·第2版需 v5 self-edit。
- 材料三形态(会议/招募):memory `reference_fde_workplan_playbook_artifacts_20260611`(飞书云文档+网页+md)。

关联 [[FDE_BUSINESS_CHARTER]] · [[session_20260611_rsi_fde_walking_skeleton_closed_endtoend]] · [[2026-06-11-fde-org-production-engine-design]]
