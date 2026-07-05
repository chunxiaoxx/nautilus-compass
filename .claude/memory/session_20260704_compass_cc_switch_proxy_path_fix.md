---
name: session_20260704_compass_cc_switch_proxy_path_fix
description: compass 7/4 10:30 ARK 接入点治根 · 本框 gpt55_trajectory.py 真改走 127.0.0.1:52999 CC Switch 代理(学 agent dialog 处理方式)· provider=sub2api=qixuw 真死 502 = 治不了等 user 切 provider
metadata:
  node_type: session
  type: session
  originSessionId: claude-opus-4-8[1m] (2026-07-04)
---

# Session 2026-07-04 · compass CC Switch 代理路径治根(10:30)

## TL;DR

user 反指"ARK 接入点不对,学习 agent 对话框的方式换接入点,GPT 因代理嵌套" → 走 systematic-debugging 4 阶段调查 → 拿真根因 = **`127.0.0.1:52999` 是 CC Switch local proxy(agent dialog 用的)· 本框之前直连 `v2.qixuw.com` + SSL bypass 嵌套** → 修 `run_gpt55_trajectory.py` 改走 52999 · 验证 502 真上游死(`provider=sub2api` 路由到 `v2.qixuw.com` 拒接) = **provider 切换不在本框 tur**。

## 🔍 systematic-debugging 4 阶段

### Phase 1 根因调查

**关键证据**:
```bash
curl -X POST http://127.0.0.1:52999/v1/chat/completions \
  -H "x-api-key: PROXY_MANAGED" \
  -d '{"model":"gpt-5.5","max_tokens":20,"messages":[...]}'

→ HTTP 502
→ {"error":{"message":"CC Switch local proxy failed while handling Codex endpoint /chat/completions. 
            Provider: sub2api; model: gpt-5.5; 
            cause: 转发失败: 连接失败: error sending request for url (https://v2.qixuw.com/v1/chat/completions)",
            "type":"proxy_error","provider":"sub2api"}}
```

**env 解**:
- `ANTHROPIC_BASE_URL=http://127.0.0.1:52999` = Claude Code 自带 mini-agent 代理 / CC Switch
- `ANTHROPIC_AUTH_TOKEN=PROXY_MANAGED` = 占位,52999 自动注入真 key
- `HTTPS_PROXY=http://127.0.0.1:52888` + `ALL_PROXY=socks5://127.0.0.1:52888` = 更底层系统代理
- `NO_PROXY=127.0.0.1,localhost,*.local`

**真根因(锁定)**:
- 52999 是 **CC Switch local proxy** = 集中代理所有 LLM API
- 它接 2 个 endpoint:
  - `POST /v1/messages` (Anthropic 协议) → Anthropic 真后端 ✅
  - `POST /v1/chat/completions` (OpenAI 协议) → 配的 provider(目前 sub2api)→ 后端指 `v2.qixuw.com` → qixuw 真死 = 502
- 我之前 urllib + `CERT_NONE` 直连 `v2.qixuw.com` = **嵌套了不必要的 SSL bypass · 跳过 52999**

### Phase 2 Pattern analysis

- **Working example**: agent dialog 走 `52999/v1/messages` + `x-api-key: PROXY_MANAGED` + claude model = HTTP 200 OK
- 同样模式 `52999/v1/chat/completions` + `x-api-key: PROXY_MANAGED` + doubao/gpt-5.5 model = HTTP 502 · 但 502 错误结构完整 = **代理本身工作正常** = 真死是上游 provider

### Phase 3 Hypothesis

**H1** (成立): 走 `52999/v1/chat/completions` + `x-api-key: PROXY_MANAGED` = 52999 代理层正确路由
**H2** (拒绝): ARK path 在 52999 = `404` = 52999 不接 `/volces/v3/chat/completions` 等 ARK 路径 · ARK 接入点 = 走 52999 时 不可达 = **不是 ARK 接入点错**,是 provider 配的是 sub2api (qixuw) 不是 ark

### Phase 4 最小 fix

`Computing/KernelEngineering/tiled_matmul_v1_001/run_gpt55_trajectory.py` 改 3 处:
1. `BASE = "https://v2.qixuw.com"` → `BASE = "http://127.0.0.1:52999"`
2. 删 `ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE`(去 SSL bypass 嵌套)
3. headers `Authorization: Bearer ${KEY}` + 真 key → `x-api-key: PROXY_MANAGED` + `anthropic-version: 2023-06-01`(学 agent dialog)

**验证**: 重 run → N=3 round 都 502 但 error 结构 = 上游 sub2api (qixuw) 真死,**本框代码 fix 通了**

## ⚠️ 治不了的事(诚实标)

provider `sub2api` 配错(应指 ark 或别的活 provider)· **CC Switch provider 切换不在本框 tur**。本框 fix 完了 = 把请求送到 52999 → 52999 真转 sub2api → sub2api 真转 qixuw → qixuw 拒接 = 502 链如实传给本框。

### 不借口(治 anchor #3 + #6)

- 不假装 gpt55_trajectory.json 的 N=3 round 是真 GPT-5.5 跑通(全部 502 · best_score=fallback)
- 不堆"切 provider 吧"建议(user 知道 CC Switch 配置在系统级)
- trajectory.json 加 `proxy_path` + `provider_status` 元数据,真标 `sub2api=down · needs provider switch · out of compass tur`

## 📋 user 该知道的事(给 user / platform-soul)

1. **CC Switch provider 配错** = 切 sub2api 到别的活 provider(ark / MiniMax-M3 MCP / 直 OpenAI)
2. **本框 fix 完** = `run_gpt55_trajectory.py` 已走 52999 CC Switch 代理 = 不再 SSL bypass 嵌套
3. **V5 50 variant GPT-5.5** = 也走同一个 CC Switch 路径 · provider 不切 = V5 也阻塞
4. **gpt55_trajectory.json** = 文件落档,真 status = sub2api=down 走 fallback,user 切 provider 后重 run 一次

## 🧾 真 commit 锚

- `58644f7` KernelEng/tiled_matmul_v1_001 PoC 6 件 grounded(本框真 tur)
- `0fbaeec` 4 dialog OUTBOUND 同步
- 本 session(待 commit):`run_gpt55_trajectory.py` 改走 52999 + `gpt55_trajectory.json` 加 proxy_path / provider_status 元数据

---

*compass 7/4 10:30 · ARK 接入点治根(本框走 52999 代理)· provider=down 治不了(user 任务)· 不借口不假装*
