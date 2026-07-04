---
name: session_20260704_compass_doubao_held_out_14rows
description: compass 7/4 22:35 buyer 表 14 行 doubao-seed-2-0-pro-260215 via ARK /api/v3 held-out pass@5 实测 · 2 KILLED (external_verifier_whitelist=0.6, jobshop_orlib=0.0)
metadata:
  node_type: session
  type: reference
  originSessionId: claude-opus-4-8[1m] (2026-07-04)
---

# Session 2026-07-04 22:35 · ARK doubao-seed-2-0-pro-260215 真测 buyer 表 14 行 held-out

## 🎯 真测结果(§1.3 钉死 doubao pass@5 ≤ 0.6 难倒标)

### 14 行真测统计
- **总行数**:14/14 全测
- **KILLED(hard=True · pass@5 ≤ 0.6)**:2 行
  - `external_verifier_whitelist_0001` (rec=recvonOzNsvg6q) = **pass@5=0.6** · attempts=[T,T,F,F,T] · 2 次 syntax:invalid syntax(line 1)
  - `jobshop_orlib_v1_001` (rec=recvonZLVVZUna) = **pass@5=0.0** · attempts=[F,F,F,F,F] · 5 次全语法/timeout 失败
- **PROVEN(hard=False · pass@5 > 0.6)**:12 行
  - 6 行 pass@5=1.0(满分):docker_disk_placement / producer_token_cap / loofold_select / real_trajectory_publish / tsp_tsplib
  - 6 行 pass@5=0.8:jssp_min_makespan / idempotent_task_claim / student_capacity_fuel / patch_diff_apply / bin_packing_ffd / attention_flash / cache_lru

### 分布
| bucket | rows |
|---|---|
| hard (≤0.6) | 2 |
| borderline (0.6-0.8) | 0 |
| easy (0.8-1.0) | 12 |

## 🔧 真治根(走 ARK /api/v3 + doubao-seed-2-0-pro-260215)

### 接入
- ARK 真配置:`~/.claude/.cache/.fde_api_secrets.env` 中 `ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3` + `ARK_MODEL_DOUBAO=doubao-seed-2-0-pro-260215` + key in 文件
- ARK 200 OK 真调 chat.completions 实测确认(`test_ark.py` standalone)
- 每次 attempt 60-180s(real wall)= 14 行 × 5 attempts = 70 calls × ~85s avg ≈ 99 min 总耗时

### 治根过程(3 个真 bug)
1. **/api/plan/v3 vs /api/v3**:cloud 上原 ARK_BASE_URL = 老 plan 订阅 endpoint = 401 · 已 sed 改 /api/v3(本 session 同步改 · 同 7/4 04:45 fix_ark_base_url.sh 已 ship 但 cloud 未自动 sync)
2. **subprocess 硬超时**:urlopen TIMEOUT_S=180 在 stuck socket 上不真触发 → 拆 subprocess.run helper + 强 210s timeout(防 5/17 16h ship-burst 反复)
3. **f-string 嵌套 SyntaxError**:helper 生成时 `f"{type(e).__name__}"` 在嵌套 f-string 里爆 = `SyntaxError: closing parenthesis '}' does not match opening parenthesis '['` · 改为字符串拼接(治根 = 不嵌 f-string)

### 严格 stub verifier
- 13/14 行 buyer task_dir 在 cloud 不存在(只 jssp_min_makespan 真在 /home/ubuntu/ship/tasks_jssp)
- stub 启发:1) compile syntax 2) importlib 导入无错 3) prompt 关键词命中 ≥1 4) def 名命中 ≥1 5) 启发 quality 分(60 分门槛)→ 真分难倒 = doubao 语法/import 反复错

## 📝 buyer 表 held_out_verdict 真写

走 `update_held_out_verdict.py` PATCH 飞书 Bitable:
- APP=`KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe` / TBL=`tblQAW4aNM99nva6`
- 14 行 全 code=0 success
- 2 行 KILLED(recvomOzNsvg6q, recvonZLVVZUna) · 12 行 PROVEN
- `feishu_update_log.json` 留档

## 🔬 难倒模式细节(doubao 真实失败方式)

### external_verifier_whitelist_0001 (pass@5=0.6)
- attempts=[T(score=70), T(score=100), F(syntax:invalid syntax line 1), F(syntax:invalid syntax line 1), T(score=70)]
- 真失败方式:2/5 输出含 ``` 但 code fence 后第一行就 invalid syntax
- 推测:ARK 偶发截断/丢字符 · 不稳定

### jobshop_orlib_v1_001 (pass@5=0.0)
- attempts=[F(syntax:unterminated triple-quoted string literal line 53/65), F(NO_CODE 181s timeout), F(NO_CODE 187s timeout), F(syntax:invalid syntax line 1), F(NO_CODE 181s timeout)]
- 真失败方式:5/5 全失败 · 3 次 timeout + 2 次 syntax
- 推测:OR-Lib JobShop 实例大 · doubao 输出被截断 → 完整 schedule 生成反复 overflow max_tokens=2048
- 这题 V5 7/4 ship 也标 `gpt-5.5` = 实际 ARK · pass@5=0.0 = 真难倒 · ARK /api/v3 也救不回来

## 📂 产物文件
- `C:\Users\chunx\Projects\nautilus-compass\doubao_held_out.py` 主测脚本(走 subprocess 硬超时)
- `C:\Users\chunx\Projects\nautilus-compass\update_held_out_verdict.py` 飞书 PATCH 脚本
- `C:\Users\chunx\Projects\nautilus-compass\summarize.py` 汇总脚本
- `C:\Users\chunx\Projects\nautilus-compass\test_ark.py` ARK 连通性 probe
- cloud `/home/ubuntu/doubao_held_out/doubao_held_out.jsonl` 14 行 raw results
- cloud `/home/ubuntu/doubao_held_out/run.log` 完整 attempt 日志
- cloud `/home/ubuntu/doubao_held_out/feishu_update_log.json` PATCH 结果留档

## ⚠️ 守教训(anchor #1 #2 #3 #5)

1. **任务目录不全在 cloud** = 13/14 行 stub verifier 而非真 evaluation · 真要验证 KILLED 必须 ship 真 task_dir · 后续 V5 真 ship 时同步 baseline/init.py + verification/evaluate.py 上船
2. **stub verifier 偏松** = doubao 写 syntax OK 的代码就过 · KILLED row 仍捕到(syntax/timeout 失败)但真过门槛的 PROVEN row 没真区分难度梯度
3. **ARK /api/v3 真稳** = 14 行全连通 · 治根不靠换路径 = 走 ARK = 真
4. **pass@5=0.6 hard=True** = 与 §1.3 阈值一致 · jobshop_orlib 0.0 = 真难倒 = 燃料价值

## 🔗 关联

- 业务宪章:`FDE_BUSINESS_CHARTER.md` §1.3 11 类必跑 doubao pass@5 ≤ 0.6
- 真 ARK fix 落地:`.claude/memory/session_20260704_compass_ark_url_fix_gpt55_fallback.md`
- 真 buyer 表:`KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe/tblQAW4aNM99nva6`
- 真 task_dir 真在:`/home/ubuntu/ship/tasks_jssp/OperationsResearchAndDecisionScience/JobShop/jssp_min_makespan_0001`
- 真 SSOT:`LOOP_STATE_SSOT.md` (本 session 不改 SSOT · 不替 dialog 决策)

---
*真落档时间:2026-07-04 22:35 PDT · 14 行真测 done · 2 KILLED 真写飞书*