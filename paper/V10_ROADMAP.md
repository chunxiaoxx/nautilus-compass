# compass v1.0 · 12 个月推进路线 (loop-tracked)

> 状态: in-progress · loop 持续推动直到全部完成
> 启动: 2026-05-05 · 目标 GA: 2027-05-05
> 生效约束: 协议优先 (MCP/A2A) · 用户为一等公民 · E2EE Pro+ · 不变现走融资

## 进度概览

| Phase | 周期 | 状态 | 关键 deliverable |
|---|---|---|---|
| **v0.8** (writer + drift) | 2026-05 | ✅ 完成 | session_writer · drift-aware obs · drift_history · session_search · MCP v0.9 7 tools · A2A adapter 雏形 |
| **v0.8.1** (LongMemEval) | 2026-05 | ✅ done | **full 500 acc 56.6%** 🏆 · ssa 83.9% · ssu 57.1% (+27 vs baseline) |
| **v0.9.0** (MCP/A2A 实测) | 2026-06 | ⬜ planned | npm @nautilus/compass-mcp · A2A 注册 · 多 agent fork (OpenClaw / Hermes / Cursor) |
| **v0.9.1** (auth + sqlite) | 2026-07 | ⬜ planned | 邮箱注册 · JWT · sqlite migration · multi-user |
| **v0.9.2** (region 第一刀) | 2026-08 | ⬜ planned | cn-shanghai 上线 · 国内 user 数据本地化 |
| **v0.9.3** (Cursor extension) | 2026-09 | ⬜ planned | VS Code marketplace 上架 |
| **v0.9.4** (Pro 灰锁) | 2026-10 | ⬜ planned | 订阅页面 · ¥38/mo placeholder · 不收钱 |
| **v0.9.5** (eu region) | 2026-11 | ⬜ planned | eu-frankfurt 集群 · GDPR 合规审计 |
| **v0.9.6** (融资节点) | 2026-12 | ⬜ planned | Seed/Pre-A pitch deck · 数据可看 |
| **v1.0-rc** (E2EE 默认) | 2027-01 | ⬜ planned | libsodium 客户端 · key derive · 自托管 docker |
| **v1.0** (Team plan) | 2027-02 | ⬜ planned | 共享 memory (Caishen 部门) · org schema |
| **v1.0.1** (画像融合) | 2027-03 | ⬜ planned | client-side aggregate · profile 浮现 |
| **v1.0.2** (开源) | 2027-04 | ⬜ planned | Apache 2.0 · GitHub release · 开发者文档 |
| **v1.0 GA** (论文) | 2027-05 | ⬜ planned | LongMemEval 论文投递 · 学术权威 |

## 当前 loop 推进项 (本会话)

```
✅ session_writer.py             writer 接入 (DeepSeek ¥0.05/session)
✅ drift-aware obs schema        frontmatter 加 drift / drift_signals
✅ Stop hook 链路升级            session_writer → llm_distill → strategy_store
✅ drift_history.py              ASCII timeline · compass 独占
✅ session_search.py             跨 project keyword + drift filter
✅ sdk/compass_client.py         multi-agent ingest SDK (offline buffer)
✅ sdk/README.md                 接入文档
✅ examples/openclaw_*.py        SDK demo (开源 agent fork 路径)
✅ examples/hermes_*.py          SDK demo
✅ paper/V09_USER_SCHEMA.md      user-as-first-class 架构
✅ paper/V10_ROADMAP.md          本文 (12 个月 loop)
✅ mcp_server.py v0.9.0-dev      7 tools (4 新)
✅ sdk/a2a_adapter.py            A2A protocol 雏形 + HTTP service
✅ 删除 claude-mem 残留          234 MB 清掉

🟡 v0.8 LongMemEval full 500     跑中 · ETA 30 min · 终态 ~55-56%
🟡 sdk/mcp_adapter.md            spec ready · 实施在 v0.9
🟡 PIPL/GDPR 合规初步            region sharding 设计 OK · 实施 v0.9.2
```

## 平台融合 (PLATFORM_FUSION.md · 8 个融合点 · 2026-05-05 加入)

