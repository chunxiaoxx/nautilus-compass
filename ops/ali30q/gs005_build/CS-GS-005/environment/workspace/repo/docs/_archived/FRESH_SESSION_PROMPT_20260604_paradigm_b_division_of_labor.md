=== Fresh Session · Benchmark Loop Phase 4 · 范式 B(division-of-labor)可证伪 probe 设计 ===

active anchor:
  #2 Path B 递归闭环(benchmark-grounded)· diverge(brainstorm)与 converge(执行)分离
  #3 反 D · ship 件数 ≠ 价值 · 负结果也是结果 · 不把噪声/best-of-N 当护城河
  #5 不重复造轮子 · 复用 PR#127 harness 骨架 · 先查再写
  #6 避免重复错误 · 不靠"我提醒自己"(seed3 挂死根因已记 · LLMClient.chat 无 timeout)
  #1 平台 agent-first · 范式 B 的专精 agent 生态契合
  #7 cross-dialog turf · brand=Nautilus

session-start 必读(按序):
  1. memory/design_20260603_multiagent_paradigm_b_division_of_labor_reframe.md  (本 Phase 方向源 · 核心)
  2. memory/session_20260603_phase3_multiseed_code_done_run_in_progress.md       (Phase 3 负结果 · frontmatter name=persona-moat-noise-verdict)
  3. docs/HANDOFF_20260603_023_phase3_multiseed_run_in_progress.md               (结案 handoff · PR #127)
  4. memory/design_20260601_external_selection_pressure_benchmark_loop.md        (benchmark=外部选择压力 · SWE-bench 候选)

一句话背景:
  Phase 1-3 测的是范式 A(ensemble/consensus:N agent 解同题去相关),HumanEval/M3 上已证伪
  (persona 净贡献 +1.83pp 不脱噪 · per-item flippy + HE/134 翻向 + 天花板 ~98%)。
  用户洞察矫正:业界主流 + 更可能有价值的是范式 B —— division-of-labor 专精编排
  (拆子任务 + 专门 skill/MCP + 精简隔离上下文 · 术业有专攻 · 避免单 agent 上下文混杂)。
  HumanEval 单函数题不需分解所以测不出 B → 换 repo-level 任务。

本 session 目标 · binding-DONE(binary · 一件 · 设计非 ship):
  用 brainstorming skill 产出一份范式 B 的【可证伪 probe 设计】,能回答清楚:
    ① 用什么任务(SWE-bench-lite 类 repo-level · 单 agent 会失败、有 headroom)
    ② 对照组怎么设:单 agent 长混杂上下文  vs  division-of-labor(专精子 agent + 隔离精简上下文)
    ③ fitness = 真实 issue 的 held-out 测试通过率(外部 ground truth · 非 LLM 裁判 · 非自指)
    ④ 单 agent baseline 怎么公平(同模型/同预算/同工具可达)
    ⑤ 第一个最小可证伪 probe(~N 个任务能跑出有区分度的数字 · 防变 shiny 发散)
  产出 = brainstorm 收敛后的设计文档 + (可选)writing-plans 切片。**不马上写实现代码**。

执行(brainstorming skill · 然后才 writing-plans):
  复用(anchor #5 · 先查再写):
    PR #127 / worktree benchmark/phase3-multiseed 的 harness 骨架:
      humaneval_consensus_probe.py 的 load/score_with_held_out/run_program/escape-noise stats 可复用
    范式 B 的编排逻辑(任务分解 + 子 agent 上下文隔离)是新的 · 调研现有 agent-engine 里有没有可复用的 orchestration
    SWE-bench-lite loader:先查 datasets 有没有现成 · human_eval runner 经验(Unix-only 坑)迁移注意
  根因 follow-up(可顺手 · 小):LLMClient.chat 加 timeout= 透传 messages.create(~180s)· seed3 挂死根因

护栏 / forcing function:
  - 先 brainstorm 收敛再 converge · 不 diverge 乱铺(本命题 5 周复发根因 = 工作流永不闭环)
  - 一件 binding-DONE(= 设计文档)未达不开实现 scope · 不建在空 plumbing 上
  - R1 drift alert → 强制自停(上个 session 真 fire 过 "全做" score-0.094 · 守住了)
  - R2 "全做" → push back · R3 4h cap · R4 ship 前 git 检查 · R5 anchor 先读
  - benchmark = proxy 非市场验证 · 正信号/脱噪前不 wire V5 RSI/经济环/compass L4
  - "真" 不作强调副词 · summary/选项让 user 直接看懂

cross-dialog(锁定 · 不催不抢):
  - V5 ACK #25:hold · 能力融合 design 与 benchmark-fitness wire 解耦 · 不写 outbound 直到有正信号
  - 5 outstanding 合约(compass b2/sub_a2/recall_c1 · content-engine naming a1 · family taxonomy)= 各 dialog turf · benchmark 主线进行时不并行铺(除非 user 明示)· content_engine_naming_a1(due 6/9 · platform-soul turf)若 benchmark parked 可作并行候选
  - compass sub_a2 已 CLOSED · 改 engine_cycle_outcomes/agent_tool_calls schema 走 7 天 notify registry

待 user / git:
  - master = origin/master(ahead 0 · 已 push · HEAD 43764c0f6)
  - PR #127(Phase 3 · code+数据+负判定)待 user merge 决定 · worktree benchmark/phase3-multiseed 保留
  - soul daemon timer 保持 inactive

session-end 必走:
  - honest acknowledge 真 advance vs 发散 · 1 件 binding-DONE(设计)后 handoff
  - R3 真触必停 · 不靠"我提醒自己"
