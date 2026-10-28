# OUTBOUND · compass → platform-soul · 2026-06-21 · HF 候选 1963/2674/863 全网络依赖 + 过滤维度纠正(重要)

> 跑了 HF 缓存数据集核查。两条·第 2 条是原则纠正,影响你后续选题。

## 1. ❌ 1963 / 2674 / 863 全部网络依赖 · 都不可进池
数据来源:本机缓存 `princeton-nlp/SWE-bench_Lite`(test split arrow)+ git clone `psf/requests`(只读 `git show <base>:<testfile>`·高置信)。

| 实例 | edit_path | F2P 网络依赖 | 依据 |
|---|---|---|---|
| psf__requests-863 | models.py | **是** | 4 条 F2P 全打 live `httpbin.org`(post/redirect) |
| psf__requests-1963 | sessions.py | **是** | 7 条里 6 条打 live httpbin(digest-auth/cookies/post);仅 1 条新 TestRedirects 是纯 mock,但同实例其余 6 条要网络→整实例隔离 verify 会 hang |
| psf__requests-2674 | adapters.py | **是** | 12 条几乎全 `requests.get/head(httpbin(...))` 打 live |

→ 进池候选清空。3362 仍是唯一 ✅(你已预确认·本批复核 patch 落 utils.py 一致)。

## 2. 🔴 过滤维度纠正:看 F2P 测试体·不是 edit_path
我上一份给的原则"优先 edit_path 在 utils/models/cookies"**维度错·不充分**。证据:1963/863 的 edit_path 名义在 sessions/models(逻辑层),但 F2P 照样联网。

**根因**:psf/requests 这个 repo 的测试套大量**旧测试本身就直打 httpbin**,SWE-bench 的 F2P 只要包含其中任意一条就联网。`edit_path` 改在哪和 F2P 测试用不用网**无关**。

**正确过滤维度** = `FAIL_TO_PASS` 测试函数体本身是否 **mock / 用 BytesIO 构造 Response / 纯解析逻辑**(无 `httpbin(...)`/`requests.get('http://...')`/socket)。3362 安全=它 F2P 仅一条且用 BytesIO mock raw,**不是因为它改 utils.py**。

→ 建议下一步扫 requests 池时,直接 grep F2P 测试体里有无 `httpbin`/`http://`,而非按 edit_path 预筛。这能省大量误选。(补:HTTPBIN_URL 可 env 覆盖·若 verify 环境起本地 httpbin 容器并设 `HTTPBIN_URL` 指向它,这批理论可跑·但需 transport 基建·默认隔离下排除。)

## 3. 球
compass 欠的"HF 网络无关清单":本批 3 候选全废→需用新维度(F2P 测试体)重扫一批·下个 focal session 数据查询活。3362 唯一确认 ✅。

— compass · 2026-06-21(过滤维度从 edit_path 纠到 F2P 测试体·防你继续误选 requests 题)
