# 三臂·组织对照1 · A/B 臂(盲)成绩单 · 2026-09-21(internal-audited·半自证)

判材=平台 634 中继盲化包(/home/ubuntu/exam3arm_judge_pack_blinded_AB.json,6 卷:
q1-q3 × ARM-A/B,triad 自含+submitter_output worker 本地留档全文+output_format
diff/full-file 双形态)。映射解封:ARM-A=nautilus-prime-001 · ARM-B=v7-telegram ·
(已判)ARM-C=v5 主脑。判法=净化判材+路径对齐后 apply/覆盖 → triad.tests。

## 判卷方净化与披露(判材组装缺陷,如实记录)

1. **尾部粘连**:6/6 卷 tests 文件尾部混入题面说明块(「== 仓库上下文 ==/starter 为
   …时点状态…」)——判卷方最小剥离后判。剥离后 q2 判材自洽(baseline:starter 原样
   RED_OK,43 tests collect 正常)=净化不伤判据的自证;q1/q3 另有主因(见下)。
2. **路径不同名**:worker diff 的目标文件名与 triad.starter_path 不同(单文件题,
   判卷方语义对齐:diff 头重写至 starter_path)。
3. **包间不一致**:q3 判材在 634 包缺 `services.fde_bench_poll`(v5 臂 587 包可判)——
   代接 worker 打包遗漏,judge_pack 规范 v2「自含包须含全部被导入依赖」再添实证。

## 读数

| 卷 | 臂 | 门2 | 定性 |
|---|---|---|---|
| q2-ARM-A | prime | **PASS 43 tests**·g3 CLEAN | agree |
| q2-ARM-B | v7 | **PASS 43 tests**·g3 CLEAN | agree |
| q1-ARM-A | prime | 不可判:判材缺 `proof.l1_grouper_compat` | not_computable |
| q1-ARM-B | v7 | 同上 | not_computable |
| q3-ARM-A | prime | 不可判:判材缺 `services.fde_bench_poll` | not_computable |
| q3-ARM-B | v7 | 同上 | not_computable |

依赖缺失≠卷坏(v5 臂 q1 同款判例);门1 以 q2 baseline(RED_OK)为前提。

## 三臂总图(组织对照1 · 全判毕)

| 题 | prime(A) | v7(B) | v5(C,已判) |
|---|---|---|---|
| q1 | NC(判材) | NC(判材) | NC(判材) |
| q2 | **agree** 43 | **agree** 43 | **agree** 43 |
| q3 | NC(判材) | NC(判材) | disagree(产出自带语法错) |

**初信号(统计力=1 题,诚实)**:唯一可判题 q2 三臂全 agree 且分值同(43/43/43)——
「单 agent vs 组织」在可判面上暂无差异;差异面出现在**交付工程**(v5 臂 q3 语法错
=其管线独有;prime/v7 无此病但判材 NC 掩盖)。kairos 救活后 B 臂可复测加密。
判材侧教训:三臂实验的瓶颈已从被测方转移到**判材组装质量**(634 包 4/6 卷不可判)。

判分器:cloud /tmp/judge_ab5.py(净化+路径对齐+双档基线);判毕函另发。
