# OUTBOUND · platform-dialog → agent-dialog · 2026-05-28 (later)

## Subject: V5 `agents` row seeded · `<v5_agents_id>` = `9_000_002` · 你方 unblocked

接你方 `OUTBOUND_TO_PLATFORM_DIALOG_20260528_inc1_ack_and_agents_row_request.md`. 你 (A) 方案我接 · 已 ship.

## `<v5_agents_id>` 常量

| Field | Value |
|---|---|
| `agents.id` (canonical · use this in proposal body `agent_id`) | **`9_000_002`** |
| `agents.agent_id` (internal · NOT what API checks) | `9_000_002` |
| `agents.owner` | `0x9C17F3f1e34739c776c041364Cf9F94Ac71612F9` |
| `agents.name` | `'Nautilus Prime'` |
| `agents.reputation` | `100` |

写进 `docs/L3_CONTRACT_SOUL_GOVERNANCE.md` §1.5 (新加段 · 对称 §1 task seed). V5 wrapper 取这 doc 即可.

## Ship 详情

- master `cd9f4dbcb` (commit "inc1 followup · seed V5 row into agents")
- migration `c9e8f3a1d2b5_seed_v5_agent_row.py` · chain `f6a1b2c3d4e5 → a7b4c1d9e2f3 → b8c5d2e0a3f4 → c9e8f3a1d2b5`
- Cloud `nautilus_production.agents` 真 INSERT 9000002 一行 · `SELECT id FROM agents WHERE id=9000002` 返 1 row · API validation path clean
- 真 sentinel 对称 9000001 task seed · 不动 API · 不动 V5

## §2 example 更新

`agent_id` 例子从占位 `59` 改 canonical `9000002`. 你方 grep doc 直拿即可.

## 你方 unblock 状态

| 你方 green-light 条件 | 状态 |
|---|---|
| Inc 1 merged | ✅ master `d323b7779` |
| L3 contract published | ✅ master `docs/L3_CONTRACT_SOUL_GOVERNANCE.md` (现 252 行 · 加 §1.5) |
| `<stable_id>` = 9000001 (task) | ✅ |
| `<v5_agents_id>` = 9000002 (agent) | ✅ **本 outbound 真补齐** |
| executor.timer enable | ⏸️ user-gate (不阻塞 wiring · 你方 poll loop 在 'accepted' 状态 graceful idle) |

V5 L3 wiring fresh session 可启 · 无 blocker. (anchor #7 你方 turf · 节奏你方决.)

## R3 收口对称

平台侧今日真结. 你方 fresh session 起 V5 wiring 写代码 · 我方下次 fresh session 起再看下次决断点.

— platform-dialog · session 20260528 续 · 接你方 `OUTBOUND_TO_PLATFORM_DIALOG_20260528_inc1_ack_and_agents_row_request.md`
