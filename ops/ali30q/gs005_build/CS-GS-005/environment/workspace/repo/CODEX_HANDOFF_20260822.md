# Codex 平台工作交接锚（2026-08-22 · Claude Code 接手）

> 单页真相源：Codex 8/3–8/15 在 nautilus-core 的平台工作已验收并合并（merge commit `b0a10dae1`，分支 `codex/g2-a0-cny10-v2`，47 提交/+27.6k 行）。此后平台工作由 Claude Code CLI 接续。开工先读本文，不重翻 codex 历史。

## Claude Code 接续进展（2026-08-22/23 · 本节由 platform 框维护）

### G2-B1 产品化：常驻 repair-executor（对齐 §0-ARCH 与"三框闭环第一圈"）

- **代码三件已入主干**（`cb21cfa3c`/`bb088c56f`/`69503e62d`）：`tools/g2_b1_agentic_runner.py`（多轮反馈循环 · RED 前置 · token 累计帽 fail-closed）、`tools/g2_b1_bug_miner.py`（git history 矿机 · 150 候选 · `docs/evidence/g2b1_task_queue.jsonl`）、`tools/g2_b1_executor_agent.py`（注册客户端+队列消费+一次性 worktree+evidence 幂等）。7 离线测试过。
- **executor 已注册生产**：`nautilus-repair-executor-001` = agent_id **9000010**（cloud DB 直查验证，wallet 0x9abce6cf…，凭据 `~/.nautilus/g2b1_executor.json` repo 外 0600）。
- **生产修复两连**（用户授权部署）：`GET /api/agents/{id}` 对新 agent 500 的两层根因——① `AgentResponse` 任务统计必填 int（NULL→422→500，`d271d7715`）② `get_agent_cached` 按内部 PK 查而路由传公共 agent_id（`dbf5c43c4`）。部署后 health 200 / 记分牌逐字不变。
- **GLM 首跑**：第一次超时（GLM 深思 completion >900s 读超时，端点健康已独立复核）；completer 硬化 read 1800s+单次重试后重跑中。

### 部署 gotcha（新沉淀，DEPLOY_DISCIPLINE 待补）

- cloud git 凭据失效（gh token expired、~/.git-credentials 无 github 条目）→ 走 **laptop ssh 直推**：`git remote add cloudpush ssh://cloud/home/ubuntu/nautilus-mvp` + cloud 侧 `receive.denyCurrentBranch=updateInstead`（git 原生，无 scp）。
- cloud repo 根是 `~/nautilus-mvp`（不是 phase3 子目录）。
- `nautilus-backend.service` 的 ExecStartPre `sync-agent-engine.sh` 每次重启会把 7 个 `backend/agent_engine/*` 跟踪文件改 dirty → updateInstead 推送会被拒。处理：stash 留档再推（stash `agent-engine sync artifacts 20260823`）。
- cloud 旧分支 `soul-distill-deploy`（7/15 旧物）被残留 worktree `~/distill-deploy` 占用，勿 checkout；部署目标是 `soul-audit-increment1`（已 ff 到 dbf5c43c4+）。
- `soul-distill-deploy` 已推 origin（单点风险清除一项）；**income 7551 冻结后现为 7639（+88）来源待 compass 审计**。


## 8/23-24 平台主线推进（Claude Code · 会话末交接快照）

### G2-B1 燃料产线（本会话核心成果，全部独立验证）

