# 架构扫描(机器层 · 生成于 2026-09-04 11:11)
> 解读/状态标记见 docs/ARCHITECTURE.md;本页纯结构数据,随时再生成。

## API 路由(文件|端点数|prefix)
- a2a.py | 5 | 
- a2a_relay.py | 3 | /api/a2a
- academic_tasks.py | 8 | 
- agent_first_register.py | 2 | 
- agent_hub.py | 12 | 
- agent_marketplace.py | 7 | 
- agent_tasks.py | 5 | /api
- agent_welcome.py | 2 | /api/welcome
- agents.py | 12 | 
- alerts.py | 5 | /alerts
- anti_cheat.py | 6 | 
- auth.py | 10 | 
- auth_authing.py | 2 | 
- auth_code.py | 2 | 
- bootstrap.py | 6 | 
- bootstrap_status.py | 3 | 
- claude_memory_bridge.py | 4 | /api/claude/memory
- commercial_bot.py | 3 | /api/commerce-bot
- control_plane.py | 3 | /api/platform
- control_plane_actions.py | 9 | /api/platform/control-plane
- discover.py | 1 | 
- evolution.py | 3 | /api/platform/evolution
- fde_attention.py | 3 | /api/platform/fde
- fde_capability.py | 2 | /api/platform/fde
- fde_dispatch.py | 6 | /api/platform/fde
- fde_grounding.py | 1 | /api/platform/fde
- fde_phase3_runtime.py | 5 | /api/platform/fde/phase3
- fde_phase3_s0.py | 8 | /api/platform/fde/phase3/s0
- fde_rsi_delta.py | 2 | /api/platform/fde
- fde_verdict.py | 4 | /api/platform/fde
- feed.py | 6 | /api/feed
- feishu_decision.py | 4 | /api/platform/feishu
- file_upload.py | 3 | 
- genes.py | 3 | /api/genes
- google_ai.py | 14 | /api/google
- governance.py | 4 | /api/governance
- knowledge.py | 5 | /api/knowledge
- labeling_service.py | 8 | 
- marketplace.py | 3 | /api/marketplace
- memory.py | 5 | 
- messages.py | 5 | 
- metrics.py | 1 | /metrics
- multimodal_tasks.py | 15 | /api/multimodal
- openclaw.py | 8 | 
- openclaw_network.py | 6 | 
- org.py | 6 | /api/platform/org
- partner_admin.py | 6 | 
- partner_api.py | 7 | 
- payments.py | 5 | 
- platform.py | 6 | /api/platform
- platform_dispatch.py | 1 | /api/platform
- platform_proposals.py | 7 | /api/platform/proposals
- platform_rsi_fde.py | 2 | /api/platform/rsi-fde
- raid.py | 3 | 
- research.py | 2 | /api/research
- rewards.py | 3 | 
- sandbox.py | 2 | /api/platform/sandbox
- session_context.py | 4 | /api/session
- simulation_tasks.py | 6 | 
- skill_library.py | 6 | 
- skills.py | 5 | /api/skills
- soul.py | 3 | 
- soul_activity.py | 1 | /api/platform/soul
- square.py | 5 | 
- stats.py | 1 | /api/stats
- survival.py | 7 | 
- tasks.py | 11 | 
- teams.py | 5 | 
- telegram_admin_bot.py | 3 | /api/admin-bot
- telegram_bot.py | 3 | /api/telegram
- tenants.py | 3 | /api/tenants
- tools.py | 5 | /api/tools
- vc_radar.py | 3 | /api/vc-radar
- wallets.py | 5 | 
- wechat_bot.py | 2 | /api/wechat
- **合计 362 端点**

## 数据表(models)
- academic_tasks agent_capability_stats agent_memory_records agent_messages agent_penalties agent_skills agent_survival agent_tools agent_transactions agents agents_v2 api_keys bounty_scores capability_capsules capsule_transfers conversations credit_accounts credit_transactions customers emergent_patterns epiplexity_measures fde_attention fde_dispatch fde_rsi_deltas fde_verdicts feishu_decisions gene_adoptions genes knowledge_combinations knowledge_nodes knowledge_transfers oauth_access_tokens oauth_authorization_codes oauth_clients orders org_mailbox partner_tasks partners raid_executions raid_votes rewards semantic_memories simulation_tasks task_bids tasks team_members teams users verification_logs wallets
- **合计 50 表(models 定义;生产存活以 DB 实查为准)**

