# HANDOFF #027 · platform-soul · benchmark 弧收尾(三连负)→ FDE 字节业务成新主线 · 三框协同

> 写 2026-06-05 00:57 · platform-soul dialog · 收口一个 ~12h marathon。单一 fresh-session 入口。
> 取代 [#026](./HANDOFF_20260604_026_MASTER_benchmark_ruler_built_paradigm_negative_value_reframe.md)。

## Fresh-session 提示词(复制即用)
```
接 HANDOFF #027(platform-soul · benchmark 弧已收尾 + FDE 字节业务主线)。
session-start 必读(按序):
- docs/HANDOFF_20260605_027_...md(本文 · 全图)
- memory/session_20260604_fde_3way_convergence_harness_probe3_cycle1_negative.md(FDE 收敛 + Probe3 负)
- Projects/vertical-task-factory/FDE_CONVERGENCE.md(三方分工 canonical)+ DELIVERY_SCHEMA.md(买方 schema)
战略锁定(勿重开):benchmark 弧三连负(范式 A/B + 递归自改 Probe3)· 平台价值 = 外部 fitness 尺 + FDE QC/语料,不在 orchestration/auto-improve。
主线 = FDE 飞书垂域题目(买方=字节)· 管道端到端已证 · 真数据 blocker compass 正解。
```

## 30 秒状态
- **benchmark 弧 CLOSED**:范式 A(ensemble)负 · B(decomp)负 · **递归自改(Probe3)负且退化**(probe 0.333→0.20→0.00 · val 0.80→0.70→0.60 · 0/2 accepted · 保守门守住 · run 死于 cycle3 SSL 抖动,N=2 候选已决定性)。→ 平台价值 reframe 坐实:**外部 fitness 尺(能诚实证伪自己)= 真资产** + FDE QC/语料。**正信号前不 wire live soul/V5**(anchor #3/#17)。
- **FDE 字节业务 = 新主线**:我们是外包方(专家提交→我们飞书表 QC→交付字节)· 管道端到端已证(v5 copilot→M3 答→**我 soul harness 评 10/11 overall_pass**)· 真数据 blocker 正被 compass 解。

## 三框分工 + 状态(canonical = vertical-task-factory/FDE_CONVERGENCE.md)
| 框 | lane | 状态 |
|---|---|---|
| **soul(我)** | 标准 + 复核/QC + 外部 fitness | ✅ RUBRIC · DELIVERY_SCHEMA(买方 14→16 列 + 7→8 类目映射)· harness(checklist_scorer 答案-QC + rubric_check 任务-QC · **14 TDD** · 2 bug 修)· 2 金样例(L2 科技/AI + L3 金融/量化)· 跨框裁定 ×4 |
| **compass** | 工具栈 + 飞书留存 + 凭据网关 | ✅ **接通飞书在线表(196 行 + 真 fileToken 附件可下载 → G2 解中)** · fde-row-assembler(16 列 · 复用我 rubric_check)· checklist-from-task(任务特定 · 喂我 scorer)· parse-messy-pdf/excel/html toolstack · 凭据网关 design |
| **v5** | 出题 copilot 执行体 | ✅ **copilot 端到端跑通**(金样例 10/11 过我 harness)· 直连飞书撞登录墙(compass turf 已解) |

## soul lane 资产(git 仓 `Projects/vertical-task-factory` · commit 到 `ad120b2`+)
- `PRODUCTION_RUBRIC.md`(二期 QC 闸)· `DELIVERY_SCHEMA.md`(买方 schema canonical + 类目映射)
- `harness/`(checklist_scorer + rubric_check + qc_smoke · **14 TDD green** · make_llm_judge 用 MiniMax 顶 Anthropic)
- `examples/`(L2 + L3 金样例 · 数据自洽核验)· `FDE_CONVERGENCE.md` · `CAPABILITY_PRELOAD.md`
- 跨框交付:harness_fix_done(v5)· official_example_answers + content_engine_naming_ruling + mcp_envvar_contract(compass)

## 关键路径 / 下一步(真 PMF)
1. 🔴 **compass 拉真 196 表 + 下载附件** → 真 16 例有真附件(G2 解)→ **三框跑首条「买方真题」端到端**(copilot→我 QC→16 列打包)= 第一个非金样例的真证据。
2. 🔴 **PMF 硬证据**:真专家场景计时 vs 人类 13-24h 基线 → 测 agent 省 ≥50% 时间。
3. 批次提交字节 → 接收 = 第一个**外部价值** verdict → 语料/模板累积(非 auto-improve)。
4. 远期:8 域专精 copilot(Probe 2 · multi-agent 唯一没测的价值)。

## Outstanding / backlog
- **cnt_content_engine_soul_naming_a1**(due 6/9):我裁定已交付(`content-engine` 独立中立)· 等 compass consume 关合约。
- **安全**:用户在对话明文贴过 8 API key + 飞书 app_secret → **建议全轮换** · 凭据该进 compass 网关不进聊天。
- **harness backlog**:litellm.completion 加 timeout(+retry)· 同 Probe3 propose_fn 课(慢网会挂 · 我本地 qc_smoke 因此复现不了,但 v5 端到端 + 14 单测已验修复)。
- **Probe3 backlog**:propose_fn retry + persist 候选(若要干净 N=3 · 低价值)。

## Standing infra(复用 · 别重建)
- Probe 装置:`phase3/agent-engine/benchmarks/swebench_probe/`(evolve_run/probe1_runner/decomp_solver · relay 52889 · venv swebench-probe-venv)· run dir `swebench-probe-run`。
- FDE:`Projects/vertical-task-factory`(独立 git 仓 · 三框共享工作区 · compass 的 fde-toolbox 也在)。
- M3 key:MiniMax MCP 配置(`.claude.json` env)· make_llm_judge/propose 都用它。

## 守住 / 教训(本 marathon)
- 「真」当强调副词复发被 hook 抓多次 → 收。
- ~12h marathon · 用户多次「扩范围/尽快」push → 守 anchor #3:channel 紧迫到真 lever(用户种子/买方数据)· 不 spray 工件。
- `/goal` cycles=4 死 run 不可达 → 不伪造数据满足机械条件(诚实底线)· 等用户 /goal clear。
- 三框 coherence 真接上(各 own lane · 复用不重造 · checklist schema 成共享标准)。
