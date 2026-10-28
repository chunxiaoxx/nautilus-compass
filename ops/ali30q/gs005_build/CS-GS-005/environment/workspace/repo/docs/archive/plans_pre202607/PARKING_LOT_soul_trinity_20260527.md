# PARKING LOT · Soul Trinity Product (2026-05-27)

> 工作流纪律:执行**第一增量**(Soul→审计→证书 一个 cycle · 见 `2026-05-27-soul-trinity-product-vision-design.md`)期间,
> 任何新想法**进这里**,不准拉进当前 goal。第一增量 DONE 之后,从这里挑下一个 goal。
> 目的:打破"一直扩展/分歧、永不闭环"的复发模式(见 memory `feedback_workflow_lock_goal_until_done_20260527`)。

## ✅ #4 DONE (2026-05-27 · binding DONE 达成 · 见 memory session_20260527_soul_api_increment4_binding_done)

**#4 · 把 /api/soul 产品化对平台 agent 提供(含 self-audit + cert)** — **完成**
- binding DONE 达成:真 agent `agent_id=59` 调 live :8000 `POST /api/soul/audit-generate` → `cert_valid=True` · 真 `fidelity_score=0.308` · 独立 verify-valid + tamper→invalid。
- 落地:agent-facing 端点(generate→self_audit→签名 cert · **无 PR/无 PAT**)+ `generate(capture_content)` 取真代码 + Option C reconciliation 切片(soul+cert canonical 进 origin 分支 `soul-api-increment4` tip `8cad58beb` · 19 tests green)+ deploy 到 mvp(含补 engine · mvp 部署留痕 `36a6953e4`)。
- code-review 抓到并修了 1 个 HIGH(path-traversal readback)+ 2 MEDIUM(bounty_id 碰撞 / 错误处理)+ 1 fail-closed。
- ⏳ 尾巴:origin 分支是否 merge → master(canonical 完成 · 待用户决)· 见下方 parked。

## 仍 parked 的候选 goal(#4 DONE 后 · 按依赖排 · 不预先承诺)

1. **Compass PoI 接入证书** — cert 加 compass PoI cite-trail(compass `ingest` + PoI 已 ship · 接线)。三位一体补齐第三块。
2. **对外 A · codegen API 产品化** — `/api/soul/generate` 从内部 → 外部可调(外部鉴权 + 返回 产出+证书)。
3. **Soul 自驱第二增量** — 把后续 goal 喂 Soul goals.yaml,让 Soul grind(dogfood · 需第一增量闸验过)。
4. **cron-wiring** — ✅ **DONE 2026-05-27**(origin/master `34d1c35dc`)。goal_selector + pr_gate + daemon + systemd + bootstrap(autonomous-soul-plan Task 4-10)· 22 soul + 196 engine tests green · 见 memory `session_20260527_soul_cron_wiring_shipped`。⏳ **仍 human-gated 未做**:Task 11 Step 4 cloud dry-run proof(需 cloud ssh + DeepSeek key)+ Step 5 `systemctl enable --now nautilus-soul.timer`(= persona-drift 反复警告的 self-loop · 必须人审 dry-run 后 fresh-session 显式决断 · 不裸 ship)。merge 到 master ≠ 自主运行(daemon 静止在 repo 直到 cloud bootstrap + 激活 timer)。**dry-run proof 已成功** + **apply+draft-PR 增量已 ship**(2026-05-27 · master `a4091cc36` · daemon apply 隔离分支→draft PR→mark done surgical→no-op 防御→has_open_pr_for · 31 tests · PR #51 证明全链)。**机制 proven 但 timer 未激活** —— 卡在 **goal-sourcing 瓶颈**:docstring seed goals 脆弱(无 import 模块已有 docstring=no-op · 有 import 文件 staging import-check fail)· reflection/docs 持续来源 cloud 未激活(无 DATABASE_URL)。见 memory `session_20260527_soul_apply_pr_goal_sourcing_bottleneck`。**真正下一个 goal = goal-sourcing**(reflection 接 DB / check-pipeline staging import fix / 人工 curate 真实 backlog)· 这是 anchor #2 闭环的"提升空间来源"核心 · timer 激活前置。**→ 用户定方向(5/27 讨论 3 轮):soul review 自己代码 → council 发散收敛 → 完善 coding · MVP SHIPPED + cloud 验证**(master `2fe445d9e` · 6 tasks done · subagent-driven)· **真 self-improve PR #52**(soul 自主 review pause_check → `unlink(missing_ok=True)` 真改进 · pytest gate pass · draft)= anchor #2 递归闭环端到端证明 · 见 memory `session_20260527_soul_self_improve_council_mvp_shipped`。⏳ **timer 未激活**(human-gated · 用户看 PR #52 后决 · `ssh cloud "sudo systemctl enable --now nautilus-soul.timer"`)。
5. **Stage 2 递归 driver** — engine 递归改自己 + line-count/docstring 守门(防 truncate drift)。
6. **V5/Kairos 接到"审 Soul 产出"** — 轻 inbound 给 agent dialog(anchor #7 consent)。
7. **Soul + V7 组合(中国化 Claude Code)** — V7 用 Soul 当 self_modify 后端(需 V7 dialog consent + core/soul 改名 v7-psyche)。
8. **B · repo 级自改进服务** — 外部 repo 隔离/sandbox + 多租户(最大工程 · blast radius 大 · 最后)。
9. **audit-generate rate-limit / 配额** — 每次调用 = 1 次真 LLM gen + 3 DB insert · 任何 authed agent 可拉高成本(code-review MEDIUM · 硬化项)。
10. **merge `soul-api-increment4` → origin/master** — canonical 完成的最后一步(additive · 已 19 tests + review + E2E)· 待用户决 merge vs 留 PR。

## 更大的愿景碎片(不丢 · 但远期)

- 产品矩阵完整化(Soul+V7+平台 = 完整原生 AI 组织底座对外)
- "queryable organization" / one-shot dashboards(YC Diana Hu)
- NAU ↔ USDC 桥 · ISO 42001 / 算法备案 cert engagement(post-revenue)
- 客户线重启(anchor #2 paused · 用户判断 timing)

## 规则

- 往这里加东西 = 好事(说明想法被记下而不是塞进当前 goal)。
- 从这里取东西 = 只在当前 goal DONE 之后,一次取一个,重走 brainstorm→plan→execute。
