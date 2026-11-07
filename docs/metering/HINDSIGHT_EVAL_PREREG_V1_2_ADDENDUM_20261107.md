# Hindsight 独立评测 · 预注册判据 V1.2 附录(2026-11-07)

> 取代 V1.1 附录 §二的车道选择(仍属**开跑前**变更——截至本附录,合成冒烟未跑、
> 任何 LongMemEval 题面 retain/recall/评分均未发出)。V1 主档与 V1.1 的其余条款不变。

## 车道变更(用户提供 · 2026-11-07)

- **subject/judge:MiniMax-M3 → qwen3.8-max**(百炼 TokenPlan 订阅车道
  `https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`,
  OpenAI 兼容;用户 11/7 直接提供 key 与双端点)。冻结 harness LLM 面实弹验证:
  subject 调用/judge 解析均通(见 run log)。
- **hindsight 服务端 retain LLM:同车道**(provider=openai + base_url 覆写;
  出厂默认模型名被覆写为 qwen3.8-max——为保持 retain/subject/judge 同厂,
  偏离 openai/gpt-4o-mini 推荐默认的记录见 V1.1 §二.1,原因更新为:
  TokenPlan 订阅零边际成本,MiniMax 按量烧钱)。
- **fallback(已验证未启用)**:MiniMax-M3 @ api.minimax.chat(V1.1 车道)。
  若 TokenPlan 限流/配额在 run 中实际卡死,切 fallback 须在 run log 记录时点与题号。

## 不变的后果声明

- 与 compass 56.6%(DeepSeek V3.2 subject)仍为**跨 subject 模型对比**,报告显式标注
- 冻结 harness prompt/judge/温度/单 vote 逐字复用不变;bank 协议与 recall 默认参数不变
- 判据仍只许更严;本附录为车道替换,不触及任何判读条款
