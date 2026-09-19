# Assay 重考成绩单 · 改进周期1 · 终版 2026-09-19(internal-audited · 半自证)

> 终版更新:37a1 补交卷(148min 长跑过同源门,平台中继 475 刷新包 faa6fbf)判毕——
> **16 tests PASS → NC 改判 agree**。趋势线:**1/5 → 3/5**。

被测:v5 框系统 | 判分:三门纯脚本零裁量(同首考判分器,判卷只认 judge_pack_v2 时间戳)

## 总读数(终版):agree 3 / disagree 2 / not_computable 0(首考 1/5 → 重考终版 3/5,坏卷上交 0)

| 题 | 首考 | 重考 | 重考读数 |
|---|---|---|---|
| g2b1:914b39c7bdea(core) | agree | **agree(沿用)** | 首考 72 passed,不重考 |
| g2b1:0c2c60c7a115(compass) | disagree | **agree** ↑ | g3 CLEAN · g2 **PASS 13 tests**(首考 corrupt patch→修复) |
| g2b1:37a117f093ec(core) | disagree | **agree** ↑↑ | 初报诚实弃考(NC);补交卷 148min 长跑过同源门,**16 tests PASS**——改判 agree |
| g2b1:355a214f29d4(v5) | disagree | disagree | g2 FAIL:SyntaxError unmatched ')'(剥除残迹新形态——**所交 diff 与其自称的 py_compile 门不同源**) |
| g2b1:a3795c2f8ea9(v5) | disagree | disagree | g2 FAIL:IndentationError line 1(同上类) |

## 改进周期判读(这张成绩单的意义)

1. 分数 1/5→2/5;更重要的是**行为改善**:首考交 4 坏卷,重考 0 坏卷+1 诚实弃考;
2. **结构性发现**:两道 v5 仓题(fde_consumer.py 目标)两轮皆坏且形态仍为剥除残迹,
   而其生产端自称双门(py_compile)已拦——**门验的字节与交卷的字节不同源**,
   修复方向:门必须对"将寄出的 diff 应用后的最终文件"编译,而非中间产物;
3. 跨仓对照:compass 仓题(corrupt→PASS)与 core 仓题修复管线有效,v5 仓装配路径
   独坏——问题在 v5 仓装配环节,不在模型解题能力(0c2c 13 全过为证)。

## 披露(同首考三句+seed 同首考承诺,判分材料=judge_pack_v2(平台中继451))

## 周期2·趋势线第四点·355a(2026-09-20 04:0x):disagree(接近)

函数级两段式管线首跑(git 全文重写 0/60 → 函数级两轮过同源门,管线判据④>0 达成)。
三门:g3 CLEAN(diff 未触测试✓);g2 **FAIL 4/5 通过,1 挂**——`test_codefix_llm_budget_defaults`
断言 `mt==32000`,重产出设 8000(首考 8000→32000 是修复主题本身,周期2 重产出又回到 8000
=**回归修复点**,非语法错非装配错)。函数级管线成立(2/3 测试过+diff 可应用),
但**该题修复点回退**。a379 在跑,出卷即判;若同管线但保住修复点,管线判定不变,
仅 355a 本题记回归。趋势线第四点=2.5/5(37a1 不变)。
