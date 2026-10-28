# HANDOFF #023 · Phase 3 persona-moat = NEGATIVE (binding-DONE · CLOSED)

> 写 2026-06-03 · platform-soul dialog · Phase 3 = 判 persona 净贡献 (3)-(2) 是否脱离噪声。
> **结案:未脱噪 · persona 编排护城河在 M3/HumanEval 不成立。PR #127 已建。**

## ✅ 最终结案(2026-06-03 凌晨)

- **判定:NEGATIVE** · full N=164 × 2 seed(seed3 挂死被杀)· (3)-(2) net mean **+1.83pp · 符号检验 p=0.109 不显著** · per-item 审计:零跨-seed 一致 persona-win + HE/134 翻向 + 4/8 win 是 greedy single 本就解出(选择运气)· 两臂贴 ~98% 天花板 = 噪声非结构。
- **PR #127**:https://github.com/chunxiaoxx/nautilus-core/pull/127(code + 2-seed 数据 + verdict · 33 TDD green · 待 user merge)。
- **不写 outbound #15 · 不 wire V5/经济环/compass L4**(未脱噪 · anchor #3)。
- **下一 Phase 候选**:更难数据集(单 LLM 真失败有 headroom)/ 跨 lab M3+DeepSeek 去相关 / 认弱命题转产品故事。
- **根因 follow-up**:`LLMClient.chat` 无 per-request timeout → hang 卡死 `ThreadPoolExecutor.map`。修:`messages.create(timeout=~180s)`。
- 详见 memory `session_20260603_phase3_multiseed_code_done_run_in_progress.md`(frontmatter name = persona-moat-noise-verdict)。

---

_以下为运行中阶段的原始交接(已被上方结案取代,留作追溯):_

## 30 秒状态

承 [HANDOFF #022](./HANDOFF_20260602_022_phase2_positive_delta.md):Phase 2 拿到首个正 delta single 67.5% → persona best-3 97.5%(+30pp),但拆开 (2)-(1)=+27.5pp 是已知 best-of-N,真正护城河判据 (3)-(2) persona 净贡献仅 +2.5pp(1 题 · N=40 噪声内)。Phase 3 用 full 164 × 多 seed 判 (3)-(2) 脱噪否。

**代码 binding-DONE。数据跑:M3 thinking + 16k tokens 调用慢 + MiniMax 限流 → 3 seed × 164(~3116 calls)要好几小时,超本 session R3 4h。每 seed 增量落盘,跑满 3 seed 跨 session。**

## 已完成(代码 · worktree 隔离)

- worktree:`.worktrees/phase3-multiseed`(branch `benchmark/phase3-multiseed`,**未 merge master**)
- 3 commits · 33 TDD green:
  1. `0ea0579c1` multi-seed 三臂 probe + escape-the-noise stats(`aggregate_multiseed` / `binom_sign_test` / `items_map` / 多 seed main + 每 seed 增量落盘)
  2. `6b2e73950` `_chat_safe` 重试包装(429 不崩长跑)
- 文件:`phase3/agent-engine/benchmarks/humaneval_consensus_probe.py` + `test_humaneval_consensus.py`

## 运行中的数据跑

- 进程:后台 python(launch 19:26 · `humaneval_consensus_probe.py 164 3 8`)· detach 健康
- 结果文件(每 seed 增量覆写):
  `.worktrees/phase3-multiseed/phase3/agent-engine/benchmarks/humaneval_multiseed_result.json`
- 已知:**single (temp 0) = 76.8% (126/164)** · 基线 sane(无 auth/全空 confound)
- seed 1/3 进行中(JSON 在 seed 1 完成后首次落盘)

## 下个 session 怎么收尾(harvest)

1. 读结果 JSON 的 `aggregate` 块(脚本自动算好,无需手动统计):
   - `persona_net`: per_seed 列表 / mean / std / 95% CI / all_seeds_positive
   - `item_level`: persona_wins / homo_wins / discordant / **sign_test_p**
   - `escapes_noise`(bool · 保守:mean>0 AND 每 seed 都正 AND sign p<0.05)
2. 看 `seeds_done`:若进程已结束但 <3,即跑到哪算哪(2 seed 也是有效多 seed 结果)。进程死了要重跑就 `cd` 到 worktree benchmarks 跑 `python humaneval_consensus_probe.py 164 3 8`(注意会覆写,先备份现有 JSON)。
3. **诚实判据(关键防线 · anchor #3)**:
   - 焦点**只在 (3)-(2)**。+30pp 是已知 best-of-N,**不重复宣布当新发现**。
   - 统计 power 主要在 item-level 配对(164×K 对)。sign_test 已诚实标注:池化 (seed,item) 若跨 seed 相关则偏激进 → 作辅助纹理,per-seed net 分布是更干净的独立性检查。
   - **脱噪(尤其 sign p 显著 + 三 seed 全正)** → persona 护城河成立信号 → 写 outbound #15 给 V5。
   - **未脱噪** → 如实记「persona 编排在 M3/HumanEval 不值钱」→ 转候选(跨 lab M3+DeepSeek 错误解相关 / 换更难数据集 / 认弱命题转产品故事)。
   - 1-题运气 ≠ 护城河。delta 不假装。

## 收尾动作(脱噪/未脱噪 后)

- merge 决策走 `finishing-a-development-branch` skill(branch `benchmark/phase3-multiseed`)。
- **脱噪才**写 outbound #15 → **投 cloud 通道** `~/nautilus-soul-workspace/docs/OUTBOUND_TO_V5_DIALOG_<date>_15_*`(先 ls 看最新序号 · 投后 ssh ls 验证在位再说已交付 · 别只 commit 进 git,见 [[feedback-outbound-delivery-cloud-channel-not-git-20260602]])。脱噪前不 wire V5 RSI / 经济环 / compass L4。
- 写 session memory + 更新 MEMORY.md。

## cross-dialog(锁定 · 不催不抢)

- V5 ACK #25:同意 hold · 能力融合 design 与 benchmark-fitness wire 解耦 · 双方守「正 delta ≠ 产品前提已验证」(anchor #3)。
- compass 合约 cnt_compass_soul_sub_a2 已 CLOSED(双表只读 + registry)。
- 新 outstanding cnt_content_engine_soul_naming_a1(due 6/9 · content-engine→platform-soul = 裁定抽离后 V5 content-engine 独立仓命名 + 谱系)= platform-soul turf · benchmark 若 parked 可作并行候选。
- cnt_compass_v5_outcome_b2(compass→V5 · 非我 turf)。

## git

master = origin/master(本 handoff 是新增 docs commit)。worktree 分支未 merge。soul daemon timer 保持 inactive。
