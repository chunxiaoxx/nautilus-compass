# 🧭 跨对话框看板(pull 聚合 · 非副本同步)

> platform 拉取各框自己 repo 的 LOOP_STATE + git log 生成 · 各框 session-start 读这份 · 弃 push 副本(已证失效)
> 生成方式:`python tools/cross_dialog_board.py --days 7` · 各框只维护自己 LOOP_STATE

## 各框状态(grounded · 各自 repo)

| 框 | 近 7d commit | 最近 commit | 当前闭环目标(自己 LOOP_STATE) |
|---|---|---|---|
| **platform-soul** | 36 | 07-20 22:08 chore: redact exposed qixuw API key in core run  | (无 LOOP_STATE 或未找到目标行) |
| **agent(V5)** | 40 | 07-20 22:08 chore: redact stale anthropic key in env backup | (无 LOOP_STATE 或未找到目标行) |
| **compass** | 29 | 07-20 22:07 chore: harden Compass eval entrypoint python res | (无 LOOP_STATE 或未找到目标行) |
| **FDE** | 21 | 07-15 12:09 audit: 完整调研审查报告 + 建议 给 platform_soul (24h ack SL | (无 LOOP_STATE 或未找到目标行) |

## 域/算子分工(grounded 算子不撞 · turf)

- **platform-soul**:OR 域(JobShop/TSP/BinPack)+ 平台 infra + verdict 持久化 + dispatch
- **agent(V5)**:GenOpt 出题主体(#2-#10 模板)+ 外环飞轮 + RSI producer
- **compass**:KernelEng(matmul/conv2d/rmsnorm)+ ComputerSys + env/verify + feishu 读写
- **FDE**:生产管理底座(飞书多维表格 base + 5 角色 + 招募)

## 各框近期 commit(近 7d · 各自 repo)

### platform-soul
- bb3e4bc03 chore: redact exposed qixuw API key in core run scripts and plan doc
- 2bc39faaf sync: receive V5 codex cross-dialog event
- f52ac99f2 LOOP_STATE: 7/18 燃料链首闭——薛美雪题成首道完整A类燃料(0/5难倒+3/3强解+验证器);燃料标准实证=概念边界密度
- 31d4c64f9 feat(fde): 🔥第一道完整A类蒸馏燃料入池(薛美雪题:弱难倒0/5+强解3/3带CoT+确定性验证器)——垂域批次燃料链首闭
- a52957e77 feat(fde): 🔥薛美雪题难倒成立(doubao 0/5·失败聚焦预扣义务时点边界)——第一道A类燃料候选;GLM-5.2强解测试中
- 8aa490d68 feat(fde): 薛美雪题验证器(劳务报酬按月合并/跳档/跨期/缺凭证三集真值)+doubao测试harness;pass@5后台运行中
- 07a299a91 feat(fde): 全批PII扫描器+结果(82文件·身份证2292/手机2607/卡168)——附件整体不可交付,机械脱敏器排入队列
- b0682da03 docs(fde): 难倒测试终判——张欢题10/10未难倒非燃料;沉淀三条方法论(任务模式分布外性≠数据私域/不喂熟口径/PII全批扫描);燃料主力候选改判多附件稽核类

### agent(V5)
- 48d62c6 chore: redact stale anthropic key in env backup
- cb83957 sync: emit V5 codex cross-dialog event
- 453af40 docs(reborn): hand off R3 observation to Codex
- b0d7d37 chore(ssot): align charter with core canonical
- 73e18e6 chore(ssot): LOOP_STATE ← core 7/18(燃料链首闭)
- 37cec92 docs: 垂域题QC盲点测试+交付triage(7/18用户提交燃料) — 现成harness对3维零覆盖·doubao实测70%可补·落买方交付非income
- 39b500d chore(ssot): LOOP_STATE 副本 ← core canonical 7/18(11题作废→垂域批次接棒·7/18探针真值)
- 6289a28 reborn R3: 写模式生产入口 production.py(TDD·6测试)— 只读影子→受限真写(write_note仅notes/·碰不到代码·self_modify留R4)+ remember补长期记忆;income由timer独立产不碰经济;熵1299/3k

### compass
- 1f2c082 chore: harden Compass eval entrypoint python resolver for 3.10+
- 5fd000a chore: redact exposed API keys in PR49 review artifacts
- bfe2060 compass: surface cross-dialog event freshness
- 9c7066d sync: receive V5 codex cross-dialog event
- 83b0573 chore(ssot): align charter with core canonical
- dff582d chore(ssot): LOOP_STATE ← core 7/18
- 5b1520b fix(lifecycle): 把 reinforce_on_recall_hit 接进 MCP 召回服务路径(access 闭环真断点)
- 8cd482a chore(ssot): LOOP_STATE 副本 ← core canonical 7/18

### FDE
- bcf2cfb audit: 完整调研审查报告 + 建议 给 platform_soul (24h ack SLA)
- f3c9460 audit: 15-repo loop complete, 9 CRIT/47 HIGH/68 MED/58 LOW, 6 pending decisions
- 3bbf616 audit: progress JSONL
- 6314494 audit: ROI roadmap
- c3b9d4d audit: cross-repo INDEX
- a2ae7e9 audit: soul-file-spec _MINI_AUDIT.md
- d85bd1b audit: smrti _AUDIT.md
- 04b65ef audit: project-nautilus _AUDIT.md
