---
spec_id: S2
suggested_owner: (我 · 不派 · 协议级风险高)
effort: 5 days
gh_issue: (not opened)
thread_id: spec-S2-proof-of-recall
status: draft · self-implement
created: 2026-05-11
---

# Goal

`compass.recall()` 返回 `recall_token` (nonce) · agent 下一次 `ingest_obs` 必须 cite 那个 nonce + 引用至少 1 条 top-3 原文片段 · daemon 验证 nonce-consumption-link · 不通过 = 标 `fake_closure: true` 写入 verification_log。

杀掉 P1-1 模式 (V5 标 completed 但下游没消费) 在协议层 · 不再靠 cron 监控补救。

# Why not派 V5

- 协议级改动 · 涉及 daemon.py · mcp_server.py · 索引 schema · 全栈
- V5 域不匹配 (营销 agent · 没必要懂 MCP 协议细节)
- 任何 bug 都阻塞所有客户端 (5 agent_type 全停)
- 派出去万一搞挂 · L4 cross-dialog 也挂 · 风险不可接受

我自己做。

# Acceptance criteria

- [ ] `compass.recall()` 返回 `{top3: [...], recall_token: "rt_xxx"}` · token 是 16-byte hex · 30 分钟过期
- [ ] `compass.ingest_obs(content, recall_token, cited_snippets)` · 新增两个可选参数
- [ ] daemon 校验: `recall_token` 在过期窗 + agent_type 匹配 + `cited_snippets` 至少含 1 段属于该 recall_token 的 top-3
- [ ] 校验通过 → 正常 ingest · verification_log entry `proof_of_recall: pass`
- [ ] 校验不通过 → 拒绝 ingest? 还是接但标 `proof_of_recall: fail, reason: ...`? **设计决策: 标但接** · 不破坏向后兼容 · 老客户端不传 token 仍正常 work · 监控分析失败率
- [ ] cron 每天扫 verification_log · `proof_of_recall: fail` 比例 > 20% → Telegram alert
- [ ] 单测覆盖: token 生成 / 过期 / 跨 agent_type 拒绝 / 片段不匹配拒绝 / 缺字段降级
- [ ] CHANGELOG v1.5 entry · semver minor bump (新增可选参 · 不 break)
- [ ] docs/PROOF_OF_RECALL.md · 描述协议 + 何时使用 + 不使用的代价

# Files touched

```
daemon.py                                         (~80 lines · recall_token 生成 + 校验)
mcp_server.py                                     (~40 lines · 转发 token · 接 cited_snippets 参)
compass_mcp_client.py                             (~30 lines · 客户端透明传 token)
tests/test_proof_of_recall.py                     (new · ~250 lines)
docs/PROOF_OF_RECALL.md                           (new · ~150 lines)
CHANGELOG.md
```

# 数据结构

```python
# daemon 端 · token store (in-memory · 30 min TTL)
recall_tokens = {
    "rt_a3f9...": {
        "issued_at": 1715456789,
        "agent_type": "v5",
        "top3_snippets": [
            {"id": "session_xx", "snippet": "..."},
            ...
        ],
    }
}

# ingest 校验逻辑
def validate_recall_proof(token, cited_snippets, agent_type):
    rec = recall_tokens.get(token)
    if not rec:
        return False, "token_not_found_or_expired"
    if rec["agent_type"] != agent_type:
        return False, "agent_type_mismatch"
    valid_snips = {s["snippet"] for s in rec["top3_snippets"]}
    cited = set(cited_snippets)
    if not (cited & valid_snips):
        return False, "no_snippet_overlap"
    return True, None
```

# 向后兼容

- 老客户端不传 `recall_token` / `cited_snippets` → ingest 正常接 · 标 `proof_of_recall: not_attempted`
- 老客户端调老 recall → 不返回 token · 与现行一致
- 新参数全是 optional · 不 break

# Migration timeline

- v1.5.0 ship: token 生成 + 校验 + 监控 · 默认不强制
- v1.6.0 (~ 4 周后): 看 fail rate · 如果 < 5% · 把 fail 改成 reject 而非接
- v2.0.0 (更后): 全强制 · 不传 token 直接拒

# 杀掉的 fake-closure 模式

```
# v1.x · P1-1 case
V5 recall("营销飞轮 thread") → top3 含 "asset_path 必须是 paper/ 不是 nautilus-compass/paper/"
V5 ignore + 直接 dispatch · 用错路径
V5 ingest_obs("完成") · 但下游 fail
[ 检测靠 monitor cron 抓 fake_closure ]

# v2.0 · 同样情况
V5 recall(...) → {top3, recall_token: "rt_abc"}
V5 ignore + 直接 dispatch · 用错路径
V5 ingest_obs("完成", recall_token="rt_abc", cited_snippets=[])
daemon → cited_snippets 空 · proof_of_recall: fail
[ 检测在协议层 · 0 延迟 · 不靠 cron ]
```

# Risk

- token store in-memory · daemon 重启丢 · 用户 ingest 时 token 失效 → fallback: 接 + 标 fail · 不报错
- 30 分钟 TTL 太短 · V7 partnership 跨小时谈判 → V7 用 `thread_recall` 拿新 token · 不是 `recall`
- agent 假 cite (复制 top3 字符串但实际没读) → 这是 best-effort 协议 · 不防恶意 · 防失误

# Out of scope (v1.5 不做)

- ❌ 不防恶意伪造 cite (用 HMAC + content hash · 留 v1.6)
- ❌ 不做 token 持久化 (留 v1.6)
- ❌ 不强制 (留 v1.6)
