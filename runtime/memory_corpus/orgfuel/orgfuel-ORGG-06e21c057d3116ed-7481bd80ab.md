---
name: orgfuel-ORGG-06e21c057d3116ed-7481bd80ab
description: "判读档判例 L3_GATEWAY_INTEGRATION_CHECK_20261005 · 实测四步(全 [实测]) #"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-06e21c057d3116ed
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 L3_GATEWAY_INTEGRATION_CHECK_20261005 · 实测四步(全 [实测])
## 实测四步(全 [实测])

1. **网关探活**:GET /v1/models 秒回(model=nautilus-v5)✓
2. **litellm 连接**:LitellmModel(model_name="openai/nautilus-v5", model_kwargs={api_base, api_key, temperature:0}, cost_tracking="ignore_errors")→请求到网关并返回 ✓
   - 两个接入坑如实记:①参数名是 `model_kwargs`(config 字段),不是 litellm_model_kwargs——写错时 litellm 静默打到真 api.openai.com(401 误导性报错);②本地模型不在 litellm 价目表,须 cost_tracking="ignore_errors"
3. **tools 调用透传**:网关 toolcall_adapter 分支——mini 真 BASH_TOOL(参数名 `command`)下发,模型按请求 schema 正确回 `{"command": "ls -la"}`,finish=tool_calls ✓(参数名跟随请求 schema,非硬编码;adapter 仅做结构归一化)
4. **多轮 tool 结果回喂**:R1 工具调用→tool role 观测回喂→R2 正常消费结果并 finish ✓