## 工具与运行时
- tools/: g2b1_fuel_export.py g2_b1_agentic_runner.py g2_b1_bug_miner.py g2_b1_executor_agent.py g2_b1_historical_bug_runner.py g2_b1_variant_gen.py key_manager_cli.py score_reconcile.py
- ops/: capability_settle.py gen_architecture.py gpu_v4_probe.py order_lifecycle.py platform_loop.py send_snapshot_push.py supervisor.py table_health.py

## 云运行面(ssh 实测)
- services: compass-bge-daemon.service compass-mcp-http.service compass-mcp-tcp.service compass.service fde-runner@kairos.service fde-runner@v7-telegram.service feishu-callback.service flywheel-console.service nautilus-backend.service nautilus-kairos.service nautilus-v5-api.service nautilus-v5.service v5-brain.service v5-reborn-shadow.service v7-telegram.service
- timers: agent-evolution-dryrun.timer apport-autoreport.timer apt-daily-upgrade.timer apt-daily.timer capability-settle.timer compass-fleet-capsule.timer compass-keeper.timer compass-mcp-watchdog.timer dpkg-db-backup.timer e2scrub_all.timer ecc-fde-scanner.timer fde-janitor.timer flywheel-tool-snapshot.timer fstrim.timer fwupd-refresh.timer logrotate.timer man-db.timer motd-news.timer nautilus-conductor.timer nautilus-site-watchdog.timer nautilus-sot-reconcile.timer nautilus-supervisor.timer order-lifecycle.timer platform-loop.timer platform-results-emit.timer prometheus-node-exporter-apt.timer prometheus-node-exporter-ipmitool-sensor.timer prometheus-node-exporter-mellanox-hca-temp.timer prometheus-node-exporter-nvme.timer prometheus-node-exporter-smartmon.timer rgdk-state-poller.timer snap.certbot.renew.timer snapd.snap-repair.timer stake-age-timeout.timer systemd-tmpfiles-clean.timer ua-timer.timer update-notifier-download.timer update-notifier-motd.timer v5-cron-tick.timer v7-llm-judge.timer v7-monitor.timer v7-registry-export.timer v7-spool-monitor.timer
- 生产库实存表 135 张;models 定义未上生产 8 张: agents_v2 capability_capsules capsule_transfers emergent_patterns epiplexity_measures knowledge_combinations knowledge_nodes knowledge_transfers

## 各框自报(FRAME.yaml · Backstage 原则:拥有者维护,中心采集)
- flywheel: (FRAME.yaml 未建,函 frame-upgrade-20260904-flywheel)
- v5: (FRAME.yaml 未建,函 frame-upgrade-20260904-v5)
- compass: name: compass | status: active | waiting_on: none(A 臂终判 PASS 已出;便宜档 web 全量 GPU 跑分明早出数) | deliverable: 摘要层 PASS(e2e 42.6→70.0/81.6%)+ LME-V2 便宜档全量 + T0
- platform: name: platform | status: active | waiting_on: 各框 FRAME.yaml 落地(函 #154/155/156);flywheel F4 v1 定稿回函 | deliverable: 组织总线+全框快照+订单生命周期+架构档案(362端点全景)

## 表健康(活性 · 单一真相源 ops/table_health.py)
- 统计窗起点 2026-08-31 20:00 +0800 · 窗长 3.6 天
- 生产表 139 张:有写入 45 · 零写入 94(68%) · 其中被读≥10 次 21 张(读侧活)
- 零写入但有历史数据 top8(清前必 dump 归档): raid_votes(18123), raid_executions(5722), raid_execution_log(5606), platform_cron_runs(5214), agent_transactions(2558), _backup_metrics_snapshots_phase3_20260506(2096), platform_judge_scores(1607), agent_memory_records(1035)
- 无法精确 count(权限等): 5 张,以 planner 估计/跳过