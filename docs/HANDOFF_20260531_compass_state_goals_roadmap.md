# nautilus-compass · 现状 / 目标 / 路线图 交接文档

> 写于 2026-05-31。目的:把 compass **是什么、到哪了、要去哪、怎么去** 想清楚、说提炼。
> 触发:dev.to 文章发表后,感觉对外表述"不够清晰提炼" → root 是核心价值主张还没收敛。
> 本文不堆术语,一段说一件事。细节链接到对应 memory / 代码。

---

## 0. 一句话:compass 是什么(待拍板 · 见 §5)

当前对外有 3 个并存的说法,这是"不够提炼"的根源——**没有选一个当 #1**:

| 候选定位 | 一句话 | 证据强度 |
|---|---|---|
| A. black-box memory | "唯一不烧 LLM token 抽取就能存的 agent 记忆层" | 强(技术真差异化 · 14× 便宜) |
| B. drift detection | "防 AI 重复犯你已经标过的错" | 中(机制真 fire · 但 act_on 才 9.87%) |
| C. multi-agent reliability infra | "无编排器的多 agent 协作可靠性底座" | 中(4-dialog field log 真实 · 但 N=1 operator) |

dev.to 文章同时讲了 B+C,所以读者抓不住重点。**2026-05-31 用户拍板:#1 = C(多 agent 可靠性底座)· A 当技术护城河支撑 · B 当 C 下的一个具体能力**。所有对外表述(README / dev.to / Show HN / pitch)统一围绕 C。一句话旗帜:
> **nautilus-compass — 让多个 agent 在没有编排器的情况下可靠协作**(跨 dialog 契约 + 漂移检测 + 4-tier 记忆生命周期)。

---

## 1. 现状(我们在哪)

### 对外 / GTM(Path B Week 1)
- **本地件全 done**:LICENSE(MIT)✅ · README(black-box positioning)✅ · CLI v0(`nautilus-compass` 命令)✅ · dev.to 文章 ✅**已发表** · Show HN 物料 ready
- **PyPI 2.0.2 已发布**(含 CLI fix · `pip install -U nautilus-compass` 可用 · 之前 2.0.1 主命令 crash)
- **未做**:Show HN 提交 · GitHub issue cross-project thread · 还没有 1 个外部 OSS team / SaaS pilot 回应(Path B 真 metric)

### 产品 / 技术
- v3 全方位提升:Phase 1 全 + 2.H/2.I done(drift loop closing 三角实证 + tier promotion + contract scanner)
- drift loop:从"只检测不干预"(5/27 finding)→ 闭环三片到位(检测 + 用户 CLI ack + agent 自 ack)· **act_on_rate 7d 9.87% / 24h 40.79%**(目标 ≥70% · 还差 7×)
- F.2 Soul subscriber poller:**blocked**,等 cloud DB credential(已 issue contract `cnt_compass_soul_sub_a2`)

### 研究 / 价值证明(诚实结论)
- benchmark:LongMemEval-S 56.6% · EverMemBench 44.4%(都有已知天花板)
- **关键诚实结论**(受控对比 Pilot 0):在单事实检索上,compass 对朴素 RAG **无可测增量**(A2≈A3)。
- → 推论:**compass 的价值不在 benchmark recall,而在差异化能力**(drift 检测 / cross-agent / PoI / 4-tier 生命周期 / recency)。这直接支持把对外定位往 "reliability / 行为" 而非 "记得更准" 方向收。

### 生态 / cross-dialog
- 4 个 Claude Code dialog(compass / Soul / V5 / nautilus-core)文件系统协议协作 · contract scanner 跨 dialog
- Soul daemon 自治跑(~12 cycle/天)· 5/30 首次 daemon-shipped PR 触发 NAU 结算 50 NAU(北星 agent 自治闭环第 1 步真 fire)
- 2 个 outstanding contract:`cnt_compass_soul_sub_a2`(要 DB credential)· `cnt_compass_v5_outcome_b2`(等 V5)

---

## 2. 目标(我们要去哪)

