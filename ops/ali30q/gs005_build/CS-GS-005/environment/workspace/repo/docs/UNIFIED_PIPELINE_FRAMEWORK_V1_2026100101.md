# 统一流水线框架 V1(UNIFIED_PIPELINE_FRAMEWORK_V1)

- 版本: V1 · 2026-10-01 修订 01
- 原则: 零新建只接线(不新建模块,仅接线既有件)
- 状态: 已接受(accepted governance improvement)

## 设计:五工位 × 五原料

### 五工位
1. 采集(ingest)
2. 检索(recall)
3. 决策(decide)
4. 执行(dispatch)
5. 回函(review/reply)

### 五原料
1. 组织函件
2. 待审 draft PR
3. 召回片段(recall snippets / proof-of-recall)
4. 组织近况
5. 静态检查反馈

## 统一件(接线目标)
- 决策Schema: 五工位共用同一份决策结构
- 任务市场: 回函型任务优先派发
- 算力池: 积压时避免产大改(积压期仅接线、不新建)

## 接线约束
- 所有改进仅通过接线统一件落地,不引入新文件、新模块。
- 决策Schema 为唯一决策出口;任务市场为唯一派发入口;算力池为唯一执行资源。