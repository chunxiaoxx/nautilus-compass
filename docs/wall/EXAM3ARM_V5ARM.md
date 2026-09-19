# 三臂·组织对照1 · v5臂(盲ARM-X)成绩单 · 2026-09-20(internal-audited·半自证)

判材=盲化包(平台587中继,starter+tests+diff自含);三门中门2为主判(门3=diff未触测试文件✓3/3;门1=以fix态测试反推为前提的判材设计)。臂映射密封至三臂全判毕(本批单臂,v5=ARM-X)。

| 卷 | 门2 | 定性 |
|---|---|---|
| q2 | **PASS 43 tests** | agree |
| q3 | FAIL·产出含语法错(`{"code": "ARM-C-daemon..."}` 被赋值为表达式) | disagree |
| q1 | 不可判·测试导入 `proof.l1_grouper_compat` 不在自含包内(依赖缺失≠卷坏) | not_computable |

判读:1/3 agree 与周期1早期同水位;harness十修后仍有真实语法错(q3=模型内容错,与门语义达标一致);q1不可判暴露自含包格式缺口(判材应含全部被导入依赖)——**格式条款将入judge_pack规范v2**。
辅证链勘误(v5 580):gate_traces误清空,主材料(DB output)不受影响,披露在案。
