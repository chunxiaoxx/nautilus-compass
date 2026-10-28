# Path B — correctness-binary RSI 设计(节点4·2026-06-18·KernelBench 证负后的 redirect)

> 前提(probe-backed·本 session 穷尽证):KernelBench speedup 上 in-context 记忆闭不了 RSI——p13 ceiling-bound(~1.03·correctness yield 0/16)+ p18 single-trick(~180×·turn-2 vs turn-1 delta 0.54% 在噪声内)= **两极都无"记忆助 turn-2 渐进改进"的梯度**。根因:speedup reward 要么没空间、要么单跳到顶、且 2× anti-cheat cap 排除算法改进区。

## 为什么 correctness-binary 能闭(KernelBench 不能闭的反面)

| 维度 | KernelBench speedup | correctness-binary(SWE) |
|---|---|---|
| reward | 连续 speedup·噪声 ~0.7%·上限低 | **离散 测试通过数·0→N·无计时噪声** |
| headroom | p13~1.03 / p18 单跳 180× | **fail→pass 是真梯度**(patch 可 0→3→全过) |
| 记忆的用武之地 | kernel 已最优·记忆没东西加 | **记忆=上轮的失败测试+报错** → 下轮针对性修 |
| anti-cheat cap 冲突 | 有(>2× 被 gate) | 无 |

**核心**:RSI-via-记忆需要"部分解 + 可定向改进"的梯度。SWE 任务天然有:turn-1 patch 过 2/5 测试 + 留 3 个 fail 的 traceback → 记忆喂这 3 个报错 → turn-2 针对性修 → 过 4/5。**turn-2 测试通过数 > turn-1 = RSI 真证**(离散·无噪声·不需噪声门)。

## 实验设计(复用现有 2-turn harness 结构)

`scripts/rsi_p13_loop.py` 的骨架可直接泛化(produce→verify→抽记忆→produce→verify→判),只换两件:
1. **producer prompt**:KernelBench 题面 → SWE 任务(repo 上下文 + issue + 失败测试)。
2. **verifier**:`gpu_eval_candidate`(kb_eval) → SWE 测试运行器(apply patch → run pytest → 通过数/resolved)。

**判据**(替 raw speedup):`reward = n_tests_passed`(或 binary resolved)。`rsi_proven = turn2_passed > turn1_passed`(离散·无需噪声门)。

**记忆抽取**(替 build_memory):turn-1 best patch + 它的失败测试名 + traceback 摘要 → "上轮这个 patch 过了 X 个、这 Y 个 fail 因为 <报错>·针对性修"。这是 grounded(真实测试输出·非泛化)。

## 🔴 唯一外部依赖(需用户授权·跨框)

SWE 验证环境(apply patch + run tests in isolated repo)= **compass resolve env turf**(FrontierSWE/SWE-bench 在它手·memory 6/17 §33 已定)。两条路:
- **A(自给·荐先试)**:SWE-bench-**lite** 单文件易题·本地起一个最小验证器(clone instance repo → apply patch → pytest → 数通过)·不依赖 compass。先证机制成立。
- **B(跨框)**:接 compass 现成 resolve env·题池更全但要它配合 + 用户授权跨框接口(违单一-owner·故 defer)。

## 执行步骤(节点4)· 进度 2026-06-18
- ✅ **验证器纯核**(`services/swe_verify.py`·7 TDD):parse_pytest_summary / extract_failed_tests / swe_reward(=通过数)/ rsi_improved(离散无噪声门)/ build_swe_memory(失败测试+报错+patch)。
- ✅ **effect 层**(`services/swe_runner.py`·4 集成 TDD):run_candidate = copy base→git apply→pytest→stdout(副本做·base 不污染·apply 失败→reward None)。端到端验通(合成 git repo)。
- ⬜ **3. 真 instance**:选 1 道 SWE-bench-lite 易题(单文件·测试少·known-resolvable)·下载 instance repo+base commit+test。
- ⬜ **4. producer 接线**:泛化 `rsi_p13_loop` 结构(produce→verify→记忆→produce）·producer=deepseek/qwen 产 patch(API·复用 bailian_complete)·verifier=swe_runner.run_candidate。
- ⬜ **5. 跑 2-turn**:turn-1 patch(无记忆)→过 X 个·记忆=失败测试+traceback·turn-2 patch(注入)→过 Y 个·判 `rsi_improved(X,Y)`=Y>X(离散·无噪声门)→ 写 PoI + 交 V5 wire。**这是真能闭的环。**
- 🔴 剩 3-5 需 API(producer)+ 真 instance 下载 = fresh session(R3）。验证器+effect 两砖已 TDD 备好,fresh session 只接 producer + 选题。

## 诚实风险(先标·防 facade)
- SWE 易题强模型可能 turn-1 就全过(X=N)→ 无改进空间(像 p18 single-trick)。**对策**:挑 turn-1 部分过的题(先 pilot 几道看 turn-1 pass 率·要 0<X<N 的"中间梯度"题)。
- 一轮记忆未必翻 fail→pass(SWE 难)。**对策**:lite 易题先证机制·难题后扩。
- 别把"turn-1 就全过"当 RSI(那是题太易·非记忆功劳)。

关联 [[session_20260618_p13_rsi_singleowner_close_fast1_structurally_dead]] · design 2026-06-14-rsi-distillation-flywheel · [[FDE_BUSINESS_CHARTER]] · docs/LOOP_PROMPTS_20260618.md(节点4)
