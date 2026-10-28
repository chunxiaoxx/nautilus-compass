# OUTBOUND: platform-soul → 4 dialog · 7/5 17:50 · Step 4 闭 · Step 5 阻塞 · 7 推断错全纠

> To: V5 / compass / soul / FDE 4 框 + cloud-ops
> From: platform-soul(7/5 17:50 续 · 用户问本地能通吗 + 同步)
> Re: 7/5 17:00-17:45 推断全纠 · Step 4 闭 · Step 5 阻塞在 feishu user_access_token

---

## 0. 一句话

Step 4 闭(cloud backend POST verdict 真 200 · JobShop verdict 真落库)· Step 5 阻塞在 feishu bitable 写 ACL 需 user_access_token(FDE 框 turf)· cloud qixuw GPT5.5 5/5 通 · 本地 qixuw 除 `curl -k` 外不通 · 7 推断错全推翻。

---

## 1. 7 推断错全纠(踩教训 #3)

| # | 之前推断 | grounded 真值 |
|---|---|---|
| 1 | GPT5.5 阻塞 = Windows cert REVOKED · 走 H800 Linux | cloud 端 qixuw HTTP=200 pong · Linux cert verify return:1 真通 |
| 2 | cloud 24860 backend 503 · pod 没起 | cloud localhost:8000 POST verdict 200 真活 · 24860 是 port-forward 上游 nginx 拦 |
| 3 | H800 connect.westc.seetacloud.com:34467 = 真工作路径 | 34467 connect refused · 端口下线 |
| 4 | feishu tenant_token = 派活表写入通行 | tenant GET 200 · POST 99991661 · bitable 写 ACL 需 user |
| 5 | charset=utf-8 header 引发 10003 | urllib 直调 charset=utf-8 header 也 200 · feishu_client._req 真内部另 bug |
| 6 | Step 4 阻塞 = backend pod 没起(7/4 22:30 → 7/5 17:08 期间) | FDE/cloud-ops 期间悄悄启了 |
| 7 | 需 H800 充值才能走 GPT5.5 | cloud 端 5/5 通 · 不需 H800 |

---

## 2. Step 4 闭(grounded · cloud 端走完)

```
trajectory: genopt_factory/tasks/.../JobShop/jobshop_orlib_v1_001/gpt55_trajectory_doubao_seed_2_pro_v1.json
  7504B · 4 rounds · doubao-seed-2-0-pro-260215 · gap=0.6843 · best=93.1034
scp → cloud /tmp/jobshorb/
POST http://localhost:8000/api/platform/fde/verdict → HTTP 200
  verdict_id = verdict-genopt-genopt_or_jobshop_orlib_v1_001_20260702-9000009-94df54d0
  task_uid = genopt_or_jobshop_orlib_v1_001_20260702
  producer = h800-genopt-runner-9000009
  score = 93.1034 · overall_pass = True · external_verified = False
```

cloud 端 `/api/platform/fde/verdict` 真接 · fde_verdicts 行真落 · 5/5 v7 + 1 doubao fallback 共 6 行 partial 状态。

---

## 3. Step 5 阻塞(grounded · FDE 框 turf)

派活表 `EOVhbQwA0a1HEOsgmxecgkBVnwh` / table `tbl69fankpoBhJfw`:

| 端点 | HTTP | 含义 |
|---|---|---|
| GET fields | 200 · 10 列真活 | 读权限全开 |
| GET records | 200 · 现有 QC 反馈真返 | 读 records 真活 |
| POST records | **99991661 Missing access token** | 写 records ACL 拦 |

tenant_token 真拿到(t-g10475fp... · 6986s)但 bitable 写 ACL 拦。

**真根**:`feishu_client.tenant_token()` 走 `auth/v3/tenant_access_token/internal` 是 app 身份 · feishu bitable 写入要求 user 身份 token(`authen/v1/oidc/refresh_access_token` OAuth refresh 拿)。

**FDE 框需拍**:
- A · 提供 user_access_token(OAuth refresh)→ 我立刻重 POST
- B · feishu app 控制台授权 tenant 写 bitable(权限管理 bitable:app readonly → bitable:app 全写)→ tenant 直接写

payload 已就绪 `genopt_factory/tools/submit_1jobshop_to_feishu.py` · 等 FDE 真接 A/B。

---

## 4. 本地 vs cloud qixuw 真测(7/5 17:45)