- **能力画像**：干净 harness 下本仓 3/3 修对（30k/20k/37k tokens），跨仓首题未修对（v5 仓 68k，3 轮：diff 上下文失配 + JSON 格式漂移，非 harness confound）。
- **七层 harness 修复链**（8/22-23 共烧 ~700k tokens 学费，每层都是"红灯先证伪探针自身"实证）：apply 双重前缀→错误上报覆盖→CRLF→collected 0 假 RED→pre-check 路径→TDD 测试不存在（SWE-bench 化：buggy 提交+fix 测试检出+辅助文件检出）→ERROR 算 RED。
- **④a-⑤ 全落地**：executor 路径泛化（任意仓，backend root 按 tests/ 树推导）→ 跨仓跑通 → winning_diff 入 evidence（燃料采样前置）→ 常驻 loop 模式（`--loop-minutes`，跨日预算状态 `~/.nautilus/g2b1_daily_state.json` fail-closed）→ 轮转队列（四仓 87 题，每题带 repo_path，`docs/evidence/g2b1_queue_rotated.jsonl`）。
- **常驻在跑**：后台任务跑 rotated 队列，每轮 2 题/30 分钟/日帽 500k，日志 `docs/evidence/.g2b1_daemon.log`。重启命令模板在 git log 或本文件。
- **燃料已交付 V5**：`g2b1_fuel_export.py` 按 V5 三件套格式（task_uid+starter_inline+verifier_inline）导出四仓 86 题（`docs/evidence/g2b1_fuel_*.jsonl`，outbound `g2b1-fuel-export-live`）。**等 V5 回：verifier 改造方式 + 拒绝采样归属**（④c 阻塞点，勿重复造 `_distill_make_traces_v2`）。
- **生产侧**：`/api/agents/{id}` 500 两层根因修复部署（d271d7715/dbf5c43c4）；income 冻结漏点修复（auto-verify 拒 genopt-*，eb6d50cba 已部署 cloud，income 稳 7639）；verdict bus 只收真跑（跳过/重放免费）。
- **未收口**：④c 等口径；executor 移交 V5 用户暂缓（平台继续扩）；Windows 计划任务注册（目前靠会话后台任务，重启机器需手动再启）；FDE 专家线停摆待用户。

### compass 新版本（v2.3 云 MCP）加载使用 —— 下个会话必读

- **重启会话后 `.mcp.json` 的 `nautilus-compass-cloud` 自动挂载**（本会话启动早于注册，只能用 TCP 直驱 workaround：注入 authToken + agent_type 到 JSON-RPC params，云 9877）。
- 正常用法：工具名必须是 `nautilus-compass-cloud`（区别于本地 `nautilus-compass`）；`ingest_obs`/`recall` 走云；agent_type=claude-code-platform-dialog 由 env 自动注入，**不要手填**。
- 自检：回执落盘路径应在云端（ssh cloud 可查 `~/.claude/projects/fleet-capsules/memory/`）；本会话已写合规首条 `session_20260824-0044_dogfood-bridge-platform-框首条云端-.md`。
- 跨框协同改进方案已提（等 compass/用户拍）：dogfood-bridge 为心脏 + outbound 48h 回执硬规则 + 平台 DB 机器可读层。

## 已证实的结论

1. **Protocol V2 = 平台重建为中立可验证协作协议层**（ADR `docs/plans/2026-08-03-nautilus-platform-protocol-v2-adr.md`）。独立 `nautilus_platform` PG 库、Ed25519 身份、原子命令、签名回执、幂等、outbox。平台不碰业务（FDE/验收/结算划出）。
2. **M1 R1a 合成修复链已完整实现并测试**：计划准入（source-hash 绑定）→ G1-A 宪法门 → G1-B 原子执行器证据 + 临时密钥准入 → fail-closed 读回。这是"平台发单→执行→签名→记账→独立验证"闭环的平台半边。
3. **G2-A0（DeepSeek 模型门）判 KILLED**：日期版模型名 `deepseek-v4-flash-0731` 在官方端点不存在。2026-08-22 用 `/models` 实测：仅有 `deepseek-v4-flash` / `deepseek-v4-pro` / `deepseek-v4-flash-vision-exp`（浮动 ID）。8/15 探针的 `policy_violation` 终态（计费 CNY 0、无重试）即此原因。**门资产保留**（V1/V2 合同 + 三道成本门 + fail-closed 测试已随合并入主干）。
4. **全套测试独立复现通过**（2026-08-22 本机）：离线 462 passed；R1a 链/CLI/fail-closed 40 passed（需环境前提，见下）；migration 3 个需"空 version 表"库状态逐一验证通过。

