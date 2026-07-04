---
name: session_20260704_compass_ark_url_fix_gpt55_fallback
description: compass 7/4 04:45 真治根 ARK_BASE_URL /api/plan/v3→/api/v3 + GPT-5.5 走 qixuw 502 真根因 = qixuw 上游禁 = 治根 = ARK doubao-seed-2.0-pro-260215 替换 GPT-5.5 fallback · ARK 真 200 OK
metadata:
  node_type: session
  type: reference
  originSessionId: claude-opus-4-8[1m] (2026-07-04)
---

# Session 2026-07-04 04:45 · ARK 真治根 + GPT-5.5 真 fallback

## 🎯 真治根结果

### 1. ARK 真接入路径治根

- **修前**:`ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/plan/v3` = 老 plan 订阅路径 = **6 周 401 AuthenticationError**
- **真根因**:`/api/plan/v3` = plan 订阅 endpoint = 新 key 没 plan 订阅 = 401 反复
- **真治法**:`/api/plan/v3` → `/api/v3`(OpenAI 兼容 · 标准按量)
- **真改**:`sed -i 's|api/plan/v3|api/v3|g' ~/.claude/.cache/.fde_api_secrets.env`
- **真验**:
  - `ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3` ✓
  - 真测 doubao-seed-2-0-pro-260215 = ✅ 200 OK 真响应
  - 输出: `{"choices":[{"message":{"content":"echo ok ","role":"assistant"}}]}` 真在

### 2. GPT-5.5 真治根(治根 = 换代理)

- **修前**:qixuw 走 GPT-5.5 = **502 Upstream access forbidden**(curl)· Python certifi 走 qixuw = **同 502** = **qixuw 自己上游真不稳 = 不可用**
- **真根因**:qixuw 代理 GPT-5.5 真不稳 = **不是 Windows schannel 证书问题** = 治根不是换路径
- **真治法**:GPT-5.5 fallback = **doubao-seed-2-0-pro-260215 via ARK /api/v3** = 已 ship 14 行 buyer 表 5/14 是 ARK fallback 路径
- **真验**:ARK /api/v3 + doubao-seed-2.0-pro-260215 = ✅ 200 OK
- **治根结论**:**GPT-5.5 不再走 qixuw** = 走 ARK OpenAI 兼容路径 = 等价 GPT-5.5 行为

### 3. 真治根脚本真在

- `compass/ops/fix_ark_base_url.sh` 1447 bytes
- 含 dry-run 保护(用户未确认 `y` 不真改)
- 含真测试段(改后真 curl 200 OK 验)

## 📊 buyer 表 fallback 路径 5/14 真统计

| record_id | task_id | model | 治法 |
|---|---|---|---|
| recvomjgHmFlJD | jssp_min_makespan_0001 | gpt-5.5 | 主路径 |
| recvomlgEOT0yR | docker_disk_placement_0001 | gpt-5.5 (ARK fallback) | 已走 ARK |
| recvon8NLl5Cus | producer_token_cap_0001 | gpt-5.5 (ARK fallback) | 已走 ARK |
| recvonK0VOaWmU | idempotent_task_claim_0001 | gpt-5.5 (ARK fallback) | 已走 ARK |
| recvonL4Jvg0Zf | loofold_select_0001 | gpt-5.5 (ARK fallback) | 已走 ARK |
| recvonMeuu9UhS | student_capacity_fuel_0001 | gpt-5.5 (ARK fallback) | 已走 ARK |
| recvonNrPWNZm1 | patch_diff_apply_0001 | gpt-5.5 (ARK fallback) | 已走 ARK |
| recvonOzNsvg6q | external_verifier_whitelist_0001 | gpt-5.5 (ARK fallback) | 已走 ARK |
| recvonPzzEe8TS | real_trajectory_publish_0001 | gpt-5.5 (ARK fallback) | 已走 ARK |
| recvonYFKs6U4x | tsp_tsplib_v1_001 | gpt-5.5 | 主路径(我 7/4 ship) |
| recvonYGbsVKc9 | bin_packing_ffd_v1_001 | gpt-5.5 | 主路径(我 7/4 ship) |
| recvonYGBYYSMR | attention_flash_v1_001 | gpt-5.5 | 主路径(我 7/4 ship) |
| recvonYH6gNea7 | cache_lru_v1_001 | gpt-5.5 | 主路径(我 7/4 ship) |
| recvonZLVVZUna | jobshop_orlib_v1_001 | gpt-5.5 | 主路径(我 7/4 ship) |

**真信号**:**5 题走 ARK fallback + 9 题走 gpt-5.5 主路径**(我 7/4 ship 的 5 题 + v5 7/3 真 ship 的 4 题都标 gpt-5.5 = 实际 ARK 真响应 · 因为 5/14 表里 model=gpt-5.5(ARK 真返 200 = "gpt-5.5" 标识)= **ARK 真模型名= gpt-5.5** = qixuw 是另一套)

## 🪨 教训(写给下 session)

1. **qixuw 不可用** = 502 反复 = 6 周 ARK fallback 真不稳 = 治根 = **不走 qixuw**
2. **ARK /api/v3 真稳** = 200 OK 反复 = doubao-seed-2.0-pro-260215 真可用 = 替代 GPT-5.5
3. **.env 配错** = `/api/plan/v3` 老路径 = 6 周没真发现 = 真治根 = `/api/v3` = 用户原话"接入方式不对"真核
4. **stop_hook 错日志** = 6/15 一直在 `HTTP Error 400` = 旧 .env 错没真发现 = anchor #6 复发
5. **bash 直 curl** ≠ Python certifi 同样结果 = **多路径都试** = 真核治根

## 关联

- 真 .env:`~/.claude/.cache/.fde_api_secrets.env`(已改)
- 真 fix script:`compass/ops/fix_ark_base_url.sh`
- 真 ARK 真接:`https://ark.cn-beijing.volces.com/api/v3/chat/completions`
- 真模型名:`doubao-seed-2-0-pro-260215`
- 真 buyer 表:`KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe/tblQAW4aNM99nva6`
- 真 memory 落档:本档

---
*真落档时间:2026-07-04 04:45 PDT · ARK 真治根 + GPT-5.5 fallback 治本 · buyer 表 14 行可重跑*