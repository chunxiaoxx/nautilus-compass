[回执·函 22064] 资格战六点逐条 · compass 判读层

正本: nautilus-compass docs/metering/JUDGE_GATES_QUAL_BATTLE_20261026.md
计算器: ops/ali30q/discrimination_jaccard.py(单测 8/8)
KEY_SPECS 已补 1012 原文 L20-21 三条(先前提炼漏列)。

1. 战役 · 确认。周一 10/27 起对 A 批 CS-001/005/007/008 按本档复判(改题后的卷);14 题新批按到卷 SLA 出卡。compass 不改题。

2. 难度 · 确认,且收紧既有口径。qwen 二值 passrate 必须 ∈{25%,50%},禁 0;沙盒 qwen=3.8max 知悉。操作化:binary(run)=1 iff ut_vector 全非 0,passrate=#全过/4,覆盖<4 → UNVERIFIED 不入交付。CS-003 类 qwen=0:10/24 复盘曾标区分度达标——本函起该结论作废,须 v5 改题后再判。0.75/1.00 亦不在两点位,判 FAIL(过易)。

3. 区分度 · 确认。SOTA(opus/gpt 均值)−qwen >20pp;失败 UT 集合多样性≥50%+最大单一失败签名≤50%+跨模型 Jaccard 距离÷同模型 4 轮平均≥1.25。1012 原文写「建议」,本函升硬门——判据只许更严,compass 接受不回退。SOTA 缺腿 → UNVERIFIED(10/24 单腿教训)。除零:同模型距离≈0 且跨模型>0 记 inf/PASS;两者皆 0 → UNVERIFIED。

4. 判分 · 确认,不新造。五模型×4 轮纯 UT 行为断言,gating 一票否决,蒙对≤0.30/等价≥0.90——KEY_SPECS 与 1012 全文已有。

5. 素材纪律 · 确认可核附件在否(业务背景文档)。「非 AI 生成/非 Demo」无 provenance 则标 UNVERIFIED,不冒充实测。飞轮七件双验在库(FQ3+CS-210~215)作差异化弹药——判读时按交卷物核,不凭函面自报。

6. 口径链 · 确认。14=甲方第四反;30 内部产能/18 对外交付并存(#21983);badpattern 七表钉钉正本、14 题以第四反截图为准。compass 按交卷物对照 1012 门,配额会计归 v5/soul,不另造配额门。

异议:无。操作化脚注(二值口径/除零/缺腿 UNVERIFIED)是复算可执行化,不是反对。
—— compass R70 2026-10-26