| Fusion | Phase | 说明 |
|---|---|---|
| #1 身份层 (单点登录) | v0.9.1 | Nautilus JWT 共享 · 移除 compass 独立 signup |
| #2 OAuth2 PKCE | v0.9.2 | 3rd-party agent (Cursor/OpenClaw fork) 走 nautilus.social |
| #3 Agent runtime 注入 | v0.9.3 | nautilus-agent SDK 默认 attach_memory |
| #6 Anchor 继承 | v0.9.4 | platform_anchors layered (base + domain + tenant) |
| #4 Stake × Drift 耦合 | v0.9.5 | red drift→stake_penalty · green→bonus |
| #8 V5 兼容 | v0.9.6 | ~/v5-memory migration tool |
| #7 RAID-2 写审分离 | v1.0 | reviewer agent 把关 obs 写入 |
| #5 Marketplace 信任层 | v1.0.1 | drift_history + profile_compatibility 暴露给市场 |

## 立即可做 (本 loop 持续推)

1. ✅ MCP server v0.9 重构 (7 tools) — done
2. ✅ A2A adapter 雏形 — done
3. ✅ A2A adapter 自测跑通 (selftest) — 2026-05-07 · 3/3 pass · DISCOVER + STORE_OBS + QUERY_DRIFT_HISTORY
4. ✅ 把本 session 自动写一条 obs 看 drift 字段 — selftest 自动验证
5. ✅ v0.8 final 出来 → 更新 paper/results/experiments_*.csv — 56.6% locked
6. ✅ npm/uv publish 准备 (package.json · setup.py) — nautilus-compass-mcp@0.9.5 shipped
7. ⬜ landing page 加 "v0.9 路线" section
8. ⬜ 注册 a2a-registry.nautilus.social (假设这个域名将在 Nautilus 平台启用)

## 必须做的硬条件 (任何 phase 都不能跳)

- [ ] 每个 v0.x.y release 必须 LongMemEval 跑分不下降 (regression gate)
- [ ] 每个新 endpoint 必须 selftest pass + 数据 round-trip 可验证
- [ ] 每个 phase 收尾写 RESULTS_v0xy.md · 含数据 + 决策 + 教训
- [ ] 不在产品里加 LLM-call 时 · drift detection 必须只用本地 bge-m3 (零边际)
- [ ] 任何用户数据落地必须可被 user delete (right-to-be-forgotten)

## loop 触发器

```
现在 (2026-05-05): 自我 pace · ScheduleWakeup ~25min 等 v0.8 final
v0.8 final 后:    更新 README + experiments csv + paper 数据 + push notif
然后:              短延迟接力 · 下一个未完成项
循环直到:          v1.0 GA (2027-05)

session 容量挂前: 写一条 v10_ROADMAP_progress.md · cron 续接
```

## 商业 / 战略 提醒 (不变现期约束)

```
M1-M5  · 0 钱 · 全用户免费 · 用 OpenClaw / Hermes / Cursor 兼容性吸开发者
M6     · 融资 (Seed) · 估值看跨 agent 用户基数 + LongMemEval 数据
M7-M11 · 用融资钱开 cloud · region · 团队
M12+   · Pro/Team 上线但不强制 · 让用户自然涨

不要做的事:
  · 不在 0.x 阶段卖功能
  · 不偷偷训通用模型 (违 E2EE 承诺)
  · 不卷 claude-mem 的 narrative 赛道
  · 不接外部 LLM provider 私货 (我们后端只跑本地 bge-m3)
```

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| Anthropic 自己出 cross-agent memory | 中 | 高 | 协议优先 + 跨平台 (我们不绑 Claude) |
| OpenAI Agent SDK 不开放 cross-call | 中 | 中 | 用 browser extension / proxy |
| MCP 协议大改 | 低 | 高 | 抽象化 transport · 标准 + 私有双轨 |
| A2A 不标准化 | 中 | 中 | 同时支持 MCP · A2A 不强 push |
| 国内监管 PIPL 收紧 | 中 | 高 | 本地化 + 自托管 + 区域 sharding |
| GDPR 处罚 | 低 | 高 | E2EE 默认 · right-to-delete · 数据不出境 |
| 融资失败 | 中 | 致命 | 小步迭代 · M3 demo 之后再决定 |
| 个人精力不足 | 高 | 致命 | loop 自动化 · 协议替代写代码 · OSS 社区 |
