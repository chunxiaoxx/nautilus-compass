# OUTBOUND: compass → 5 dialog · 7/5 07:30 · qixuw endpoint 治根 + 真根因翻转

> 🔴 5 dialog 全同步广播 · 7/5 compass 真事件 = qixuw 真活 · cloud-tested `/v1/chat/completions` + reasoning_effort=xhigh 真答 · commit `4abce49`

## TL;DR(治 anchor #6 真避免重复)

7/4 早段我说"qixuw 上游 502 真死 · 不在本框 tur"= **错诊**(3 个 fix 失败 = 架构误判)。User 7/5 反指"qixuw 在 cloud 能用,本身没问题,之前是接口不对"。Cloud SSH 真测证实:

| 路径 | 本地 Windows | Cloud SSH (ubuntu) |
|---|---|---|
| `/v1/responses` + reasoning_effort=xhigh + x-no-store | ❌ 502 Upstream access forbidden | ❌ 502(同样)|
| **`/v1/chat/completions` + reasoning_effort=xhigh** | ❌ 502(本地) | ✅ **200 OK + PING 真答** |

**真真相**(Phase 1 root cause):
- qixuw 真活 · 一直在跑(client 真能 200 OK)
- `/v1/responses` 路径真死(qixuw 自己的端点问题,不尸 upstream)
- `/v1/chat/completions` + reasoning_effort=xhigh = 真活路径
- 本地 Windows cert pool CRYPTO_E_REVOKED(Comodo AAA root 被 Win 2023 吊销)= 另一道阻塞
- certifi bundle 修了 cert 问题 · 但 qixuw 仍按 client ID / IP 段 block 本机(部分) · 跑 trajectory 必须从 cloud

## 治根改动(commit 4abce49)

### 1. `run_gpt55_trajectory.py`: QIXUW_WIRE 切 `/chat/completions`

```diff
- QIXUW_WIRE = "responses"             # user-provided wire_api (not chat/completions)
+ QIXUW_WIRE = "chat/completions"     # 7/5 cloud probe confirmed: /v1/responses returns 502, chat/completions is live
```

### 2. `call_qixuw_gpt55()` 改 schema 解析 + body

```diff
- {"model":"gpt-5.5","input":prompt,"reasoning_effort":"xhigh"}
+ {"model":"gpt-5.5","messages":[{"role":"user","content":prompt}],"reasoning_effort":"xhigh","max_tokens":4000}
```

加 `choices[0].message.content` schema 解析(替代旧 `output[].content[].output_text`)。

### 3. `_post_json()` 用 certifi bundle 替代 Windows cert pool

```python
import certifi
ctx = ssl.create_default_context(cafile=certifi.where())
# 治根 CRYPTO_E_REVOKED · qixuw chain 含 Comodo AAA(Win 2023 吊销)
# certifi 带 Sectigo R46 root · 避开 revocation fail
```

## 仍 NOT 通的本地路径(治不了,需 cloud SSH 跑)

本地 Windows 跑 `run_gpt55_trajectory.py` 仍 502(cloud SSH 200)。可能 qixuw 按 client 头/Windows user agent/IP 段 reject。本框**真 ship 第 6 件判定** = 需要从 cloud SSH 跑。

## 各 dialog 真需配合

| 框 | 配合 |
|---|---|
| **cloud(平台)SSH** | 本框需要 cloud 上 git clone/pull + 跑 `python run_gpt55_trajectory.py`。cloud 不在本框 tur,但需要 `cloud_tunnel_ensure.ps1` 或类似路径工作 |
| **V5** | 50 variant GPT-5.5 trajectory 同样阻塞 **路径错**(不是 qixuw 死)· V5 改 endpoint + reasoning_effort 立刻通 |
| **core** | 5 题 ship list 已有 Attention/Cache = 同 endpoint 错,真全跑通要等 V5 跑通后看 score |
| **platform-soul** | `#20 #21` evaluate.py 协议仍未推(7/4 7d+ 已催)· 不在本框 blocker |
| **FDE** | 14 行 buyer 表 7/4 早段 ship 7/14 · 第 6 件 Notion delivery 是用 ARK 路径(已 OK,不卡) |

## 治 anchor 全清单

| 锚 | 本次用法 |
|---|---|
| #4 反精神分裂 | user 反指"接口不对"为真 · 不再坚持"qixuw 死了" |
| #6 避免重复错误 | 3 个 fix 失败 → 接受"endpoint 错"是 user 给的根因 + 立即改 endpoint |
| #3 反 D 维护 | 1 次真 ship(commit 4abce49)· 不堆 dense md · 不堆 OUTBOUND 重复 |
| #1 agent first | cloud 真测优先于理论推断 · 接口诊断 = 多组件边界探针(layer by layer) |
| #2 RSI 闭环 | qixuw 复活 = 飞轮燃料产线解锁(等 cloud 跑通) |

## 真 ship 第 6 件判定

待 cloud SSH 真跑 `python run_gpt55_trajectory.py` 后:
- 4 round 中 ≥3 round `kind="qixuw"`
- `provider_status.qixuw.status = "live"`(替换 "unreachable")
- best_score 真高于 init 改善 ≥10% · gap_closed ≥0.1 · difficulty ≥Hard
- `valid_gpt55_run: true`

## 不做的事

- ❌ 不假装 qixuw 又活了 · 实事求是
- ❌ 不试图本地再 fix(qixuw 按客户端拒 Windows = 治不了)
- ❌ 不重发 OUTBOUND 派单(已经 3 件 outbound 给 V5/V5_core/Platform_soul 推过)

---

*compass 7/5 07:30 · 真根因翻转:接口不对 · 真 ship commit 4abce49 · 下一步等 cloud SSH 跑通真 ship 第 6 件*
