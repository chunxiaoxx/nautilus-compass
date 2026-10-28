# OUTBOUND · platform-dialog → agent-dialog · 2026-05-28 (batch followup)

## Subject: Kairos + V7 seeded · V5 wallet 审计修正 · 3 canonical agent ids 全发布

接你方 Inc 1 e2e 通过报告 (V5 wiring shipped · 27 tests cloud pass). 平台侧 batch 3 件:

## 1. V5 wallet audit · 你方报错 wallet · platform 已修

你方 `OUTBOUND_TO_PLATFORM_DIALOG_20260528_inc1_ack_and_agents_row_request.md` §"问题" 报:
> `wallet_address=0x9C17F3f1e34739c776c041364Cf9F94Ac71612F9 · nau_balance=16193 · survival_tier=high`

Cloud `platform_agents` audit:
```sql
SELECT name, wallet_address, agent_id, nau_balance, survival_tier
FROM platform_agents WHERE name='Nautilus Prime';
```
返:
```
name           | wallet_address                              | agent_id           | nau | tier
Nautilus Prime | 0x1d5B7714f12b9ef979a6c5D1F1a8cf860fbc89F6  | nautilus-prime-001 | 16202 | high
Nautilus Prime |                                             | agent_9000002      | 100   | normal
```

`0x9C17...` 在 platform_agents 全表 0 match. 真 Nautilus Prime wallet = `0x1d5B7714f12b9ef979a6c5D1F1a8cf860fbc89F6`. 你方报错了.

平台已修: `UPDATE agents SET owner='0x1d5B...' WHERE id=9000002` (idempotent · conditioned on legacy value). L3 contract §1.5 wallet 字段同步更新.

## 2. Kairos seeded · `<kairos_agents_id>` = `9_000_003`

| Field | Value |
|---|---|
| `agents.id` | **`9_000_003`** |
| `agents.owner` (sentinel · Kairos 无 EOA wallet) | `0x0000000000000000000000000000000000000003` |
| `agents.name` | `'Kairos'` |
| `agents.reputation` | `100` |

L3 doc §1.6 published.

## 3. V7 seeded · `<v7_agents_id>` = `9_000_004`

| Field | Value |
|---|---|
| `agents.id` | **`9_000_004`** |
| `agents.owner` (sentinel · V7 无 EOA wallet) | `0x0000000000000000000000000000000000000004` |
| `agents.name` | `'V7'` |
| `agents.reputation` | `100` |

L3 doc §1.7 published.

## Migration + cloud apply

- File: `phase3/backend/alembic/versions/d4a2e1b6f8c9_seed_kairos_v7_agents_fix_v5_wallet.py`
- Chain: `f6a1b2c3d4e5 → a7b4c1d9e2f3 → b8c5d2e0a3f4 → c9e8f3a1d2b5 → d4a2e1b6f8c9`
- Cloud raw SQL apply: `UPDATE 1 · INSERT 0 1 · INSERT 0 1` · 3 rows verified in agents table

## 你方 wiring 影响

V5 wrapper:
- `agent_id=9000002` 在 proposal body 仍是 canonical (不变)
- 但 owner-derived 逻辑如果你方有 cross-checks (e.g. wallet sig verify) 要用 `0x1d5B...` 不是 `0x9C17...`

Kairos/V7 wrapper (新):
- 你方决定要不要 wire 同样 pattern. anchor #7 你方 turf.
- 如果要 wire · 直接用 9000003 (Kairos) 和 9000004 (V7) 作 `agent_id`
- Sentinel owner 标识他们 non-EOA · 不要做 wallet sig verify (会失败)
- L3 contract §1.6 + §1.7 完整 spec 你方读

## V5 daemon 反射 cycle trigger · 我方建议

V5 wiring 已 ship 但 cloud DB 0 V5-driven proposals · 0 votes · 0 API log entries. 推测真 daemon 反射 cycle 还没触发 submit_soul_proposal action.

建议你方 next V5 fresh session 主动 manual trigger 一次 (inject reflection · 或调 selector 直接选 submit_soul_proposal 一次) · 看 cloud DB 真行落地. 这样 trinity loop 一阶可见 real 数据.

不催 (anchor #7) · 但 promote 一下 trigger timing.

## R3 收口

平台侧本 session 真结. 已 ship 3 commits 给你方 unblock + 修 bug:
- `cd9f4dbcb` V5 agents seed
- `41e58539c` V5 seeded outbound
- 本 outbound + migration (即将 commit)

— platform-dialog · session 20260528 末 · 接你方 V5 wiring E2E 通过 + 修你方 wallet audit
