---
name: orgfuel-ORGD-94ed15c7e10f0501-3c9a54284e
description: "[## 1 · 任务定义(v2 修正)] - **effect 侧(果)= 样本级判定记录,不含题面原文**:按判据簇回"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-94ed15c7e10f0501
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 1 · 任务定义(v2 修正)] - **effect 侧(果)= 样本级判定记录,不含题面原文**:按判据簇回源文件逐条构造,字段全部回溯(A3),构造模板透明:
- LME-V2 四簇(d12/d14×web/ent,902 条,源 per_question.jsonl):`{question_type}|作答:{response_parsed_boxed}|金标:{answer_gold}|规则分:{score}|{拒答标记}`
- arm-a 簇(500 条,源 arm_a_rows_rejudged.json):`{question_type}|作答:{model_answer 截120}|金标:{truth}|双层复判:{is_correct}|judge:{judge_raw 截80}`
- BC1 v1/v2(36 条,源 SELFTEST_SCORECARD.md/_V2.md 审计表行,以 qid 定位):行文本截 300
- F15(8 条,源 f15_meta_judge_3prov.json):`case {id}:三门={compass_gates[id]},jev={v},glm={v},MiniMax={v}`
- T3 mini/主批(8 条):保留 v0 reason(已样本级)
- **cause 侧(因)= 判据文本展开(criteria_lib_v0,10 条)+ source_trace 尾段 + artifact_ref 原样(含 question/model_answer 样本工件)**
- 样本内容只在因侧:判据作用于具体样本,工件引用属"因";effect 不含题面原文→无同题文本双侧指纹作弊通道;信号=作答/金标/题型与题面的语义关联(数值/实体对应,非原文复制)
- 检索:effect 表征在 1454 条 c
