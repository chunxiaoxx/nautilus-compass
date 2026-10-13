---
name: orgfuel-ORGG-1a9a1a77b452ad20-8f778e9b96
description: "判读档判例 2026-09-09-rsi-trial1-preregistered · 三件套范围(实现契约) ## 三"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-1a9a1a77b452ad20
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-09-rsi-trial1-preregistered · 三件套范围(实现契约)
## 三件套范围(实现契约)

1. **fact_status 写入门**:daemon `parse_memory_file` 读出+recall 结果带出+hook 渲染标注;
   session_writer 蒸馏输出必带;人工写入走纪律(frontmatter 模板)。**只标注不过滤**
   (过滤策略 Phase 2 与置信度分层一起定,本环不引入自动丢弃)。
2. **查重触发合并**:daemon 新 action `dedup_check`(BGE 对全项目条目,≥0.9 merge /
   0.75-0.9 gray / 其余 unique);session_writer 写入前调用,merge 时升级原条目不新建;
   人工写入纪律=写前调用。**本环 daemon 不自动改写任何 memory 文件**。
3. **沿链一跳**:recall 组装后对 top 条目 body 的 `[[name]]` 引用展开一层(不递归,
   cap 5,`chain_extra` 单独字段+`via` 标注,不混入 recall 主列表打分)。
