# Compass v0.9 真用户 Onboarding Playbook

> 给自家产品 (OpenClaw / Hermes / ZenMind / Caishen) 接入 compass.nautilus.social 用 · 5-10 分钟接入 · 跑 1 周 · 收 feedback

## 1. 接入对象优先级

控代码 = 风险低. 顺序: 先 1 个跑 3 天 · 没 issue 再加 2-3.

| 顺序 | 产品 | 难度 | 接入方式 |
|---|---|---|---|
| 1 | **OpenClaw** | ★ | `attach_memory(agent)` 2 行 |
| 2 | Hermes | ★★ | loop end hook · 3 行 ingest_obs |
| 3 | ZenMind | ★★★ | MCP server (Claude Code 配 compass-mcp) |
| 4 | Caishen | ★★ | web API 直调 `/v1/observations` |

**推荐第一个: OpenClaw** · 单 agent · 主循环清晰 · 我们最熟 · fail 也不影响业务.

## 2. 接入步骤

- **OpenClaw** (`~/.openclaw/agent.py`): `from compass_sdk import attach_memory; attach_memory(agent, user_id, token)` · 在 main loop 前
- **Hermes** (`~/Projects/hermes/loop.py`): loop 结束钩子加 `client.ingest_obs(text, tags)`
- **ZenMind**: 不直接接 · 在 Claude Code `~/.claude/mcp.json` 加 compass-mcp · agent 通过 MCP 调
- **Caishen**: HTTP POST `/v1/observations` (Bearer token) · 财务/HR Agent 完成任务后调

## 3. 第一天 checklist

- [ ] `curl -X POST https://compass.nautilus.social/v1/auth/signup` → 存好 user_id + token + encryption_salt
- [ ] 写 5 条真观察 (不是 hello world)
- [ ] 调 `/v1/recall?q=...` · 主观判 top-3 命中没
- [ ] `GET /v1/audit_log` · 确认事件追踪正常

## 4. 第一周 checklist

- [ ] Daily 跑 `compass-drift-history 30` 看 timeline
- [ ] 收 feedback (好: 召回准 · 跨 agent 真用 / 坏: 慢 · 不准 · 体验)
- [ ] Day 7 写 retro doc · 含 3 个 wow moment + 3 个改进点

## 5. 成功标准 (7 天)

- 累积 50+ obs
- ≥5 次 recall 主观 "有用"
- 0 次 service down (uptime)
- drift detection ≥1 次主动 trigger 真问题

## 6. 失败 / 退出标准

- 召回明显不如直接 LLM context
- 性能不可接受 (LLM API 慢 · sqlite 锁)
- 3 天 0 wow moment

## 7. Feedback 收集 form

Tally template · 字段: 产品 · 接入难度 1-5 · 召回准度 1-5 · 跨 agent 真用 (Y/N) · 性能感受 1-5 · 总分 1-5 · 自由评论.

## 8. Week 2 决策

retro doc 沉淀 · 选项: (a) 全产品扩展 (b) 修关键 issue 先 (c) 砍掉. 决策依据 = §5 标准命中率 · 给 paper §future work 留素材.
