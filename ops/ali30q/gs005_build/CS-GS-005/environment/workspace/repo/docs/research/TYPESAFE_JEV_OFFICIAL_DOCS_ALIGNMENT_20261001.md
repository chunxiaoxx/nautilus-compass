# Jev/TypeSafe 官方文档对齐报告(2026-10-01 · 用户供源 · T2/T3 混合)

> 用户提供源头:白皮书作者 Diogo Amogo(TypeSafe);官方文档 docs.typesafe.ai;GitHub:typesafe-ai/skills / yibie/jev-engineering-zh / TianyuCodings/JevHarness。建议路线=先官方 skills 再白皮书。

## 一、官方核心理念(实测读取自 docs.typesafe.ai)

1. **System One 模型**:返回类型化决策+概率(非生成文本)——"可编程常识"。Jev 是旗舰
2. **三原语**:
   - **Choice**(选择:给定答案空间选一个)
   - **Score**(打分:数值维度)
   - **Noul**(布尔判断:真假+概率)——**我们的 Schema 没有单独的 Noul,用 choice(2 档)近似了——后续可扩展**
3. **State 结构**:字符串/JSON 对象/数组三形态——**与我们 Schema 的 state 字段(五维判读上下文)对齐,我们用的是对象形态**
4. **校准**:概率对结果优化以反映不确定性——与我们 gold_probs(软目标分布)同源
5. **代码拥有工作流,模型提供语义理解**——与我们"AI 派单,代码管流程"的组织设计完全同构

## 二、与我们决策 Schema V1 的对齐检查

| 字段 | 官方 | 我们(V1) | 差异 |
|---|---|---|---|
| state | ✅对象/字符串/数组 | ✅对象(五维) | 一致 |
| questions | ✅三原语混排 | ✅choice+boolean 混排 | **缺 Score 原语**(置信度用 boolean 近似——后续可改 score 0-2) |
| gold | 概率分布 | ✅gold_probs+双 kind(annotator/deterministic) | 我们多了 kind 标注(训练数据溯源)——超出官方,合理 |
| calibration | 官方核心 | 我们的 c4 一致率双向校验 | 我们从应用层做了校准检查,方法论同源 |

**结论**:V1 对齐度高;两处可吸收:①Score 原语(置信度从 boolean 改 0-2 数值)②官方"state=给专家小组看的材料"的比喻比我们的"五维上下文"更直观——手册 V2 可借用。

## 三、对我们的三重启示

1. **我们不是在模仿 Jev,是在造自己的 Jev**:官方是"模型即服务"(API 调用);我们是"组织即引擎"(数据自产+判据自建+训练自做+部署自有)——同一方法论,两种产品形态,互补不冲突
2. **决策头 SFT 的验证标杆**:官方模型经过校准训练;我们十月第四周的决策头训练(2000 条起)可以直接对标"校准性"指标(概率与真值分布的匹配度)
3. **执行 API 的协同点**:官方三原语(Choice/Score/Noul)恰好是我们执行 API 的任务分类模型——AI 生态调用我们时用这三原语描述任务,我们分派给人类执行

## 四、坐标登记

- 官方文档:https://docs.typesafe.ai(llms.txt 索引可用;state/system-one/primitives 三页已读)
- 官方 skills:~/Projects/typesafe-skills(Claude Code 插件可装:`claude plugin install typesafe@typesafe-ai`)
- 社区翻译:yibie/jev-engineering-zh(白皮书中英对照)
- 社区 harness:TianyuCodings/JevHarness
- 我们已有:NanoJev 本地仓(~/Projects/NanoJev)+ awesome-jev fork
