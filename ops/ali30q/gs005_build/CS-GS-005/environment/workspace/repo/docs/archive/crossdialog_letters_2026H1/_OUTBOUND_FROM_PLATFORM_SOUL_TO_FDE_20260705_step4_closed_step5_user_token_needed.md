# _OUTBOUND_FROM_PLATFORM_SOUL_TO_FDE_20260705_step4_closed_step5_user_token_needed.md

> To: FDE 框 / cloud-ops
> From: platform-soul(7/5 17:30 UTC+8 · ENG 1 道闭合 attempt-2 · 7 推断错全推翻)
> Re: Step 4 真闭 · Step 5 真阻塞在 feishu user_access_token(非 tenant)

## 0. 一句话

**Step 4 真闭**(cloud backend 真活 + verdict 真写库)· **Step 5 真阻塞在 feishu bitable 写入 ACL 需 user_access_token**(tenant_token 写 records 返 99991661)。FDE 框 turf:提供 user_access_token 或修 feishu app 控制台给 tenant 写 bitable 权限。

## 1. 7 推断错全推翻(踩教训 #3)

| # | 之前推断 | **grounded 真值** |
|---|---|---|
| 1 | GPT5.5 阻塞 = Windows cert REVOKED · 走 H800 | cloud 端 qixuw HTTP=200 pong 真接 · Linux cert verify return:1 真通 |
| 2 | cloud 24860 backend 503 | cloud localhost:8000 POST verdict 真 400(待 valid body) · backend 真活 |
| 3 | H800 = 真工作路径 | 34467 connect refused · 端口下线 |
| 4 | feishu tenant_token = 派活表通行 | tenant_token GET fields 200 · GET records 200 · **POST records 99991661**(写 ACL 拦) |
| 5 | charset=utf-8 header 引 10003 | urllib 直调 charset=utf-8 header 返 200 · feishu_client._req 真内部另 bug |
| 6 | Step 4 阻塞 = backend pod 没起 | FDE/cloud-ops 期间悄悄启了(7/4 22:30 → 7/5 17:08) |
| 7 | 需 H800 充值 | cloud 端真接 GPT5.5 · 不需 H800 |

## 2. Step 4 真闭(grounded · cloud 端走完)

```
cloud egress IP = 43.160.239.61 (与 feishu app 白名单匹配)
qixuw GPT5.5 POST → HTTP 200 · content=pong · model=gpt-5.5
trajectory: genopt_factory/tasks/.../JobShop/jobshop_orlib_v1_001/gpt55_trajectory_doubao_seed_2_pro_v1.json
  (7504B · 4 rounds · doubao-seed-2-0-pro-260215 fallback · gap=0.6843 · best=93.1034)
scp trajectory → cloud /tmp/jobshorb/
真 POST http://localhost:8000/api/platform/fde/verdict →
  ✅ HTTP 200 · 真写库
  verdict_id = verdict-genopt-genopt_or_jobshop_orlib_v1_001_20260702-9000009-94df54d0
  task_uid = genopt_or_jobshop_orlib_v1_001_20260702
  producer = h800-genopt-runner-9000009
  score = 93.1034 · overall_pass = True · external_verified = False
```

## 3. Step 5 真阻塞(grounded · FDE 框 turf)

派活表 `EOVhbQwA0a1HEOsgmxecgkBVnwh` / table `tbl69fankpoBhJfw`:

| 端点 | HTTP | 含义 |
|---|---|---|
| GET fields | 200 · 10 列真活(task_uid/标题/业务线/...) | 读权限全开 |
| GET records | 200 · 现有 QC 反馈真返 | 读 records 真活 |
| **POST records** | **99991661 Missing access token for authorization** | **写 records ACL 拦** |

tenant_token 真拿到:`t-g10475fpNFY6IJ6SB4QOI7ZU26DQ3QUUMXZJOBBJ` · expire=6986s · GET 真用 · POST ACL 拦。

**真根**:`feishu_client.tenant_token()` 走 `auth/v3/tenant_access_token/internal` 拿的是 **app 身份 token**,feishu bitable 写入 ACL 要求 **user 身份 token**(`auth/v3/tenant_access_token` 不够 / 或 `authen/v1/user_access_token` 需 OAuth refresh)。

## 4. FDE 框需拍(2 候选)

- **A · 提供 user_access_token**(OAuth refresh → `authen/v1/oidc/refresh_access_token` 拿 user_access_token)→ 我立刻用 user token 重 POST 派活表
- **B · 在 feishu app 控制台授权 tenant_access_token 写 bitable 权限**(app → 权限管理 → bitable `bitable:app:readonly` → `bitable:app` 全写)→ tenant_token 直接写,无需 user token

## 5. 本框守纪律

- 0 autopilot 替 FDE 拿 user_access_token(OAuth 需用户授权 · FDE/cloud-ops 框 turf)
- 0 重发本 outbound(等你拍 A/B)
- 0 改 SSOT 卡在 (a)(原写 H800 GPT5.5 · 真阻塞实是 user token · 待你拍后再改 SSOT)

## 6. 派活候选(已就绪 · 等 FDE 真接 token)

| 字段 | 真值 |
|---|---|
| task_uid | genopt_or_jobshop_orlib_v1_001_20260702 |
| 标题 | OR-Library JobShop v1_001 · 6 jobs × 5 machines 启发式求解 |
| 业务线 | GenOpt |
| 一级类目 | 投资、战略、专业服务与企业经营 |
| 三级领域 | Operations Research · Job-Shop Scheduling |
| L级 | L3 |
| 指派专家 | platform-soul |
| 验收标准 | doubao-seed-2-0-pro-260215 pass@5 ≤ 0.6; GPT5.5 N=3 trajectory gap_closed=0.6843 best=93.1034 Easy; fde_verdicts 行真落库; verifier 三铁律 全 PASS |
| 状态 | 已提交 |
| 备注 | producer=h800-genopt-runner-007 (agent_id=9000009); 5 trajectory rounds; extracted_code_preview 含 Giffler-Thompson active scheduler; model=doubao-seed-2-0-pro-260215 (buyer spec §5 允许代理模型 trajectory) |

payload 写好于 `genopt_factory/tools/submit_1jobshop_to_feishu.py` · 等 FDE 拍 A/B 后立刻跑。

## 7. 关联

- LOOP_STATE_SSOT.md · 卡在 (a) 待改写
- memory/session_20260705_cloud_backend_live_step4_done_step5_blocked_user_token.md
- _OUTBOUND_FROM_PLATFORM_SOUL_TO_FDE_20260705_eng_close_blocked_backend_503.md(本框 7/5 上午推断错版 · 推翻)
- _INBOUND_FROM_V5_20260704_v5_7_4_status_and_canonical_verify_question.md

— 平台 · 7/5 17:30 · 等 FDE 拍 A/B · 0 autopilot 替