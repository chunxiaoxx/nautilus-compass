=== Fresh Session · Phase 2 · Persona-diverse Consensus · positive-delta hunt ===

active anchor:
  #2 Path B 递归闭环(benchmark-grounded)· 产品与闭环合一
  #3 反 D · ship 件数 ≠ 价值(falsifiable delta 才算数)
  #5 不重复造轮子 · 先调研再写
  #6 避免重复错误 · 不靠"我提醒自己"
  #7 cross-dialog turf · brand=Nautilus

session-start 必读(按序):
  1. docs/plans/2026-06-02-phase2-heterogeneous-consensus-humaneval.md  (本 session 的可执行 plan · 主线)
  2. memory/session_20260602_benchmark_consensus_probe_negative_result.md  (Phase 1 负结果 + 机制)
  3. memory/observation_20260602_platform_self_referential_economy_3layer.md  (自指陷阱 3 层实证 · 为何要外部 fitness)
  4. docs/HANDOFF_20260602_021_benchmark_phase1_negative_result.md  (Phase 1 落地状态)
  5. memory/design_20260601_external_selection_pressure_benchmark_loop.md  (方向源)

一句话命题:
  Phase 1 在二元 bug 检测上证伪了朴素 consensus(vote -11.5% / judge 0)。
  根因 = 任务选错(二元无答案空间)+ 同质采样(错误相关)。
  Phase 2 = 换代码生成+测试执行(客观外部 ground truth)+ persona-diverse 生成(错误解相关),
  找一个让 multi-agent > single 的正 delta。

/goal · binding-DONE(binary · workflow lock · 一件):
  三臂在 HumanEval 子集(~30-40 题)的 pass@1(held-out 测试评分):
    (1) single · (2) homogeneous best-of-3 · (3) persona-diverse best-of-3
  输出 3 真数字 + 两 delta:
    (3)-(1) = consensus 总增益(给 V5 的解锁信号候选)
    (3)-(2) = persona 编排净贡献(产品护城河判据)
  delta>0 如实记为正信号;<=0 如实记不假装(换 task/model 或认弱命题)。

执行(executing-plans · TDD 8 步在 plan 里):
  step 0: pip install human-eval + sandbox 自检(canonical_solution 必 100% 过 / 故意错解必败)
  step 1-6: TDD 纯逻辑(load_subset / build_persona_prompt / extract_code / extract_visible_tests
            / select_by_self_tests(注入 mock runner) / score_with_held_out)
  step 7-8: integration 三臂 cloud 真跑 + main 并发输出

复用(先查再写 · anchor #5):
  phase3/agent-engine/benchmarks/consensus_reliability_probe.py  (parse/run_probe/并发框架 · 扩展不重写)
  datasets(cloud 4.8.5)load openai_humaneval · human_eval.execution.check_correctness(官方 sandbox · 不自造)
  llm/client.py get_llm_client()(M3 · 本地+cloud key)

3 个正交生成 persona:edge-case-first / spec-literalist / test-driven(各产可见测试作选择信号)

不动 / parking(反 anchor):
  - 防 oracle 作弊:选择只用 agent 自产可见测试 · held-out 只评最终 pick · 不让 oracle 直接选(平凡 best-of-N 无价值)
  - Tier B 跨 lab(M3+DeepSeek)对照 · client 多 provider 支持先查 · Tier A 出结果后再加
  - 接 fitness 进 soul/经济环/compass L4 · 进口外部 agent · 通知 V5 wire —— 全部等正 delta 后
  - V5/Kairos/compass repo(anchor #7)

forcing function / 护栏:
  - R3 4h cap 严守 · 不复发长 marathon(上个 session 偏长 · 这次到点即停)
  - 一件 binding-DONE 未达不开新 scope · diverge(brainstorm)与 converge(plan->execute)分离
  - 每个 "success" 第二工具核(重跑 / raw output / per-item)· N=30-40 有方差 · 报方差
  - sandbox 先自检再跑 LLM · 不信"应该能跑"
  - "真" 不作强调副词 · summary/选项让用户直接看懂 · 不堆缩写术语

cross-dialog(锁定 · 不催不抢):
  - V5/compass L4/soul 全部 silent-wait 在"platform 产出正 delta"(agent-dialog outbound #22)
  - 正 delta(尤其 (3)>(2))才写 outbound 通知 V5 + 喂 compass L4 · 在那之前不发
  - 合约 cnt_compass_soul_sub_a2(due 6/7 · secure channel 交付)· cnt_compass_v5_outcome_b2(due 6/5)standing

待 user(跨 session):
  - master 领先 origin(docs plan + 本 prompt commit · 未 push)· 需推说一声
  - soul daemon timer 保持 inactive(设计内 · 等正 delta 才考虑 re-enable)

session-end 必走:
  - honest acknowledge 本 session 真 advance vs noise · 1 件 binding-DONE 后 handoff
  - R3 真触必停 · 不靠"我提醒自己"
