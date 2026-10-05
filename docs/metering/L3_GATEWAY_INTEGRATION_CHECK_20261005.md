# L3 开跑前置 · v5 网关×mini-swe-agent 接入验证(2026-10-05,R172)

> 结论:**接入验证 PASS**(接口层四项全通),一处协议磨合点如实记(开跑实测项),一处网关缺陷发现(不阻塞 B 臂)。
> 环境:mini-swe-agent==2.4.6($TEMP/mini_venv,PyPI 官方源;pypi 清华镜像无此包)×v5 网关 127.0.0.1:18001(nautilus-v5 `_run_v5_api_18001.py`,PID 27224)。

## 实测四步(全 [实测])

1. **网关探活**:GET /v1/models 秒回(model=nautilus-v5)✓
2. **litellm 连接**:LitellmModel(model_name="openai/nautilus-v5", model_kwargs={api_base, api_key, temperature:0}, cost_tracking="ignore_errors")→请求到网关并返回 ✓
   - 两个接入坑如实记:①参数名是 `model_kwargs`(config 字段),不是 litellm_model_kwargs——写错时 litellm 静默打到真 api.openai.com(401 误导性报错);②本地模型不在 litellm 价目表,须 cost_tracking="ignore_errors"
3. **tools 调用透传**:网关 toolcall_adapter 分支——mini 真 BASH_TOOL(参数名 `command`)下发,模型按请求 schema 正确回 `{"command": "ls -la"}`,finish=tool_calls ✓(参数名跟随请求 schema,非硬编码;adapter 仅做结构归一化)
4. **多轮 tool 结果回喂**:R1 工具调用→tool role 观测回喂→R2 正常消费结果并 finish ✓

## 协议磨合点(开跑实测项,非接口断)

mini DefaultAgent 官方 system_template 协议=每轮(含完成轮)必须发工具调用(submit 机制),实测 M3 完成任务后倾向直接文本收尾(finish=stop 无 tool_calls)→ mini parse 抛 FormatError → 连续多次后 RepeatedFormatError 退出。mini 的 format_error 喂回重试机制会兜(错误提示回给模型),真跑 SWE-bench 的通过表现=开跑读数,接入验证不预设。

## 网关缺陷发现(照实报,不阻塞 B 臂)

**v5 主脑 chat 分支(agent.respond,非 tools 请求)非 stream 挂起**:curl POST /v1/chat/completions 无 tools+非 stream→60s 零字节超时;stream 模式正常(PONG);tools 在场走 toolcall_adapter 分支非 stream 正常。范围仅限"无 tools+非 stream"组合,mini 负载恒带 tools 不受影响。建议 v5 侧排查 agent.respond 收集循环(待通报)。

## B 臂接入配置定版(入 L3 档坐标)

```yaml
model_name: openai/nautilus-v5
model_kwargs:
  api_base: http://127.0.0.1:18001/v1
  api_key: <local-18001>(网关无鉴权,占位)
  temperature: 0
cost_tracking: ignore_errors
```
mini-swe-agent 版本钉 2.4.6(release tag a83fcae82d2a);Windows 本地跑批=LocalEnvironment(Git Bash),SWE-bench 标准做法为 Linux 容器——若跑批遇环境不兼容,备选=docker 环境(environments/docker.py,不改变 harness 本体)。
