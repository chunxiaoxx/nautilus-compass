---
spec_id: S3
suggested_owner: (我 · 不派 · 短平快 · 立即可做)
effort: 2 days
gh_issue: (not opened · self-implement)
thread_id: spec-S3-cross-project-recall
status: draft · self-implement next
created: 2026-05-11
---

# Goal

`compass.recall(scope="cross_project")` · 同 user 跨所有 project 索引 union · 让 nautilus 上踩过的 V5 营销飞轮坑 · 写禅心时被自动 recall · 不重蹈。

白盒做不了这个 (entity graph 不通用 · 跨项目实体冲突) · 黑盒天然可以 (BGE-m3 embedding 跨语言跨域)。

# Why short-path

- 不动协议 · 加 1 个可选参 (`scope`)
- 不破现有 (默认 `scope="project"` · 现行行为)
- 索引 union 是 SQL `UNION ALL` 一行
- 测试用例少 (3 个跨项目 query + 1 个性能不退化)

2 天搞定 · 不阻塞 · 跟 S1 dispatch 完全无关 · 我自己做。

# Acceptance criteria

- [ ] `daemon.py` recall 接受 `scope` 参数: `"project"` (default) / `"user"` (cross-project · 同 user)
- [ ] `mcp_server.py` 转发 scope
- [ ] `compass_mcp_client.py` 透传 scope
- [ ] 索引 schema: 现有索引按 (user, project) · cross_project = filter only by user
- [ ] 3 个 E2E 用例:
  1. 在 `nautilus-mvp` ingest "V5 飞轮 305 教训" · 在 `chunx` recall(scope=user, q="飞轮") · top1 命中
  2. 在 `compass-dev` ingest "drift_check v1.3 校准" · 在 `nautilus-mvp` recall(scope=project) · 不命中 (隔离正常)
  3. 在 `compass-dev` recall(scope=user, q="drift_check") · 跨项目同时命中 compass + nautilus 历史 · 按 cos 排
- [ ] 性能: scope=user 比 scope=project 慢 ≤ 30% (典型用户 < 5 个 project · 不会爆)
- [ ] CHANGELOG v1.4 entry · semver minor bump
- [ ] 单测 ≥ 80%
- [ ] PR body 跑 drift_check + cite recall top-3 (proof-of-recall 自证)

# Files touched

```
daemon.py                          (~30 lines · scope 参数 + index 选择逻辑)
mcp_server.py                      (~10 lines · 转发)
compass_mcp_client.py              (~10 lines · 客户端 method 加 scope)
tests/test_cross_project_recall.py (new · ~150 lines)
docs/CROSS_PROJECT_RECALL.md       (new · ~80 lines · use case + privacy 说明)
CHANGELOG.md
```

# Privacy 说明 (docs/CROSS_PROJECT_RECALL.md)

- scope=user 只能跨**同 user (同 token)** 的 project · 不能跨 user
- 是 opt-in · 默认 project-scoped
- 用户可禁用: `compass.config set cross_project_enabled false`
- 索引 union 在 daemon 内存中 · 不持久化 join table
- session_*.md 文件本身不动 · 仍按 project 目录组织

# Risk

- 跨项目召回噪音 · 一个 project 的术语 (e.g. "飞轮") 在另一项目无关
  · 缓解: 提示用户 scope=user 默认关闭 · 用户主动开
- 性能 · 5+ project 时索引 scan 成本上升 · 缓解: top_k 后再 union · 不 union 后再 top_k

# Out of scope (v1.4 不做)

- ❌ 跨 user (敏感 · 不做)
- ❌ Project alias / merge (用户改名 project · 索引不自动迁 · 留 v1.5)
- ❌ 细粒度权限 (project A 只允许召回到 project B · 留 v1.6)

# Test scenarios (具体可执行)

```python
# tests/test_cross_project_recall.py
def test_default_project_isolation():
    """default scope=project · 各 project 不串"""
    ingest(content="V5 fake closure", project="nautilus")
    res = recall(query="V5", project="compass-dev")
    assert "V5" not in res[0]["content"]

def test_cross_user_recall():
    """scope=user · 跨 project 召回"""
    ingest(content="V5 fake closure", project="nautilus", user="user_a")
    res = recall(query="V5", project="compass-dev", user="user_a", scope="user")
    assert "V5" in res[0]["content"]

def test_cross_user_isolation():
    """user_a 的 project 不能被 user_b 召回"""
    ingest(content="secret", project="nautilus", user="user_a")
    res = recall(query="secret", project="nautilus", user="user_b", scope="user")
    assert len(res) == 0

def test_performance_within_30pct():
    """5 project · scope=user 比 scope=project 慢 < 30%"""
    ...
```