## 测试运行前提（谁跑谁知道）

- 库 URL 硬格式：`postgresql+psycopg2://postgres:<pw>@127.0.0.1:5432/nautilus_platform_g1b_<14位数字>`（harness `test_m1_r1a_synthetic_repair_cli.py` 强制）
- R1a 链测试需三个环境变量指向 pin 死的 worktree：
  - `NAUTILUS_V5_AUTHORITY_ROOT` = `~/.config/superpowers/worktrees/nautilus-v5/m1-r1a-ephemeral-signer-v1`（HEAD `4c18c5a7`，须 clean）
  - `NAUTILUS_V5_EXECUTOR_ROOT` = `…/nautilus-v5/m1-r1a-review-required-v3`（HEAD `f3d94d32`，须 clean）
  - `NAUTILUS_COMPASS_AUTHORITY_ROOT` = `…/nautilus-compass/g1-m1-r1a-grounding-capsule-v1`（含 commit `37efc4fc`/`e87234bb`）
- 运行命令（evidence 文档口径）：`python -m pytest tests/platform_protocol -q --confcutdir=tests/platform_protocol`
- 无环境变量时 ~12 个集成测试 fail（非 skip）——这是设计如此，不是回归。

## 已废弃的假设

- "DeepSeek 控制台看到的日期版模型号可用于 API pin" —— 证伪。
- 旧 Core public schema / 历史 Alembic 图作为迁移权威 —— ADR 明确废弃。

## 悬挂清单（未收口）

| 项 | 状态 | 动作 |
|---|---|---|
| `soul-distill-deploy` 未推送远程 | 单点风险 | 待用户决定 push |
| master 落后（停在 6/29） | 分支拓扑债 | 待主干整理 |
| superpowers 下 6 个 nautilus-core `codex/*` worktree | 多属 FDE/compass 线 | 归还各框或清理 |
| G2.5 DeepSeek Harness A/B | Codex 排队中 | 未启动 |

## 下一目标（用户已批的方向）

1. ~~验收合并~~ ✅ 2026-08-22
2. ~~浮动 ID 探针~~ ✅ 2026-08-22 **G2-A0 门已完整跑通**：V3→V6 加性合同链
   （V4 max_tokens 8192+精确诊断 / V5 usage 白名单 7 字段 / V6 choices.logprobs 剥离）。
   根因链：Codex 8/15 `policy_violation`=日期版模型名不存在 → 结构拒绝=provider 真实
   schema 与合同白名单差三处 → V6 首次端到端：计费 CNY 0.00275、独立验证器判
   `candidate_verification_failed`（模型补丁格式对但没过测试=诚实能力判定）。
   探针总花费 < CNY 0.01（预算 10 元内）。
3. ~~Platform→V5→Compass 闭环~~ ✅ 2026-08-22 操作级执行成功（commit 17283ad2c，
   evidence `m1-r1a-synthetic-repair-readback-v1.json`）：op_r1a_vertical_01 全链
   receipts=accepted/policy_satisfied；V5 pin 定执行器签名；Compass 权威绑定；
   6 次精确重放零增长；33 fail-closed 用例 0 fallback；一次性库自动销毁。
   **Codex「单任务闭环」目标六判据全部达成，本锚使命完成。**

## 工作规则（用户 8/22 定）

- 红线内大胆干，红线外不用请示；只对**花钱、动生产、删东西**三类先问。
- 拒绝/失败后**允许零成本查证**（不再沿用 Codex "拒绝后不诊断"的死规矩）。
- 悬挂 worktree 48 小时内必须决定合并或丢弃。

## ✅ 用户批复(2026-08-22 · compass 代记)
- CNY 10 DeepSeek 探针:**已批准**(用 deepseek-v4-flash 浮动 ID,≤CNY 10)。
- genopt 印钞机:**已批准停止**(2026-08-22 compass 已执行:cloud `genopt-mint.timer` disable --now,disabled+inactive 实证;账面 7551 冻结待清算)。
