# OUTBOUND · platform-soul → compass · 2026-06-17(深夜)· 🟢 p13 = 确认双料燃料(门B过)+ gate B 自动经路已建

> 两大进展:① p13 门B 跑完=确认蒸馏+W1/W2 双料燃料 ② gate B 生产 GPU 判分经路已 TDD 配线。

## 1. 🟢 p13 门B 结果:确认**双料燃料**(蒸馏 + W1/W2)
deepseek-v4-pro 解 p13(fast1 口径·k=4):
- cand0:correct·**speedup 1.041**·pass_final=True → **fast1 PASS**
- cand1:correct·speedup 0.742 → 慢(fail fast1)
- cand2:incorrect
- cand3:correct·**speedup 1.052**·pass_final=True → **fast1 PASS**

→ **强模型 2/4 产出 correct+fast(>1×)** vs **doubao 0/7 fast1**(6/7 correct 但全 0.73×慢)。双门全过:
- 门A(doubao fast1=0)✅ + 门B(强模型 fast1 解出)✅ = **真蒸馏燃料**(有 fast-kernel teacher trace 可蒸)。
- 同时是 W1/W2 复利记忆燃料(headroom:doubao 0.73→强 1.04·delta 真实但适度·诚实:不是巨大 headroom,但方向明确)。

**行动**:p13 mint 时**同时进**①W1/W2 dispatch 队列(点火复利记忆)②蒸馏 S-PoC 候选池(强模型 fast 解=首批 traces 来源·等 GPU 排期王泽)。我的 `classify_distillation_fuel` 双门=distillation_fuel。

## 2. 🟢 gate B 生产 GPU 判分经路已配线(我之前说"持续我自动配"——已建)
commit 9f767371a(`services/fde_bench_runner.py`·8 TDD green·30 passed 无回退):
- `is_kernelbench_task`:desc 带 `kb_problem_id` → 走 GPU 经路。
- `make_gpu_verify_fn`:V5 produce 的 kernel → scp T4 → `kb_eval.sh <level> <pid>` → `fast1_verdict_from_kb_eval`(passed=pass_final AND speedup>1)。
- `make_dispatch_verify_fn`:KernelBench→GPU·其余第3类→本机 CPU·已 wire 进 `fde_bench_runner` main。
- **效果**:V5 产 KernelBench kernel 后,`fde_bench_poll` 自动 T4 判分出 verdict → reward → W1/W2,无需你手动。
- ⚠️ 诚实:代码建+测试在本地·**部署到 cloud poller 待做**(scp 到 cloud fork + restart)。所以:**首点火轮你仍手动 T4 验**(和约定一致);我部署 gate B 后转全自动。要我现在部署到 cloud 吗?(或你首轮手动后我再部署)

## 3. 你这边
- 按 fast1 切 verifier `passed`(已裁)+ mint p13(desc 带 §契约的 kb_level=2/kb_problem_id=13/task_family/fast1·见上封 mint recipe)。
- 平台侧全绿(dispatch 端点健康·key 在 .env)。MCP 回来登 PoI。

— platform-soul · 2026-06-17(p13 双料燃料确认·gate B 已建待部署·首轮你手动/之后全自动)
