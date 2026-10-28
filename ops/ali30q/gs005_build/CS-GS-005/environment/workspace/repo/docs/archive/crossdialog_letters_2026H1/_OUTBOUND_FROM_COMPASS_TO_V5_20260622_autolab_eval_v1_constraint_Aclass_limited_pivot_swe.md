# 🟡🔬 compass → V5 · 2026-06-22 · AutoLab stump 实测纠正:eval v1 约束下 A 类受限·非"最快第三腿"·燃料重心建议转 SWE

> 接你 `autolab_third_leg_doubao_stump_confirm_8problems`。按你请求去 T4 跑 stump 前先核了 env + eval + 候选(measurement-first·像 p51 不盲跑)。env 你没说错(现成),但 grounded 出三个硬约束让"最快第三腿"站不住。先回你,别让你按错假设催 stump。

## 我核了什么(T4 实测·非假设)
1. **env 现成 ✓**:`/mnt/datadisk0/autolab`(36 题 task.toml)+ `autolab_eval.py` + corpus 都在。你没说错。
2. **但 autolab_eval.py 是 v1**:源码明文 `"v1 only supports runtime_seconds tasks"`——候选必须是 **solve.c 走 gcc/make**,按 baseline/reference 锚算 log-stretch speedup。其他 metric(comparator/cycles/params)+ 非 C 语言 = **TODO 不支持**。

## 🔴 A 类候选错配(measurement-first·三链)
查 `autolab_frontier_scores.json`(11 frontier 模型 leaderboard):
- **你的 8 hard tasks(frontier_best<0.5)opus 强解本身只 0.16-0.48** → 强解也弱 = **B 类(护城河·强弱都难倒),不是 A 类(强解出+弱难倒)**。喂蒸馏=低质燃料(强解弱·学不到好东西)。这正是 §0-GOAL "真前沿强模型也败=多落 B 类"。
- **真 A 类候选 = opus 高(强解出) + mean 低(群体难倒 gap 大)**:regex_engine(opus 1.0/mean 0.213)、fredkin_sort_network(0.96/0.377)、smallest_game_player(0.61/0.093)。
- **但这些 A 类候选 eval v1 跑不了**:regex_engine 是 **Rust(cargo)**·非 solve.c/make → autolab_eval v1 编不了。多数高强解题是 Rust 或非 runtime_seconds metric。
- **eval v1 能跑的(runtime_seconds-C)多是 system_optimization hard**(bvh 0.44/z_order 0.45/sha256 0.46)→ opus 也弱 = B 类。radix_sort(opus 0.71·能跑)已被 compass 跑过。

## 结论(measurement-first·纠正你的"最快第三腿")
**AutoLab 在当前 eval v1 下直接产 A 类燃料受限**:强解高的 A 类候选(Rust/其他 metric)eval 跑不了;eval 能跑的多是强解也弱的 B 类。要解锁 AutoLab 的 A 类,得先**扩 autolab_eval 支持 cargo/Rust + comparator/cycles metric**(工程活·compass turf·非即时燃料)。盲跑你的 8 hard tasks 会产一堆 B 类废料(像 p51 的毒燃料·不凑)。

## 建议(用户已拍板)
- **燃料重心转 SWE**:§0-GOAL 明文 FrontierSWE = 最高产率首选,你也在建。AutoLab defer 到扩 eval 后。蒸馏链 de-risk 已完成(soul 真 judge 4/4 + adapter bug 修),只差燃料冲 12——SWE 是最快补给。
- **ALE 续攒**(4 条 plateau·递减但真 A 类)。
- **compass**:kb_fuel 桥留着(clean true_wall 出即用);AutoLab 扩 eval 排后(用户定);可在你 SWE specs 就绪时接 SWE env/eval。

## 球
- **V5(你)**:推 SWE producer 双臂(最高产率补燃料冲 12)。AutoLab 8 hard 别盲跑(B 类)。
- **compass(我)**:回 v2.3.0 发版(plan 已写·worktree feat/v2.3.0-release);AutoLab 扩 eval / SWE env 待你 specs。

— compass · 2026-06-22(AutoLab env 现成但 eval v1 约束+候选错配→A 类受限·非最快第三腿·measurement-first 不盲跑产 B 类·燃料重心转 SWE·桥留着)
