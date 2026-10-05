v5 网关缺陷通报( compass 侧 L3 接入验证顺带发现,照实报):

现象:POST /v1/chat/completions **无 tools+非 stream** 组合挂起——60s 零字节超时(curl 实测);同请求 stream=true 正常返回;带 tools 的请求(走 toolcall_adapter 分支)非 stream 正常。范围仅限 agent.respond 收集分支。

影响评估:compass L3 B 臂(mini-swe-agent)负载恒带 tools,不受影响,接入验证已 PASS(docs/metering/L3_GATEWAY_INTEGRATION_CHECK_20261005.md)。

建议排查方向:_stream/agent.respond 的 async 收集循环(Windows SelectorEventLoop 下 async generator 中断?)。坐标:nautilus_v5/api/openai_api.py chat_completions 非 tools 分支。
