# 🎯 LOOP STATE · 单一真相源(SSOT)· 所有对话框 session-start 必读

> **这一份是当前闭环状态的唯一权威。** goal 命令 / FRESH_SESSION_PROMPT / 各框记忆与此冲突时,**以此为准**。
> 🔴 **变更协议(治精神分裂·anchor #4)**:任一框改了"当前闭环目标 / 下一动作 / 卡在" → **先改这四行,再开工**。不先改这里 = 各框拿过期框架 = 精神分裂(本 session 的病根)。
> canonical 在 `nautilus-core/LOOP_STATE_SSOT.md` · 副本同步各 repo 根(同 FDE_BUSINESS_CHARTER 机制)。

---

## 🔴 7/6 v3 · /goal 落地(用户拍 · 细化 7/5 收口 · 当前最高权威目标)

**唯一目标**:把已跑通一次的收敛闭环(ENG 基准 × RSI × FDE · 一鱼两吃)从 **one-off** 变成
**(a) 活 producer 自持产出(income 自动越 98 持续涨)+ (b) 已交付甲方(11 题入飞书派活表)**。
不扩到 1000,不开新战线(守 7/5 收口)。

**已落地一次(7/6)· 带诚实标注**:GenOpt JobShop trajectory → producer 9000009 persist
→ `soul_canonical_verify.py` 复现 97.6047 MATCH → PATCH external-verify → `total_income` 0→98
(平台史上第一行外部 gate income)。判据1 ✅(SSOT 声称)/ 判据3 ✅ / 判据2(Kairos income=0)⚠️。
⚠️ income=98 / 1 条 verified 是 SSOT 声称值,**compass 探针 creds 失效未独立复核** —— 与"引擎自循环
停摆一个月被 verdict 刷屏遮"同类病(无独立探针 = 信剧场)。

**下一 binding-DONE(外部可证 · 全成立才算闭)**:
1. **自持可重复**:活 producer(nautilus-prime-001 / 9000009)cycle 产【可复现完整解】GenOpt
   trajectory → soul_canonical_verify MATCH → external_verified=True → total_income 越 98 持续涨,
   **且 compass 探针独立复核到**(查 DB 真值,不信 SSOT 散文)。
2. **已交付**:11 题达 buyer §2 三条(ship 5/5 + frontier_eval 9/9 + GPT5.5 valid + doubao pass@5 ≤ 0.6)
   + 入飞书派活表(GET 回读)。

**各框下一动作(FDE 只做业务不背 infra)**:
- **V5**:🔴 把 nautilus-prime-001 cycle objective 从"改自己内务"(stake/recovery/audit)扭到
  "产可复现 ENG trajectory → persist → 入账";续跑自治但产出绑中心环。勿停 PID 884064(=活 agent)。
- **soul-verify**:新 trajectory 跑 soul_canonical_verify → external_verified=True(唯一入账门)。
- **platform**:doubao 难倒 10 题(ARK 本机已通)→ M1 · 维护 backend/PATCH 端点。
- **compass**:🔴 ① 先修 liveness 探针 DB creds,拿回独立验闭环真态能力 ② feishu 写函数做 11 题 submit
  ③ 探针盯 income 持续涨 + ledger GREEN。
- **用户(一次性)**:飞书 OAuth user_access_token → 交 compass 写。
- **FDE(轻)**:只定 11 题业务/派活表内容,不背 token/infra 阻塞。

**新增守则(叠加下方 5 坑护栏)**:
- 🆕 **agent 层反 D**:自治 agent 的 cycle 只改自己不产外部价值 = agent 层维护陷阱;objective 必须绑
  中心环产出(V5 定,compass/platform 独立探针观测,不信自报 soul_alive)。
- 外部验证入账只走活 producer(9000009 / nautilus-prime-001),不复活已死引擎自循环(6/3 停摆剧场)。
- "验活"要独立探针,不信自报。

**🔴 7/7 fresh delta(compass 同步 · 剧场被 agent 自审 grounded)**:
- income 已 98→**188**(platform 加 QAOA 90 + C 口径双门 · 见下 close_loop 判据 1)。platform 自己标注:188 仍是**手摇链**产出,**自持(producer cycle 自产)+ compass 独立探针复核 = v3 binding-DONE 仍开**。
- nautilus-prime-001 cycle 115715(7/7 10:18)自审:`fde_claim_produce` = fake-success 工厂,**1233 actions / 0 settled**;cron **220+ cycle 0 执行**。= agent 从内部证实了"信剧场"。它现在修自己执行管道(cron / 注册 / settle),让动作能落地。
- ⇒ "自持可重复"卡在更深缝:**agent 管道(cron 执行 + 动作 settle)先修好,才谈 objective 绑 ENG**。V5 turf,进行中。
- ~~compass 探针缺口更卡:psql creds 失败 + verdict GET 被拒~~ → ✅ **7/7 compass ① DONE**(commit 720c17f · `ops/economy_liveness_probe.py` + 12/12 test + live 实测)。原"psql creds 失败"是误诊:compass_sub ssh-tunnel 连接**通**,有 SELECT on fde_verdicts/engine_cycle_outcomes/agent_tool_calls/poi_credit 等 6 表;verdict GET 走 `/api/platform/control-plane`(公开可读)+ DB 双路解决。**独立裁判已建**,grounded 复核:
  - income **188 独立复现**(不信自报):fde_verdicts 里 external_verified∧overall_pass 的 sum(round(score)) = JobShop 98 + QAOA 90 = 188。TSP 97.63 verified 但 overall_pass=False 未铸、gate-probe 未铸 —— canonical C 口径全对上。
  - "剧场"独立坐实:engine_cycle_outcomes last_cycle=**33.8d 前**、24h=**0**(总 49)= 引擎自循环停摆一个月属实;agent_tool_calls 却 last=now/329k = agent 空转但不落 cycle/income。⇒ **binding-DONE #2 自持仍开**(income 冻在 188 · 无自产增长),V5 修管道先行。
  - 唯一剩缺口 = `agent_survival.total_income` 权威值无 grant(permission denied)→ 已发合约请求 platform GRANT SELECT(`cnt_compass_platform_grant_survival` · scanner surfaced · verdict-derived 兜底不阻塞)。
- ✅ **7/7 compass ③ DONE**(commit 67f1788 · `--watch` income growth watch):live 两跑 = FIRST(记 188)→ **FLAT**(188→188)。**grounded 信号给各框:income 当前冻在 188 · 无自产增长**(引擎停摆坐实)· V5 修好管道 producer 自产入账后,watch 才会显 GROW = binding-DONE #2 达成的可观测判据。
- ✅ **7/7 compass ② 假依赖解除(confound 核出 · 守则"confound 先核")**:goal 说"等用户 OAuth user_access_token"是**假依赖**。实证:`feishu_client.py`(cloud `/home/ubuntu/fde-toolbox`)用 **`tenant_access_token`(app 级 FEISHU_APP_ID/SECRET · 金库已有)**,**不需用户 OAuth**;`create_bitable_record`/`update_bitable_record` 写函数齐全;FDE_CHARTER §3 证 compass 已写过飞书(L3表 recvm5L3iFlatJ)。
  - 原"写不了"真根因 = **金库 CRLF 行尾 + feishu_client ENV 默认硬编码 Windows 路径**(跨机同步残留)→ `\r` 污染 secret(len 33 而非 32)→ auth 10003。**已修**(ENV→`expanduser` portable + `_env()` strip · cloud 备份)· **端到端验证 tenant_token LIVE + 读出题表 tblhD4O4f0esTyXc 43 行**。
  - ⇒ **compass ② 写路径现在完全 LIVE**。binding-DONE #3 的 compass 部分**不再等用户**;真剩余依赖 = **FDE 定 11 题内容 + 确认目标派活表 id**(FDE 轻 turf),compass 拿到即写+GET 回读。
  - 🎯 **7/7 compass GET 回读基线(#3 证据机制已跑)**:base `EOVhbQwA0a1HEOsgmxecgkBVnwh` 5 表 = 数据表 / **L3基准样例 `tblhD4O4f0esTyXc`(43 道产出题·第三类·多数难倒 doubao)** / **FDE派活表 `tbl69fankpoBhJfw`(=goal 说的"派活表"·21 行)** / 专家库CRM / 第三类经验复现(compass)`tblvR6BCSBH4IG59`。**派活表现状混杂**(真任务 drift_detection ✅5/5、rsi_grounded ❌打回 + finance/legal/ecommerce placeholder + my_test_001 等测试垃圾)· **无干净 11 题 buyer 集**。⇒ #3 真缺 = **FDE 从 43 题/专家任务选定 11 题达 buyer §2 → 填派活表**(FDE 内容 + soul QC turf);compass 写路径+GET 回读全通,给到即闭 compass 半(合约 `cnt_compass_fde_11q_content`)。
- 🔴 **7/7 compass 独立诊断 binding-DONE #1 根因(守则"不信自报"· 发 V5+platform 合约)**:用新 DB 读能力核 agent 自审"1233/0 settled / cron 0 执行",发现**方向对但表述误导 + 定位可执行病灶**:
  - agent 循环**猛跑不是 0 执行**:nautilus-prime-001 = 240k tool calls · 24h 8154/93.8% success/last=now。
  - **fde_claim_produce = 假成功工厂 DB 坐实**:24h 1268/1268 success 但 output `claim_id=None`(只吐 hint 从不真 claim)。
  - **真 settle 工具打 404**:`send_to_agent`→`/api/platform/messages` GET+POST **独立 curl 确认 404**(112/112 fail)· `nautilus_claim_bounty` 77/77 = ERR:404。疑 v3 未 merge/部署。
  - **两本账背离**:agents.total_earnings(9000009)=**0**(external-verify 铸的 188 只写 agent_survival 未传播)。
  - ⇒ **0 settled 根因 = produce 假成功 + settle 路由 404**,非"cron 不 fire"。修复靶点:platform 补/部署结算路由(`cnt_compass_platform_settle_routes_404`)· V5 修 produce 假成功判定(`cnt_compass_v5_fake_success_produce`)。
  - 🎯 **404 已定性到 ground truth(compass 查 nautilus-core code)**:`messages_router`(prefix `/api/messages`)在 main.py 已 import(L74)+mount(L587)· 分支 `soul-distill-deploy`(c857f3e1c "A2A Messages")。同 main.py 的 `control_plane_router`(L643)**live 200** 但 `/api/messages` **live 404** = **部署 backend 是旧版 = deploy/merge gap**,坐实 goal "platform 待 merge main"。⇒ merge/deploy `soul-distill-deploy` 修 messages 404(+ 前缀 mismatch)。
  - ⚠️ **compass confound 核实后修正(守则"confound 先核")**:**messages 404 是独立 a2a 故障 · 不是 income 冻结主因**。核实:pf_claim_bounty **是通的**(150/154 success · claim marketplace bounty)但喂 dmas.bids 不喂 income;income(188)只由 GenOpt trajectory external-verify 喂,是 **agent 9000009(h800-genopt-runner)挣的,非自治 agent nautilus-prime-001**。⇒ **income 冻结核心主因 = 自治 agent fde_claim_produce 假成功(claim_id=None)产不出可验证 trajectory** → 无新 verify → 冻 188。精确对上 goal "objective 绑 ENG 产出 / 不产外部价值=维护陷阱"。**binding-DONE #2 解锁键 = V5 把自治 agent objective 绑到'产真可复现 GenOpt trajectory→verify→mint'**(非改自己内务),非 messages 404。

---

## 🔴 7/5 收口(用户拍 · 暂停扩张)· 覆盖下方 7/2 四行

用户 7/5 反馈"过往一周工作比较混乱"→ 拍 **D 暂停扩张,清点收口**:
- **不产新 GenOpt 题 · 不碰蒸馏 · 不开新战线**
- 锁 **11 题交付甲方(M1+M2)= 最小可闭环**(11 题全 OR JobShop Easy · ship 5/5 + frontier_eval 9/9 + GPT5.5 valid · 缺 doubao 验证 10 题 + user_access_token)
- 完整规划 = `docs/plans/2026-07-06-genopt-rl-eng-delivery-convergence.md`(8 收敛缺口 + Phase 0-4 + 6 里程碑 + 各框分工)
- 混乱根因 = 一周 60+ commit 0 binding-DONE · 417 散落 outbound(物理证据)· 见 memory `feedback_week_chaos_pause_expand_consolidate_20260705`
- **下方 7/2 四行 = 收口期冻结**(GenOpt 扩量/蒸馏 全 park,收口完再解冻)

---

## 📍 当前活状态(四行·last-updated 2026-07-02 深夜 · 收口期冻结 · 见上方 7/5 收口)

| 字段 | 值 |
|---|---|
| **当前闭环目标** | **双主线(用户 7/2 拍)**:(A) 🆕 **GenOpt RL 1000 题交付**(买方新单 · Frontier-Eng generative optimization 范式 · SPEC=`vtf/BUYER_SPEC_GenOpt_RL_20260702.md` · 各框协同统筹)· (B) 证或杀蒸馏(维①)。**两线合一处:GenOpt 题目=连续分数+verifier+迭代轨迹=ALE 同构蒸馏燃料·一鱼两吃** |
| **下一动作** | ① ✅ **H800 到位**(7/2 · `ssh -p 34467 root@connect.westc.seetacloud.com` · 80GB · torch2.7+trl/peft 栈全 · 数据盘 250G)② ✅ **JobShop pilot GPT5.5 N=3 真数据**(7/2 · H800 端跑 · seed=24.7 → best=94.89 · gap=0.7022 · **Easy** · 3 轮:r1 timeout / r2 92.69 / r3 94.89)③ ✅ **GenOpt 第二题 TSP 真数据**(7/2 · H800 端跑 · seed=89.5152 → best=100.0 · gap=**0.1048 · Hard** · 3 轮全 100/138s/154s/164s)· 双题端到端通 = Easy/Hard 两端都打到 ④ ✅ **verifier 三铁律 QC**(`genopt_factory/tools/verifier_qc.py` · 确定性+只读+超时 全 PASS)⑤ ✅ **5 题真 grounded + v7 二次标定**(7/3 · 4 难度档跨 5 题 · JobShop Easy 0.6843 / TSP Hard 0.1048 / Attention Hard 0.2293 / Cache Hard 0.1092 / BinPack Easy 0.6667)⑥ ✅ **第 6 题 Quantum:qaoa_maxcut_v1_001 端到端通**(7/3 · 7 synthetic instances · baseline 64.90 / reference 78.19 · gap 上限 0.133 Hard)⑦ ✅ **批量化基建落地**(`produce_task.py` 工厂 + `gapclosed_batch_runner.py` K 题并行 + H800 worker)⑧ ✅ **4 框催球 outbound**(7/3 0:35 · 截止 9:00 · 不接球我代行)⑨ 蒸馏候选 A:**不阻塞于 GPU** · 待 soul 择机 |
| **负责框** | **platform(本框)= GenOpt 统筹+工厂资产+H800 运维+OR 域生产** / compass=KernelEngineering+ComputerSystems 域(KernelBench 资产复用)+ env 审查 / V5=批量题目变体+GPT5.5 轨迹批跑 producer / soul=verifier 三铁律 QC+难度分级判定+交付前把关 / FDE=飞书交付表对接 |
| **卡在** | (a) **GPT5.5 中转站不稳=真阻塞**(本机 b2xwto5km/b0urzez29 三轮 502/close 全断;**H800 端 qixuw OPENAI_BASE_URL 直连稳定** ⇒ 真工作路径走 H800,本机 driver 仅备援)· 备援口径=Minimax M3(7/2 用户说额度充足,本 session 暂未压测)(b) **难度旋钮实证**(JobShop Easy 0.7022 / TSP Hard 0.1048 / Attention Medium-Hard 漂移 / Cache Hard 0.1087 / BinPack Easy 0.6667 / QAOA 待测)⇒ **baseline 写法决定难度可控**;GPT5.5 N=3 seed 漂移 ⇒ **多跑取众数**真必要(v7 二次标定验证可重现性)(c) **5 → 6 题扩量**· 5 域覆盖(OR 3 题 / KernelEng 1 题 / ComputerSys 1 题 / Quantum 1 题 · 第 5 域 Robotics 待出)· 真生产应 50+ 题入表(d) **破自循环 Step 2/3 pending** · 等 A800 真 verified verdict(GenOpt Easy/Hard 不算 — 走 soul canonical verify 链才真) |

## ✅ close_loop 判据(6/29 23:30 grounded 实测 · 纠正之前推断)
1. ✅ **7/6 首次成立 · 现值 188**:`agent_survival.total_income`(agent 9000009)0→98(JobShop)→**188**(+QAOA Hard 档 90 · C 口径下第一笔)。链 = 完整解轨迹 → persist → `soul_canonical_verify.py` 独立复现(JobShop 97.6047 / QAOA 90.3195 / TSP 97.6311 全 exact)→ PATCH external-verify。**🔴 C 口径(7/6 用户拍)**:验证与经济解耦——external_verified 只看复现;income 加双门 = ① overall_pass(难度档合格·Rejected/too-easy 不铸)② 同 (task_uid×producer) 只铸一次(堵同题重跑刷钱)。TSP(Rejected 档)只翻验证标不铸;部署竞态误铸的 98 已删账修正(286→188 · 有痕)。⚠️ 诚实:188 仍是平台框手摇链产出,自持(producer cycle 自产)+ compass 独立探针复核 = v3 binding-DONE 仍开。<br>*旧(6/29):24h delta=0。*
2. ⚠️ Kairos `agent_status=alive` · `survival_level=GROWING` · `survival_income=0`(schema 没 `balance` 字段 · 之前"balance=8 被冻"是过时推断 · 当前不 critical 但 income=0 是另一回事)
3. ✅ `platform_nau_ledger` 24h delta=**+1250** · 71 行新增 · last_entry **2026-06-29 23:30:51**(1 分钟前)· PoI 账本**活跃增长** · 不只 6/29 续23 报的"1299→1507" · 持续

## 🛡️ 守教训护栏(防 5 坑·6/29 用户拍"蒸馏一条线+守教训")
1. **n≥12 才跑 LOO**(verdict-gate commit 210e0fd24 拦 n<12·防 whipsaw 教训2)
2. **易 django PROVEN → 须非易料复证**(排 over-fit 假迁移·教训3)
3. **confound 先核再下结论**(教训3·本 session 两次找错 FDE 路径=戒)
4. **SSOT 钉死+广播四框**(治精神分裂·教训4)
5. **ship 了必验活**(教训5·FDE cloud runners/compass 探针都得验)

## 🔴 6/30 grounded 纠正 · 7 个推断错(踩教训#3)

| # | 之前推断 | **grounded 真值** | 实证 |
|---|---|---|---|
| 1 | "cloud 是 V5 跑点" | GPU 端(43.166.8.20)才是 V5 真跑点 · cloud = control plane | ssh gpu /home/ubuntu/fde_run/ 在 |
| 2 | "V5 6/29 第 3 道缺位" | sklearn-10297 真到位 · A_bucket=true · doubao 1/1 error | strong 161229/163936/212635 三次 resolved · doubao 163936 error_ids 含 |
| 3 | "soul verify 工具不在触及范围" | GPU 端有 `/home/ubuntu/verify_aclass.py`(1115B · 6/26 20:43)+ `verify_pathA_one.py`(1017B · 6/24) | 文件在 · 能跑(双 arm docker verify) |
| 4 | "A-class n=2" | **n=4 真 grounded** = django-12113/13220/sklearn-10297/django-13551 | 6/26 doubao baseline = 0/2 unresolved · 6/29 三次 strong verify · 6/29 doubao 1/1 error |
| 5 | "复核真阻塞 = V5 产料慢" | 不是产料慢 · 6/29 verify 真跑成功 · 155206 transient error(33 分钟后恢复) | 161229/163936/212635 都成功 |
| 6 | "H100 到位后立刻跑 LOO" | n<12 gate BLOCK · 不能跑 · 但 LOO 不是 H100 第一刀 | verdict-gate commit 210e0fd24 拦 |
| 7 | **"docker images 空 = 真阻塞"** | ❌ **docker images 15 张全在且能跑** · 不是空不是 corrupt | 7 swebench env + 1 base + 4 ale + 1 rust + ubuntu · 实测 swebench 4 张 Python 3.11 OK |
| **8** | **"T4 GPU 还在"**(7/2 推翻) | ❌ **T4 (43.166.8.20) 用户 7/2 主动关闭** · A800 租赁中替代 H100 | ping 100% loss · SSH timeout |

**关键反转**:A800 第一刀候选 A 锁定(verify_pathA_one n=4 复证)· 不再是"部署 swebench 镜像"(已不空)· 见下"🎯 A800 第一刀候选(锁定候选 A)"。

## 🎯 A800 第一刀候选(SSOT 锁定候选 A · 用户 7/2 拍)

| 候选 | 内容 | 数据点 | 与 SSOT gate | 状态 |
|---|---|---|---|---|
| **A · verify_pathA_one 真跑 n=4 复证** | GPU 端 verify_aclass.py 真跑 django-12113/13220/sklearn-10297/django-13551(强解+doubao 双 arm docker)· 拿 f2p 真数据点 | 真 f2p 真数据 · 验证 V5 SWE producer 真干净 · 不需 n≥12 | ✅ 不撞 LOO gate · 真 grounded 复证 | 🔴 **锁定** · A800 到位后立刻跑 |
| B · LOO n=4 INCONCLUSIVE | distill_loo.py 真跑 n=4 · verdict-gate 自动降级 INCONCLUSIVE · 守 n≥12 gate | 机制活信号 · 不下结论 | ⚠️ INCONCLUSIVE 走通 · 不算 verdict | 🅿️ 暂缓 |
| C · 等 V5 续产到 n≥12 | 等 V5 A800 上产 frontier-eng 等 5 类 → n≥12 → 真 verdict | 真 verdict · 但 A800 后才能续产 | ✅ 不踩 n<12 gate · 但零数据点 | 🅿️ 暂缓 |

**A 锁定**(用户 7/2 拍)· A800 到位后第一步 = 真 grounded 复证 · 拿 f2p 数据 · 不踩 gate · 同时验证 V5 SWE producer 真干净(RADIX-style 真赢信号)· 出 f2p 真数据为 LOO n=12 准备。

## 🅿️ Parking Lot(冻结·蒸馏 verdict 出前不碰)
- 维②经济环(credit 口径/结算腿 liveness)· compass MCP 耦合(Phase 1-4)· 平台 mint_mcp_token · FDE 招募/RBAC/4 skill 发版 · content-engine 命名合约 · 维① KILL 资产保留(未来上 H800/换真难料重启)
- **🅿️ GPU park**:T4 已关闭 · A800 租赁中(等 IP/SSH config)· 期间 platform-soul 守 SSOT 不动其他框 · verify_aclass.py 路径待迁移(原在 T4 /home/ubuntu/ · 6/30 确认能跑)
- **FDE 切飞书多维表格**:执行路径已变(飞书→多维表格→「ECC-三类业务生产管理」base 14 表)·非 cloud systemd runners。FDE 下次同步进 SSOT 细节。

### 🛠️ 破自循环通道 + Producer 注册化(锚点③ 治根 · 7/2 用户拍)
- **实证**(6/29 grounded DB):fde_verdicts 今日 190 全 `compass/bench_eval` source·task_uid 全 `compass_exp_*_automint_<ts>`·engine_cycle_outcomes 今日 0·`soul_alive=True` 靠自循环刷的剧场。
- **scope**(用户 6/29 拍 B·微破):仅为**蒸馏 verdict 留通道**,不变成通用维②清理(踩教训1)。
  - 加 1 列:`fde_verdicts.external_verified bool`(默认 false·仅 soul canonical verify 标 True)+ `external_verified_at timestamptz`。
  - 改 1 判据:`control_plane.soul_alive` 按 `MAX(external_verified_at)` 新鲜度算(非 cycle stale_hours)。
  - 内循环(auto-mint / bench_eval)继续跑·只是不再"算活/入账"——**不改 compass 内部逻辑**(V5/compass turf 不动)。
  - 不写新服务/不写新 runner/不写新 webhook——复用现有 soul canonical verify 加 1 行 UPDATE。
- **🔴 实施进度(7/6 更新)**:
  - ✅ **Step 1 已完成**(7/2):ALTER TABLE fde_verdicts 加列 `external_verified` + `external_verified_at` · 实测 db 验证 ✓
  - ✅ **首条 external_verified=True 已达成**(7/6 · GenOpt 链):第一刀 `PATCH /api/platform/fde/verdict/{id}/external-verify` 端点上线(4 防剧场护栏:幂等 / 只 False→True 入账 / 只整数 producer_agent_id / verifier≠producer)+ 第二刀 producer 持久化完整解 + `soul_canonical_verify.py`(preview 轨迹拒 / sha 对账 / determinism 自检 / 容差判定)· verdict `…-d01cfd4d` 复现 MATCH → income 98 入账 agent 9000009 · 旧不可复现轨迹的 4 条 verdict 保持 False(诚实)
  - ✅ **Step 2 已完成**(7/6):`control_plane.py` soul_alive 判据改按 `MAX(external_verified_at) WHERE external_verified=true` 新鲜度算(<48h)· cycle 降级为 metadata · TDD 3/3 + 部署 cloud 实测(soul_alive=True 由外部验证撑 · last_cycle_at=6/3 暴露引擎自循环停摆一个月 · 老判据靠 verdict 刷屏遮着)· 顺修 PATCH 端点 naive-utcnow 进 timestamptz 偏 -8h 时区根因
  - 🅿️ **SWE 链 verify(候选 A verify_pathA_one)仍等 A800**:与 GenOpt canonical verify 是两条链,不混
  - 🏀 **球→V5(7/6)**:cloud `~/genopt_delivery/` runner 轨迹没存完整解(582B)→ 过不了 canonical verify → 不可入账。修 runner(cloud `~/genopt_live/tools/gpt55_local_runner.py` 可直接用)后 7/7 凌晨 7 条 jssp 产能接上 income 链。详 V5 repo 根 `_INBOUND_FROM_PLATFORM_20260706_trajectory_reproducibility_ball.md`(untracked·V5 gitignore 拦 inbound 文件)
  - 🔧 **backend 部署规程(7/6 事故后钉死)**:cloud backend = `nautilus-backend.service`(systemd 管 · 自动重启)。**部署 = scp + `sudo systemctl restart nautilus-backend`,禁手工 kill/nohup**(7/6 两次手工重启制造双进程打架 → 旧代码抢答 → TSP 误铸;广谱 pkill 还差点误杀他框服务,systemd 自愈救回)。pgrep/pkill -f 会自匹配 ssh 命令行,用 systemctl 或精确 pid。

### 🛠️🆕 Producer 注册化(锚点③ 真根 · 7/2 用户点破 · 必须执行)

> **用户点破**:"你就是平台和 soul 对话框,都是你" → Claude 对话框(我)≠ 真 producer · H800 端 Python 进程才是真 producer · 必须走 `api/agent_first_register` 拿整数 agent_id · 不能以裸字符串 "harness" 跑数。

**根(SSOT §0-ARCH 早已钉,本 session 才真执行)**:
- H800 端跑出 JobShop Easy(gap=0.7022)· TSP Hard(gap=0.1048)的真 grounded 数据 ✓
- 但 **producer 身份没注册** = "harness" / "miniconda python 进程" 裸字符串 = **踩 §0-ARCH 红线**
- 真要"持续生产"必须:① H800 harness 注册成真 agent 拿 agent_id · ② 每次 trajectory 走 soul canonical verify + 写 fde_verdicts 行(带 producer_agent_id binding)

**实施步骤(7/2 起 · 等 backend 通就执行)**:
1. ✅ **写 `genopt_factory/tools/register_h800_producer.py`** — challenge→答→拿 agent_id(走 /api/agent-first/{challenge,register}·capabilities=["code"]→answer="55")· 凭据存 `~/.nautilus/h800_harness_credentials.json`。
2. ✅ **写 `genopt_factory/tools/persist_trajectory_verdict.py`** — trajectory JSON → fde_verdicts INSERT(带 verdict_id 唯一 · source=`h800-genopt-runner-<agent_id>` · overall_pass · score · items[] · artifacts{} · external_verified=False 待 soul canonical 标)。
3. 🅿️ **Backend 当前未起**(localhost:8000 + postgres:5432 都 conn refused · 7/2 23:30 实测)· 注册脚本 dry-run 通了 · 等 backend 一键执行。
4. 🅿️ **H800 harness 加 `--producer-agent-id` 入参** — 让 trajectory 落 fde_verdicts 时带真 producer 标识(治根 vs "harness" 裸字符串)。
5. 🅿️ **已有真 grounded trajectory 重新走 binding**:JobShop `gpt55_trajectory.json` + TSP `gpt55_trajectory_h800.json` · backend 起来后用 `persist_trajectory_verdict.py` 一键写库。

**阻塞 vs 已就绪**:
| 件 | 状态 |
|---|---|
| 注册脚本 | ✅ 写完 · dry-run 通 · 等 backend |
| 持久化脚本 | ✅ 写完 · dry-run 通 · 等 backend |
| H800 harness 改造(加 agent_id 入参) | 🅿️ 下 session(等 backend 通 + agent_id 真值) |
| 已有 trajectory 入库 | 🅿️ 同上 |
| 后续生产走"register→跑→persist"全闭环 | 🅿️ 等 backend · 但**脚本 + SSOT 协议已固化** |

**底线**:本 session 没新增任何"裸 producer 跑数"。JobShop/TSP 已跑出的 trajectory **标 `provisional · producer-pending`**,只有 backend 通 + 真注册 + 真持久化后才转 `verified · producer=agent_id`。

## ✅ binding-DONE 判据(外部可证·任一框可查·治目标无限膨胀)
闭环 = 下面三条**全 grounded 成立**:
1. `agent_survival.total_income` 因真外部验证产出(soul-canonical / held-out)增长
2. Kairos 脱离 critical(balance ≥ min 20·当前 8 被冻)
3. PoI 账本恢复增长(compass `probe_ledger_growth` 从 DORMANT → GREEN)

**判据成立前不算闭·不开新战线。** 不是"我觉得行了",是这三条 SQL/探针返回真值。

## 🅿️ Parking Lot(冻结·闭上面环之前不碰)
- ~~维①蒸馏 KILLED~~ → **6/29 推翻 KILL·正确 unblock**(用 n≥12+非易料重跑·非 n=2 whipsaw)。
- **SWE 批产到 n≈12**:进行中·V5 turf·优先非易 django 避 over-fit confound。
- FDE 三类业务线 / content-engine 命名合约 / 其它 → parking。

## 📌 6/29 推翻 KILL 的诚实条件(防 whipsaw)
- **不是** n=2 LOO(统计无意义·verdict-gate BLOCK n<12·撞 over-fit confound)。
- **是** V5 续产到 n≥12(同族 django 或换真难非易燃料)→ soul verify → 借 compass GPU(GPU 服务器一直开着·非阻塞)→ distill_loo --kind swe → 对比 ALE 0.0833。
- 若易 django PROVEN → 须用非易料复证(排 over-fit 假迁移)·否则不算破墙。

## 🧭 收敛机制(为什么这样安排·别走回头路)
- **同步** = 这份 SSOT(各框读同一份·变更先改这里)。
- **收敛** = 把闭环**执行搬出对话框、进常驻自治 agent**(daemon/conductor/结算 cron 跑 systemd·对话框退回战略/验证/纠偏·不 crank)。对话框是脚手架·不是执行路径(§0-ARCH)。
- **落地** = 一次一个外部可证的 binding-DONE(上面判据)。
- 详 `feedback_workflow_lock_goal_until_done` + `reference_platform_history_architecture_review_20260622`(最大未闭缝=producer 没收口到注册自主 agent)。

## 各框 turf(不越界)
- **platform-soul**:平台 infra / 结算 / dispatch / 部署 / SWE eval / benchmark verify / 标准 QC。
- **soul-verify**:canonical verify(verify_pathA_one)/ 难度门 / verdict-gate。
- **V5**:producer(产候选/轨迹)/ daemon 大脑 / external_reward 入账 / RSI。
- **compass**:记忆/recall/PoI/drift/governance / benchmark env+eval / liveness 探针 / feishu 读写。

---
*维护:闭环目标/动作/判据有变 → 改本文件 canonical(nautilus-core)+ 同步各 repo 根。变更同时记 memory + 广播。*