### 北星(不变)
**agent first · agent 自治生态**(anchor #1)。真客户是未来 super-agent 不是人。compass 的终极形态 = 多 agent 共享的"自知 + 预测 + 经济"记忆 substrate(L4 cross-agent)。

### 当前 wedge(2026-05-27 pivot · 5/30 correction)
**Path B:OSS multi-agent reliability eval**。
- 不是"客户获取 defer",是 **buyer wedge swap**:Path A(算法备案 audit ¥30k/件)已 drop(5/5 critical miss),换成 OSS 多 agent 可靠性赛道(4/4 critical met)。
- 打法:用 compass 自己 dogfooding(4-dialog field log)当产品 demo,而非刷 benchmark。

### 成功标准(Path B · 不是 ship 件数)
- Week 1 后 4-7 天:**1 个 OSS team verified integration + 1 个 SaaS pilot inquiry**
- 这才是 0→1。dev.to/Show HN/CLI 都是手段,不是目的(anchor #3 反 D)。

---

## 3. 未闭环清单 / 接下来的工作(2026-06-01 更新 · 按 owner 分类)

> 🔴 **最该看见:Path B 真 metric = 0**。本轮 ship 多(CLI/PyPI/dev.to/README/desc/定位 C)都只是"准备好让外部能验证",成功标志(1 OSS team verified integration + 1 SaaS pilot inquiry)还没开始。anchor #3:ship 件数 ≠ 价值,外部回应才是 0→1。

### A · 待用户动作(outward · agent 不能代做)
- **Show HN 提交**(dev.to 已 live 且 crisp · 隔 4-6h · 8am-12pm PT · 物料 `paper/promo/show_hn_*.md` ready · title #2)— 触发外部回应的扳机
- GitHub issue cross-project thread(HN 上首页才发 · conditional)

### B · blocked(等外部 unblock · cross-dialog)
- **F.2 Soul subscriber poller**:等 `cnt_compass_soul_sub_a2` credential(6/7 · platform secure channel)+ 本地 daemon 连 cloud DB 需 ssh tunnel · **unblock 后最高杠杆**(poll `engine_cycle_outcomes` → 喂递归闭环 + L4 PoI + surface soul outcomes 给用户)
- `cnt_compass_v5_outcome_b2`:等 V5 dialog ack(6/5)
- L4 cross-agent substrate(soul outcomes surface + PoI):依赖 F.2 unblock

### C · 可独立推进(无 blocker · fresh session 能直接做)
- **drift act_on_rate 9.87% → 70%**:闭环已通,缺减少误报(cry-wolf · 从 specificity 入手不是加 alert)· 递归自我提升核心 KPI(本会话多次 drift 误报正说明此痛点真实)
- **受控研究**证差异化能力(drift/cross-agent)真实价值 · 不刷 benchmark(诚实结论:单事实检索 A2≈A3 无增量)

### D · 技术债 findings(低优先 · 不阻塞)
- `nautilus-compass` umbrella 没 wire `feedback` 子命令(现用 `feedback log <id> fp`)
- `release.yml` 只匹配 `v1.*`,v2 tag 只发 PyPI 不建 GitHub release
- **scanner cross-dir bug**:daemon recall plugin 误显 `cnt_compass_soul_sub_a1` outstanding(repo 端 `contract.py` scan 已对 · daemon 是老 plugin lineage)· 修它减 cry-wolf → 直接服务 drift act_on

### ✅ 已闭环(本轮 · 不再是 TODO)
- 对外表述 reframe 统一 #1=C(README 首屏+30s-pitch / dev.to live PUT / GitHub repo desc)
- CLI v0 修复 + PyPI 2.0.2 live(`nautilus-compass` 命令之前 crash)
- #1 定位 C 拍板 + 固化(memory + 本文档)

### 非 compass scope(不漏 · 不 owner)
- `cnt_family_taxonomy_ack_2026_05_18`(V5→nautilus-core · 等 nautilus-core confirm · 非 compass action)

### fresh session 第一件事(判断树)
1. Show HN 已发且有回应 → 跟进 inquiry(Path B 真 metric · 压倒一切)
2. credential 到 → F.2(unblock 后最高杠杆)
3. 都没 → **C 类直接做**(drift act_on specificity / 受控研究)· 其中修 scanner cross-dir + drift specificity 服务递归闭环(anchor #2)

---

## 4. 关键风险 / 张力(诚实)

- **滑回 self-loop**:产品闭环若不指向最终可交付物,会滑回历史 94% self-loop(anchor #2 唯一要盯的点)。Path B 的外部 metric(OSS team / pilot)就是防线。
- **ship 件数 ≠ 价值**(anchor #3 最高复发):本 session ship 了 CLI + PyPI + dev.to,都是手段;真价值要等外部回应。不要把"发了 N 件"当进展。
- **drift cry-wolf**:act_on 9.87% 的根因可能是误报多致 agent tune out(参 `session_20260527_drift_loop_open_tuneout`)· 提升要从 specificity 入手不是加更多 alert。
- **定位不收敛**:见 §5,这是当前最该解决的战略问题。

---

## 5. 已拍板(2026-05-31):#1 = C · 多 agent 可靠性底座

dev.to"不够提炼"的 root 不是文笔,是没选一个主张当锚。**2026-05-31 用户定:#1 = C(multi-agent reliability infra)· A(black-box memory)当技术护城河支撑 · B(drift detection)当 C 下面的一个具体能力**。

理由:最贴当前 wedge(Path B OSS multi-agent reliability)+ 北星(agent 自治);dev.to field log 已是这个角度。已知弱点:N=1 operator 证据强度,需外部 team verified integration 补强(正是 Path B Week 1 metric)。

落地动作(下一步对外表述统一围绕 C):
- README 首屏旗帜句改成 §0 那句(reliability layer · 无编排器协作)· black-box / drift 降为"支撑能力"小节
- dev.to 重发或新写一篇 crisp 版:开头 3 句讲清"无编排器的多 agent 可靠性",field log 当证据,black-box/drift 当机制细节(不和 reliability 主线抢戏)
- Show HN title 用 reliability 角度(物料 title #2 "caught its own verify-gap" 是 reliability 的具体 incident · 一致)
- 一句话 pitch / GitHub repo description 统一成旗帜句

---

## 关联
- [[anchor_user_strategic_compass]] · 7 stance(北星 + 红线)
- `nautilus-core` memory `feedback_anchor_2_wedge_swap_path_b_20260530` · Path B 真意
- [[session_20260531-0530_compass_p2p3p4_options1234_complete_handoff]] · 本 session P1-P4 + CLI + dev.to/PyPI 执行
- [[project_compass_layer2_controlled_study]] · 受控对比战略(价值证明走差异化非刷榜)
- [[session_20260527_drift_loop_open_tuneout]] · drift 闭环开环 + cry-wolf 根因
- `paper/promo/dev_to_4dialog_case_study_DRAFT.md` · `paper/promo/show_hn_*.md` · 对外物料
