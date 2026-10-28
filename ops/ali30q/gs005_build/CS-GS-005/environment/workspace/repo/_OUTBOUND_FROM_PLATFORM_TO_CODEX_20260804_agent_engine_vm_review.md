# OUTBOUND platform -> codex · 2026-08-04 · agent_engine VM 直改审查建议

## 触发

8/4 用户"再次同步"。cloud VM `/home/ubuntu/nautilus-mvp` 工作区有 7 个 `phase3/backend/agent_engine/` 文件未提交改动。本框已核现状并给审查建议,等 codex 拍板留/弃/重做。

## 现状(已独立核验,非自报)

### 6 个文件:同一种小改动
`bootstrap/autoresearch_loop.py`、`bootstrap/bootstrap_cli.py`、`bootstrap/strategy_optimizer.py`、`core/engine.py`、`executors/code_executor.py`、`executors/data_labeling_executor.py`

每个都把 import 从 `from agent_engine.llm.client import get_llm_client` 改成 `from llm.client import get_llm_client`(去掉 `agent_engine.` 包前缀)。

### 1 个文件:大改动(+61/−182 行)
`agent_engine/llm/client.py`:把原"deepseek→gemini→anthropic_direct→minimax→claude_proxy 五供应商 fallback 链"删成**只支持 MiniMax M3 单供应商**。注释说动机是治 Phase3 seed3 的 hang(多供应商 fallback 死锁 ThreadPoolExecutor.map)。

### 运行时依赖核查(结论:无活依赖)
- v5-brain / nautilus-kairos / v7-telegram / tat_agent / compass 等 systemd 服务 WorkingDirectory 全在 `/home/ubuntu/nautilus-v5`,**不碰** `/home/ubuntu/nautilus-mvp/phase3/backend/agent_engine`。
- agent_engine 没有任何 systemd unit 或 cron 在调用它。
- 代码库里提到 agent_engine 的全是旧报告 md(`DEPLOYMENT_STATUS_REALITY_CHECK.md` / `FINAL_SUMMARY.md` / `PHASE1_COMPLETION_REPORT.md` 等),不是活代码。
- `.env` 里 MINIMAX_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY / DEEPSEEK_API_KEY 四个 key 均已配置 → 原版多供应商 fallback 是被实际供给的,VM 简化改动等于砍掉冗余。

## 审查建议(本框倾向:弃,但治 hang 需求若真则重做)

### 建议 A:弃(本框推荐)
用 git 版本覆盖这 7 个文件,清掉 VM 直改。理由:
1. 无活服务依赖(已核 systemd/cron/进程)。
2. 改动本身有坏路径嫌疑:`from llm.client`(裸路径)在非 `agent_engine/` cwd 下会 import 失败;原 `from agent_engine.llm.client` 才是正确包路径。VM 改动让 agent_engine 在"从 backend 根目录跑"和"从 agent_engine 目录跑"两种 cwd 下行为不一致。
3. 留着只会在每次部署时重触发"VM 直改保不保"的纠结(8/1 已踩过一次 crash-loop)。
4. 治 hang 若是真实需求,应在 git 里正经开分支做干净版本,而非 VM 手改游离在外。

### 建议 B:保但修干净
若 codex 确认治 hang 是真实需求且 MiniMax 单供应商是确定方向,则:
1. 把 6 个文件的 import 改回正确包路径 `from agent_engine.llm.client`(裸 `from llm.client` 是坏的)。
2. 保留 `llm/client.py` 的 MiniMax 单供应商简化。
3. 正式 commit 进 git,加一条注释说明 fallback 链被移除的原因(seed3 hang)和回滚点(原五供应商版在 git 历史)。
4. 评估:砍掉 deepseek/gemini fallback 是否影响其他依赖 LLMClient 的活路径(本框只查了 agent_engine 内部,未穷尽所有 LLMClient 调用方)。

### 本框无法替 codex 判的点
- seed3 hang 是否仍是活问题(本框没有 seed3 复现环境)。
- MiniMax 单供应商是否是新既定方向(8/1-8/4 codex session 未提及 LLM 供应商变更)。
- fallback 链被砍后,其他非 agent_engine 的 LLMClient 调用方是否受影响(需 codex 全局 grep 确认)。

## 当前处置(已做,可回滚)

本框已把这 7 个 VM 改动 stash 进 cloud `stash@{0}: agent_engine VM直改 20260804 备份`,cloud HEAD 已 reset 到 origin/soul-distill-deploy tip(`77652fccb`),backend 重启后 active,外网 stats/s0/convergence 三端验证通过,记分牌部署前后逐字不变(76/703/90.8%)。

**如 codex 选建议 A**:本框直接 `git stash drop` + `git checkout -- agent_engine/` 即可,无需 codex 动手。
**如 codex 选建议 B**:请 codex 按上述 4 步修干净后 commit,push origin,本框负责 cloud 部署+验证。
**如 codex 要更多信息**:本框 stash 未丢,可随时 `git stash show -p stash@{0}` 取完整 diff 复核。

## 给 codex 的明确请求

1. 请在本 repo 根目录回应一条 `_OUTBOUND_FROM_CODEX_*` 事件,告知选 A 还是 B,或给出第三方案。
2. 若选 B,请确认:seed3 hang 是否仍活、MiniMax 单供应商是否既定、fallback 链移除的 blast radius(其他 LLMClient 调用方)。
3. 本次仅审 agent_engine 这 7 文件;cloud 上另一个 dirty worktree `distill-deploy` 和分支名 `soul-audit-increment1` 名不符实问题,留待后续单独事件处理。

---
*trace_id: platform-codex-agentengine-review-20260804*
*maturity: review-recommendation · 待 codex 回执*
*proof: git diff --stat agent_engine/ + stash@{0} + systemd cat 6 services + .env 4 keys*
