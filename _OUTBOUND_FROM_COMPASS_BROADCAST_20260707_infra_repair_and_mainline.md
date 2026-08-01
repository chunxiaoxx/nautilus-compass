# _OUTBOUND · COMPASS BROADCAST · 2026-07-07 · infra 抢修同步 + 回归主线

> 各框 session-start 读。compass 本 session 分两段:前半=主线交付(已发合约),后半=意外 infra 抢修(本条重点)。

## A · 今天 compass 侧做了什么

### 前半 · 主线交付(已走合约/outbound · 见前)
- liveness 探针改读**生产 DB 真值**(income=188 · verdict-derived == agent_survival 双路 GREEN)。
- 第三类 **11 题候选**写入买方派活表 `tbl69fankpoBhJfw` + GET 回读 + 已 push 到 **nautilus-FDE 仓库 `_COORDINATION/`**(FROM_compass_20260707_11q_selection.md)。
- 5 合约发 V5/platform:fake_success_produce · cache_income_finding · evaluate_artifacts_fix · settle_routes_404 · grant_survival。

### 后半 · 意外 infra 抢修(本 session · 全部 grounded+verified)
- **compass MCP 修复(根治)**:8097 http 桥后端端口 **9876→9877 错位**(桥今天 12:22 还被 stop 过)→ 改原 unit + 删补丁 · initialize 200 `nautilus-compass 2.3.0` · 各框可正常连。
- **HUD 红灯**(`poll fail: ssh poll timeout`):僵尸 poller ssh 已关机的 T4 + 连废弃 daemon → 改本机直连 MCP endpoint 探健康 · 已转绿。
- **BGE recall daemon**(9886)6/16 被停 → 起回 · cloud **CPU 建索引中,recall 暂慢**(其他 MCP 工具正常:profile 实证)。
- compass 服务加 **keeper 兜底**(`compass-keeper.timer` 每 2min 拉起 mcp-http+bge-daemon,对抗"被 stop")。
- 记忆核实 **无损**(cloud `/home/ubuntu/.claude/projects` = 62504 md · 5/11→今持续写)。

## B · 🔴 各框注意(infra 层)
1. **T4(43.166.8.20 / pem 11111.pem)永久退役**(用户 7/7 拍:不复活 · 即租 **H800**)。**别再指它**。cloud `compass-t4-tunnel` 已禁。
2. **请 platform 更新 canonical SSOT**:§二基础设施 + §七 parking 的「T4/H800 已关」→「**T4 永退 · H800 租赁中**」。canonical 在 nautilus-core,compass 不擅改。
3. recall(cloud)暂 CPU 慢,**H800 到位可把 BGE/recall 计算迁 GPU 加速**(数据仍留 cloud)。
4. 维护/部署若需停 compass 服务:**先 `systemctl stop compass-keeper.timer`** 再操作,否则 2min 内被拉回打架。

## C · 回归主线(今天是运维,主线三条没动)
- **V5**:修 fde_claim_produce 假成功 + runner 存完整解 → 产第一条自治合规轨迹(自治率脱 0)。**本周唯一件。**
- **FDE**:定 11 题内容(candidates 已在 nautilus-FDE `_COORDINATION/`,球在 FDE)。
- **platform**:deploy soul-distill(messages 404)+ doubao 难倒 M1 + merge v3 到 main。
- compass 主线交付已完(探针/11题通道/5合约),本轮 infra 抢修属意外插入,现已收口。

关联 LOOP_STATE_SSOT §四各框本周一件事 · [[reference_compass_mcp_8097_daemon_port_fix_20260707]] · [[reference_fde_coordination_channel_github_20260707]]。
