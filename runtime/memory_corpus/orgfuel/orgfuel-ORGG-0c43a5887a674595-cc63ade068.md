---
name: orgfuel-ORGG-0c43a5887a674595-cc63ade068
description: "判读档判例 INFISTAR_GATEWAY_METERING_PLAN_20260930 · 二、Probe 集(五类"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-0c43a5887a674595
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 INFISTAR_GATEWAY_METERING_PLAN_20260930 · 二、Probe 集(五类,每模型每轮)
## 二、Probe 集(五类,每模型每轮)

1. **身份指纹**(10 题/模型):该模型独有训练截止知识、风格特征、拒绝模式、自我身份报告。示例:`你的训练数据截止到什么时候?请给出一件 2025 年 Q2 的行业新闻`+模型特有行为题。**判定:任一指纹与官方对照腿矛盾=红旗单列,不计均化**。
2. **能力锚**(10 题/模型):固定难度梯度(数学/代码/指令跟随),测输出质量漂移(同题 30 天 90 次采样的一致性)。
3. **长上下文**(3 题/模型):~100k token 注入,尾置关键信息提问,验证无截断(收长窗的钱给短窗=行业通病)。
4. **结构化输出**(5 题/模型):JSON schema 遵从率(F15 Choice 三态同款格式)。
5. **延迟/可用性**:以上全部请求记录 latency、http_code、SSE 断流。
