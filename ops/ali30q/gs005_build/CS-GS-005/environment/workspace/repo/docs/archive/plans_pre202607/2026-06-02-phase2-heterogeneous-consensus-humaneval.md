# Plan · Phase 2 · Persona-diverse consensus on HumanEval (find the positive delta)

> 写 2026-06-02 · platform-soul dialog · 接 Phase 1 负结果。本 plan 是新 session 用 **executing-plans** 直接 TDD 接的可执行设计。
> 前置阅读:`memory/session_20260602_benchmark_consensus_probe_negative_result.md` + `memory/observation_20260602_platform_self_referential_economy_3layer.md`

## Context · 为什么是这个

Phase 1 在 **Devign 二元 bug 检测** 上测 consensus:vote −11.5%、judge 0,都没让"多 agent 更可靠"站住。审计根因:① 任务是**二元分类**(consensus 结构上最差——答案空间只有 2,错的没法散开);② 同质采样(同一 M3,错误相关,clean 偏置被放大)。

Phase 2 同时修这两点:
1. **换任务** → 代码生成 + 测试执行(大答案空间 + **客观外部 ground truth = 测试 pass/fail**,不靠 LLM 裁判 · 最产品对齐)。
2. **换机制** → persona-diverse 生成(失败模式正交 → 错误解相关),自产测试做选择。

**跨对话框背景(锁定)**:V5 / compass L4 / soul 全部 silent-wait 在"platform 产出一个正 delta"(agent-dialog outbound #22 修订解锁条件)。本 plan 出的信号 = 解锁键。**正 delta 前不通知 V5 wire**。

## Done Criteria(binding-DONE · binary)

三臂对照,每臂在 HumanEval 子集上 pass@1(held-out 测试评分),输出 3 个真数字:
1. **single**:单 persona 1 次
2. **homogeneous best-of-3**:同 prompt ×3 + 自测选
3. **persona-diverse best-of-3**:3 正交 persona + 自测选

- **(3)−(1)** = consensus 总增益(= 给 V5 的解锁信号候选)
- **(3)−(2)** = persona 多样性净贡献 = **RAID 编排是否真值钱**(产品护城河判据)

binding-DONE = 三数字 + 两个 delta,审计 per-item。delta>0 如实记为正信号;≤0 如实记不假装(可能 task/persona 仍不对 → 决定下一步,非粉饰)。

## 复用(anchor #5 · 先查再写)

- `phase3/agent-engine/benchmarks/consensus_reliability_probe.py` —— **已有** `parse_label`/`run_probe`/labeler 框架 + ThreadPoolExecutor 并发 + 数据优先存盘。扩展,不重写。
- `datasets`(cloud 4.8.5 已装)load `openai_humaneval`(164 题:prompt/test/entry_point/canonical_solution)。
- **sandbox**:`pip install human-eval`(纯 Python 小包)→ 用官方 `human_eval.execution.check_correctness(problem, completion, timeout=5.0)`(内置 subprocess+timeout+reliability_guard)。**不自造 sandbox。** 装不上则 fallback ~35 行 runner(拼 prompt+completion+test+`check(entry_point)` → subprocess timeout · 测试逻辑来自 HumanEval test 字符串)。
- LLM:`llm/client.py get_llm_client()`(M3 · 本地+cloud key 有)。Tier B 跨 lab 对照需 DeepSeek(cloud `.soul-env` 有 DEEPSEEK_BASE_URL/MODEL)——client 是否支持切 provider 要先查;不支持则 Tier B 延后,先做 Tier A(同 M3 persona-diverse,产品赌注)。

## 3 个正交生成 persona(代码生成 · 失败模式解相关)

| persona | system 框架 | 解掉的 bug 源 |
|---|---|---|
| edge-case-first | "先枚举边界(空/负/越界/0/单元素)各自处理再实现" | off-by-one · 空输入 |
| spec-literalist | "逐句重读 docstring,严格按规格+返回类型,对每个 docstring 例子验证" | 误读规格 |
| test-driven | "先从 docstring 写 3-4 测试,实现到全过,心算 trace" | 逻辑 bug |

3 个够(anchor #3 不过度)。每个 persona **同时产 docstring 衍生可见测试**作选择信号。

## 选择步(防 oracle 作弊 · 关键)

- 选择 **只用 agent 自产的可见测试**(同轻 sandbox 跑),不碰 held-out HumanEval 测试。选通过最多 pooled 自测的候选,平局取最短/first。
- held-out 测试**只用来给最终 pick 评分**。
- ⚠ 不可让 held-out oracle 直接选最优 → 那是平凡 best-of-N ≥ single,无价值。真问题 = agent 自测能否挑对。

## TDD 任务分解(RED→GREEN · 每步独立可测)

1. **`load_humaneval_subset(n)`** → 取 ~30-40 题(datasets)。test:返回 n 题且每题有 prompt/test/entry_point。
2. **`build_persona_prompt(problem, persona)`** → 纯函数。test:含 docstring、persona 指令、要求产可见测试 + 最终代码块。
3. **`extract_code(llm_output)`** → 从自由文本抽 ```python 代码块。test:多种围栏/无围栏 case。
4. **`extract_visible_tests(llm_output)`** → 抽 persona 自产的 assert/测试。test:mock 输出。
5. **`select_by_self_tests(candidates, visible_tests, sandbox_runner)`** → 纯逻辑(注入 mock runner)。test:候选 A 过 3、B 过 1 → 选 A;平局取最短。
6. **`score_with_held_out(pick, problem)`** → 包 check_correctness。test:canonical_solution 必过、明显错解必败(用 1-2 题真跑或 mock)。
7. **integration `run_codegen_arm(problems, mode, ...)`**(LLM · 非离线测,cloud 真跑验证)→ 三臂 single/homogeneous/persona-diverse。
8. **main**:并发跑三臂 → 输出 3 pass@1 + 2 delta + per-item + raw,存盘。

## Verification(防假装成功)

- sandbox 先用 canonical_solution 自检(必 100% 过)+ 故意错解(必败)→ 证评分管道对,再跑 LLM。
- 三臂数字第二工具核(重跑看方差 · N=30-40 仍有噪声,报方差)。
- per-item 看 persona-diverse 到底在哪些题赢/churn,不只看汇总。
- 任何"正 delta"先排除"是不是采样更多的平凡收益"((3) vs (2) 必看)。

## Parking(不在本 binding-DONE)

- Tier B 跨 lab(M3+DeepSeek)对照 —— client 多 provider 支持先查;Tier A 出结果后再加。
- 接 fitness 进 soul gate / 经济环 / compass L4 —— 等正 delta 后另起。
- 进口外部 agent 当选择压力 —— Phase 2 出信号后的结构化方向。
- 通知 V5 wire —— 仅在正 delta 后。

## 出 binding-DONE 后

- 正 delta(尤其 (3)>(2)):写 outbound 给 agent-dialog(解锁信号 + 是否带编排护城河)+ 喂 compass L4 真 fitness。
- ≤0:如实记 + 决策(换 task domain / 换 model / 认"可靠性弱命题"转产品故事)。
