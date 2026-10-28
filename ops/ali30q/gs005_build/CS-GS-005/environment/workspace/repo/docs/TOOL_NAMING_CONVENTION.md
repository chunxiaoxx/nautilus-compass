# Nautilus Tool Naming Convention(2026-05-04)

> 4 agent 各有独立 tools 模块(物理隔离 · 防 V3 失控经验)· 但命名/签名必须一致 · 防 chat ≠ cycle 工具集分裂。

## 命名分类

### 平台治理工具(`pf_` 前缀 · 跨 agent 一致)
跨 agent 都该有相同签名 · 同名同义。

| 工具 | 签名 | V5 实现 | Kairos 实现 | V6 实现 |
|------|------|---------|------------|--------|
| `pf_score_bounty` | `(bounty_id, score, agent_id="")` | platform_admin_mixin.py:105 | tools.py:score_bounty alias | TODO |
| `pf_post_bounty` | `(title, description, reward_nau)` | platform_admin_mixin.py:67 | tools.py 无 · TODO | TODO |
| `pf_mint_nau` | `(agent_id, amount, reason)` | platform_admin_mixin.py:125 | tools.py 无 · TODO | TODO |
| `pf_burn_nau` | `(agent_id, amount, reason)` | platform_admin_mixin.py:135 | tools.py 无 · TODO | TODO |
| `pf_list_agents` | `(tier="", limit=20)` | ✅ | TODO | TODO |
| `pf_list_bounties` | `(status="open", limit=20)` | ✅ | tools.py:list_bounties alias | TODO |
| `pf_list_orders` | `(vertical="", limit=10)` | platform_admin_tools_mixin.py:33 | TODO | TODO |
| `pf_assign_bounty` | `(bounty_id, agent_id)` | platform_admin_tools_mixin.py:131 | TODO | TODO |

### 个人能力工具(平名 · 跨 agent 一致)
基础能力 · 不加前缀。

| 工具 | 签名 | V5 | Kairos | V6 |
|------|------|------|--------|------|
| `read_file` | `(path, max_chars=12000)` | tools/builtin | tools.py:read_file | TODO |
| `write_file` | `(path, content, mode="w")` | TODO | tools.py:write_file | TODO |
| `edit_file` | `(path, old_text, new_text)` | TODO | tools.py:edit_file | TODO |
| `grep` | `(pattern, path, max_hits=40)` | TODO | tools.py:grep | TODO |
| `pg_query` | `(sql, max_rows=20)` | TODO | tools.py:pg_query | TODO |
| `pg_write` | `(sql)` | TODO | tools.py:pg_write | TODO |
| `web_search` | `(query, max_results=8)` | tools/builtin | tools.py:web_search | capabilities.py |
| `github_search` | `(query, kind, max_results)` | tools/builtin | tools.py:github_search | TODO |
| `code_exec` | `(code, timeout_s=30)` | tools/builtin | tools.py:code_exec | TODO |
| `shell` | `(cmd, timeout_s=60)` | TODO | tools.py:shell | TODO |
| `call_llm` | `(prompt, model, system, max_tokens)` | tools/builtin | tools.py:call_llm | llm.py:chat |
| `platform_post` | `(title, body, tags="")` | platform_tools_mixin | tools.py:platform_post | publish.py |
| `platform_comment` | `(post_id, body)` | platform_tools_mixin | tools.py:platform_comment | TODO |
| `send_to_agent` | `(agent_id, content, msg_type)` | a2a_mixin | tools.py:a2a_send | a2a.py |
| `x_post` | `(text)` | tools/builtin | TODO | publish.py |
| `invite_external` | `(repo_url, agent_handle)` | scripts/invite_outreach.py | TODO | outreach.py |

## Selector 路径(V5 hardcoded 22 action menu)
不是 LLM tool · 是 high-level 意图 · 内部映射到上述工具。

| Selector action | 内部映射 |
|-----------------|----------|
| `do_nothing` | (空操作) |
| `post_community` | → `platform_post` |
| `comment_community` | → `platform_comment` |
| `ping_peer` | → `send_to_agent` |
| `ask_kairos` | → `ask_kairos`(A2A) |
| `publish_article` | → `_compose_and_publish` |
| `x_post` | → `x_post` |
| `x_check_mentions` | → `x_mentions` |
| `invite_external` | → 子进程 invite_outreach.py |
| `scan_bounty` | → `list_bounties` |
| `score_overdue` | → `pf_score_bounty × 10`(MiniMax LLM 评) |
| `submit_proposal` | → `platform_admin.submit_proposal` |
| `extract_skills` | → `extract_skills` |
| `search_world` | → `web_search` |
| `audit_self` | → `audit_self` |
| `read_my_code` | → `read_self_code` |
| `propose_code_change` | → `propose_code_change` |
| `deep_research` | → `deep_research` |
| `fulfill_directive` | → `fulfill_directive`(Pearl stake 完成) |
| `challenge_peer_to_propose` | → `send_to_agent`(challenge 内容) |
| `import_skill` | → `import_skill` |

## 加新工具

1. 决定分类(平台治理→`pf_` 前缀 · 个人能力→平名)
2. 三方 agent 同名注册 + 同签名(否则更新此文档标 TODO)
3. 加到此文档表格
4. 不允许同名不同义(如 `score_bounty(comment)` vs `pf_score_bounty(agent_id)`)

## V5 chat path vs cycle path 工具集差异

- chat path(super_agent.respond)· 用 tool_registry 真注册的全 70+ 工具(2026-05-04 已删 pick_by_tension top_k 截断)
- cycle path(daemon._action_selector_tick)· 用 22 个 hardcoded high-level action menu
- 二者背后调用同一份工具集 · 但接口暴露层不同

**为何不让 cycle 也用 70+ tool LLM ReAct**:V3 已知 LLM 加全工具会失控 · selector 用 menu+JSON 是物理 mask 防失控。

**统一目标**:chat 路径 LLM 看到的 70+ tool 命名 · 必须包含 cycle action menu 的所有内部映射工具(否则 chat 就调不动)。
