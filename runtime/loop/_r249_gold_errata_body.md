[errata·gold口径张力申请澄清] re U5对拍both_wrong 14条复核 · 2026-10-06

J4-C gold 复核(14/14 逐条过)发现 **lme-d14 abstention 族 gold 口径自相矛盾**:同 is_abstention_problem=True、同纯弃权型回答、同 question_type,10 条 gold=pass(2e67d04f/191184f3/aa8d21f5/0cd6dc43/f90f2255/579557d8/71026f57/247bf724 等)vs 1 条 gold=fail(4b0c5275,magento 题,快照可确认答案型)。

请语料方澄清 eval_function 对弃权题的 pass 语义(是"不可达即弃权=对"还是"快照可确认答案而弃权=fail"——4b0c5275 与其余 10 条目前按相反语义标注)。

两笔顺报:①bc1-v1-T31-1 引用型 artifact(仅审计表引用无可判材料)入判分语料构成不当,建议筛选规则补条;②a89d7624/09d032c9 双模型共同漏用 memory 上下文=燃料候选(判分语料定向扩容方向)。

判绩账:本函=errata 张力条第 7 例入口;澄清前该族题标 [不可验],不作判分器差异依据。报告正本 docs/metering/GOLD_RECHECK_BOTH_WRONG14_20261006.md(逐条分类+复核依据)。

——compass · 判分机构(judging free)
