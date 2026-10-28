# LLM 通道状态 · 2026-09-04 实测(digest_human 排障副产品;文件名避 gitignore *_STATUS* 规则)

> 用 LLM 前先看此页。实测方法:逐通道裸调 chat 端点看真实返回(401/400),非自报。
> 处置原则:env 行**不删不注释**(消费者在低频路径,抠行有启动校验风险;换 key 即活)。

| 通道 | 状态(9/4) | 实测证据 | 消费者(平台仓) | 恢复路径 |
|---|---|---|---|---|
| **api.chunxiao.wang(自有中转·newapi·HR 框维护)** | ✅ **已接入(平台主通道)** | platform-ops token 实调 glm-5.3-flash 200,digest 已切换 | digest_human.py 首选(云 .env CHUNXIAO_*) | — |
| ↳ 站内上游:zhipu-glm / kimi-coding-plan / minimax-coding-plan / glm-ma-relay | ✅ 四条活 | newapi channels 表 status=1 | 由 HR 框维护 | — |
| **minimaxi anthropic**(`CLAUDE_BASE_URL`+`MINIMAX_CODING_KEY`,MiniMax-M3) | ✅ 活(digest 兜底层) | say ok → OK | v5 主脑现役;digest_human.py 兜底 | — |
| Anthropic 官方(`ANTHROPIC_API_KEY`) | ⚠️ key 有效但**欠费** | 400 credit balance too low | 散点 | 充值即活 |
| DeepSeek(`DEEPSEEK_API_KEY`/`_BASE_URL`/`_MODEL`) | ❌ key 失效 | 401 invalid api key | g2_b1 两工具(手动跑) | 换 key |
| qixuw 中转(`CLAUDE_PROXY_API_KEY`+`CLAUDE_PROXY_BASE_URL`) | ❌ key 被禁用 | 401 API_KEY_DISABLED | proposal_intelligence/agent_executor(proposals 线零流量) | 换 key/弃 |
| Gemini(`GEMINI_API_KEY`) | ❌ 占位符 | 400 invalid key(值=REMOVED) | 11 文件(gemini_cache/batch、deep_research、kairos_daemon 等,均休眠或已换通道;kairos 现役=MiniMax) | 换 key |

v5 仓 `.env.systemd` 另有遗留 DEEPSEEK_API_KEY(v5 现役已切 minimax)——v5 框资产,平台不代改。

## 判活配方(复用)

```
ssh cloud "cd .../phase3/backend && python3 -c '<裸调该通道 /v1/messages 或 chat/completions>'"
```
换 key/充值后请更新此表(此文件随平台仓 commit,部署 scp 到云端 ops/)。
