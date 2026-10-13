---
name: orgfuel-ORGQ-R172-92d46c6650
description: "### R172 · 2026-10-05 10:5x-11:3x(用户拍"现在验证 v5 网关接 mini-swe-a"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R172
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R172 · 2026-10-05 10:5x-11:3x(用户拍"现在验证 v5 网关接 mini-swe-agent"→接入验证 PASS,开跑前置清零)
- **验证执行(docs/metering/L3_GATEWAY_INTEGRATION_CHECK_20261005.md)**:mini-swe-agent 2.4.6 装机($TEMP/mini_venv;坑:清华镜像无此包走官方源+socks 代理毁 pip 第 N 次复发)→ 四步全 [实测]:①网关探活✓②litellm 连接✓(两坑:config 字段名=model_kwargs 非 litellm_model_kwargs,写错静默打到真 OpenAI 401 误导;本地模型须 cost_tracking=ignore_errors)③tools 透传✓(参数名随请求 schema——mini 的 command 正确传递,adapter 仅归一化)④多轮 tool 结果回喂✓
- **协议磨合点(开跑实测项)**:mini 官方协议每轮(含完成轮)必须 tool call(submit 机制),M3 完成后倾向文本收尾(finish=stop)→ FormatError→RepeatedFormatError 退出;mini 的 format_error 喂回重试会兜,真跑表现=开跑读数不预设
- **网关缺陷发现(照实报,通报函 3269)**:v5 chat 分支**无 tools+非 stream**组合挂起(60s 零字节;stream 正常/tools 分支正常);mini 恒带 tools 不受影响;建议 v5 排查 agent.respond async 收集循环
- **B 臂接入配置定版**:model_kwargs{api_base 18001/api_key 占位/t