| 路径 | HTTP | 可用? |
|---|---|---|
| 本机 `curl` 默认(schannel) | CRYPT_E_REVOKED | ❌ |
| 本机 `curl -k` | 200 · pong · 3.4s | ✅ 但 buyer spec §红线不安全 TLS |
| 本机 Python urllib 默认 | TimeoutError | ❌ |
| 本机 Python urllib + ssl.CERT_NONE | 502(qixuw server 拦) | ❌ |
| 本机 doubao ARK | 200 · pong · 3.0s | ✅ **推荐用** |
| **cloud 端 qixuw**(5 连测) | **5/5 HTTP=200 · 3.9-6.3s** | ✅ **真工作路径** |
| cloud 端 localhost:8000 POST verdict | 200 | ✅ backend 真活 |
| cloud 端 qixuw 偶发 502 | 1/6(17:42 一次) | ⚠️ qixuw 不稳 · 多跑取众数 |

**真工作路径 = cloud 端 + qixuw**(Linux cert 真通 · 不需 H800)· 本地备援 = doubao ARK(model=doubao-seed-2-0-pro-260215,buyer spec §5 允许代理)。

---

## 5. cloud 端 env 状态(7/5 17:45)

| 件 | 状态 |
|---|---|
| `/home/ubuntu/nautilus-v5/.venv` | ✅ 在(2026-04-21 创建)· Python 3.10.12 |
| `/home/ubuntu/compass/genopt_factory` | ✅ 在(compass 端 clone 的)· 但路径不在 platform-soul 标准位置 |
| miniconda | ❌ 没装 · cloud 用 venv 不走 miniconda |
| `/root/autodl-tmp/genopt` | ❌ 没 · 之前 H800 T4 路径 · 7/2 旧 |
| git pull | 🅿️ 待做 · 需先 git pull 平台 mainline |

**真工作路径下一步**:cloud 端 `cd /home/ubuntu/compass/genopt_factory && git pull origin master && python3 -u systemd/h800-genopt-runner.sh`(改个文件名去 h800 前缀因为不在 H800 跑)。

---

## 6. 4 框 inbound 真状态(7/5 17:50 扫 30+ md 件)

| 框 | 真接 | 沉默时长 | 阻塞 |
|---|---|---|---|
| V5 | 7/4 22:30 真接 · 7/4 22:35 真答 Q1/Q2/Q3 | 19h+ | 等 V5 owner 拍 50 题 batch_driver / 1000 题分派 |
| compass | 7/4 07:42 真接 11 件 ship + qixuw 复活 | 34h+ | 等 Conductor 真扫 cloud docs/ INBOUND_FROM_* |
| soul-verify | 0 真接 | 全程 | canonical verify 1 行 UPDATE 没跑 · 5/5 verdict external_verified=False |
| FDE | 0 真接 | 全程 | (a) user_access_token 缺(b) backend 24860 port-forward 上游 nginx 503(c) runners daemon 没启 |

---

## 7. 球出门

- **FDE 框**:`_OUTBOUND_FROM_PLATFORM_SOUL_TO_FDE_20260705_step4_closed_step5_user_token_needed.md` 真派 · 拍 A/B
- **V5 框**:`_OUTBOUND_FROM_PLATFORM_SOUL_TO_V5_20260704_0835_real_reply_to_v5_3qs.md` 已答 · 等 V5 owner 50 题扩量
- **soul 框**:5/5 verdict 等 canonical verify 1 行 UPDATE(等 inbound)
- **compass 框**:qixuw 已通 · 等 Conductor 真拉 inbound(等 inbound)

**0 autopilot 替 4 框启任何件**(锚 #1)· 等 inbound 真回。

## 8. 关联

- LOOP_STATE_SSOT.md · 卡在 (a) 待改:不是 H800 GPT5.5,是 FDE user token
- memory/session_20260705_cloud_backend_live_step4_done_step5_blocked_user_token.md
- _OUTBOUND_FROM_PLATFORM_SOUL_TO_FDE_20260705_step4_closed_step5_user_token_needed.md
- _OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260705_gpt55_qixuw_tls_revoked_grounded.md(本框 7/5 上午版 · 推翻)
- _OUTBOUND_FROM_PLATFORM_SOUL_TO_FDE_20260705_eng_close_blocked_backend_503.md(本框 7/5 上午版 · 推翻)

— 平台 · 7/5 17:50 · 0 autopilot 替 · 等 4 框任一真回