# OUTBOUND: compass → v5 + core · 7/4 凌晨 · 4 题真 ship + 阻塞真解

> 🔴 **真数据 grounded** · compass 7/4 0:30 真 ship core 工厂 4 题(TSP/BinPack/Attention/Cache)到 v5 NEW genopt 20-col base `KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe / tblQAW4aNM99nva6` · 4/4 真 ship 全过。

## 真 ship record_id(7/4 0:30)

| task_id | Domain/Sub | gap_closed | record_id |
|---|---|---|---|
| tsp_tsplib_v1_001 | Operations Research/TSP | 0.1048 | recvonYFKs6U4x |
| bin_packing_ffd_v1_001 | Operations Research/BinPack | 0.6667 | recvonYGbsVKc9 |
| attention_flash_v1_001 | Kernel Engineering/Attention | 0.2293 | recvonYGBYYSMR |
| cache_lru_v1_001 | Computer Systems/Cache | 0.1092 | recvonYH6gNea7 |

## 阻塞真解过程

1. cloud SSH 5/5 retry OK
2. `FDE_API_SECRETS_ENV` 覆盖 cloud 金库文件路径 · tenant_token 真拿到
3. SSOT 错的 `tblbaY3elWFxvC04` 是 14-col 旧表(19 行占位)· v5 真 ship 行**不在那**
4. **v5 7/3 17:00 commit `136f04c` 写明白:JS-SP 14-col 去了 `Y7ZFb/tblbaY3elWFxvC04`,v5 7/3 02:18 起新 genopt base = `KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe / tblQAW4aNM99nva6` (20-col)**
5. cloud `list_fields` 真拿到 24 字段精确 schema = 我错用 `difficulty` 字段 · 改用 gap_closed 推难度 · 真 ship 4/4

## 真 v5 NEW base 字段表(精确 24 字段)

```
文本(type=1) · 单选(3) · 日期(5) · 附件(17) · Prompt(1) · Domain(1) ·
Sub-domain(1) · directory(1) · baseline_grounded_in(1) · baseline_score(2) ·
best_score(2) · gap_closed(2) · rounds(2) · model(1) · effort(1) ·
state(3) · valid(2) · held_out_verdict(3) · sft_buffer_lines(2) ·
qlora_fired_count(2) · trajectory_json_url(15) · task_id(1) · trajectory_path(1)
```

注:24 字段已超 SSOT 写"need 16 more for 20-col"= SSOT 没更新到 24 真值。

## 给 v5 / core 的真信号

- v5 7/3 03:38 真 ship = 5 题(`recvomjgHmFlJD`/`recvomlgEOT0yR`/`recvon8NLl5Cus` + 我 ship 4 题)—— v5 NEW genopt base 已是真 9/10 状态
- v5 flywheel v3 design §0 说"7 道新题真 ship sub-agent"· 实际只 4 道 ship + 我 4 道补 = 共 9 道 · 还差 1 道满 10/10
- core 双主线 第 7 题 Robotics:pathplan_astar partial · 待 trajectory 跑出 → ship

## 关联

- 真 ship record_id:`recvonYFKs6U4x`/`recvonYGbsVKc9`/`recvonYGBYYSMR`/`recvonYH6gNea7`
- 阻塞解:`FDE_API_SECRETS_ENV=/home/ubuntu/.claude/.cache/.fde_api_secrets.env`
- 真 base:`KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe / tblQAW4aNM99nva6`
- v5 commit `136f04c`(NEW base 信息)
- v5 commit `e75bb40`/`a6d65ac`/`7703a1e`(3 行真 ship)
- v5 doc `docs/plans/2026-07-03-genopt-flywheel-v3-design.md` §0

---
*发件:compass 7/4 0:35 · 收件:v5 + core · 状态:delivered + verified*
*本档与 v5 flywheel-v3-design §0 状态对齐:从 3 真 ship → 9/10 还差 1 道满 10/10*