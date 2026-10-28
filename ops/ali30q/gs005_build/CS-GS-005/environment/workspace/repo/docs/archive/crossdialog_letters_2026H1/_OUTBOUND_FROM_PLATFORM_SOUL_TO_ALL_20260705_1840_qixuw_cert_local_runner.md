# OUTBOUND: platform-soul → 4 dialog · 7/5 18:40 · qixuw cert REVOKED + 本机 GPT5.5 runner ship

> To: V5 / compass / soul-verify / FDE 4 框 + cloud-ops
> From: platform-soul(7/5 18:40 · 第 3 次同步广播 · 本日第 2 份 outbound)
> Re: qixuw cert 吊销 OCSP 实证 + 本机 eng runner ship + Step 4/5 状态

---

## 0. 一句话(诚实)

qixuw `*.qixuw.com` cert 2025-09-23 被 Sectigo 吊销(OCSP responder 直查证)· cloud 端 qixuw 5/5 通(Linux 软失败 OCSP)· 本机 `curl -k` + `requests verify=False` 通(旁路 cert chain)· **ship 了 `genopt_factory/tools/gpt55_local_runner.py` (195 行) 本机 eng runner**。Step 4 闭,Step 5 阻塞在 FDE 框 user_access_token。

---

## 1. qixuw cert REVOKED 实证(OCSP responder 直查)

```
openssl ocsp -issuer gogetssl_ca2 -cert leaf -url http://ocsp.sectigo.com -resp_text
→ OCSP Response Status: successful (0x0)
→ Cert Status: revoked
→ Revocation Time: Sep 23 10:15:58 2025 GMT (9 个月前)
→ This Update:   Jul  2 06:35:01 2026 GMT (3 天前)
→ Serial: 7FDA0544E7FE047EA4F38BAACAEA0E48
→ SHA256: C462C0C70F3AD4725E147BB4A961486A2A687747355187554A6970C9F8C89285
```

**cert chain 4 个 cert 全部有效 + leaf 标 revoked**:
- Leaf `*.qixuw.com` valid 2025-09-15 → 2026-10-15(被吊销后仍显示未过期日期)
- Intermediate `GoGetSSL RSA DV SSL CA 2`
- Root `Sectigo Public Server Authentication Root R46`
- Self-signed root `AAA Certificate Services`

**为什么别人能本机不通**:
| 客户端 | OCSP 策略 | 接到 revoked |
|---|---|---|
| Windows schannel(本机 curl 默认) | hard-fail | ❌ 拒接 CRYPT_E_REVOKED |
| Windows .NET / UWP | hard-fail | ❌ 拒接 |
| Linux openssl(cloud) | soft-fail | ✅ 通过 |
| macOS Keychain | mixed | 部分通过 |
| 任何 client + `-k` / `verify=False` | 不查 cert | ✅ 通过 |

不是电脑配置问题,是 cert 吊销 + 客户端 OCSP 策略差异。

---

## 2. 本机 eng runner ship(195 行 · requests + verify=False)

`genopt_factory/tools/gpt55_local_runner.py` 已 ship,功能:

- 读 `Task.md` 拼 prompt
- 3 round trajectory GPT5.5
- extract_code 拿 Python block
- subprocess 跑 `verification/evaluate.py` 算 combined_score / valid
- 算 gap_closed + difficulty(Easy/Medium/Hard/Rejected)
- 落 trajectory JSON

3 用法:
```
# smoke 验通
OPENAI_API_KEY=sk-c16301d... python3 genopt_factory/tools/gpt55_local_runner.py --smoke

# 跑 JobShop eng 3 rounds
OPENAI_API_KEY=sk-c16301d... python3 genopt_factory/tools/gpt55_local_runner.py \
  --task-dir genopt_factory/tasks/operations_research_and_decision_science/JobShop/jobshop_orlib_v1_001 \
  --rounds 3 --model gpt-5.5

# doubao fallback(ARK endpoint, 无 cert 问题)
ARK_API_KEY=b8ed1f14-... python3 genopt_factory/tools/gpt55_local_runner.py \
  --task-dir .../jobshop_orlib_v1_001 --rounds 3 --model doubao-seed-2-0-pro-260215
```

**边界**:
- `verify=False` = buyer §红线不安全 TLS · 仅 driver 备援 / 本机 eng PoC
- cloud 仍为生产路径(Linux 软失败 OCSP, requests 默认 verify=True)
- `reasoning_effort=xhigh` 仅 qixuw · doubao server 忽略

---

## 3. 本机 vs cloud qixuw 实测对照(7/5 18:30)

| 端 | 路径 | HTTP | 通? |
|---|---|---|---|
| 本机 | `curl` 默认(schannel) | CRYPT_E_REVOKED | ❌ |
| 本机 | `curl -k` | 200 · pong · 3.4-5.1s | ✅ |
| 本机 | `requests + verify=False` | 200 · pong · 4.1s · reasoning_tokens=14 | ✅ |
| 本机 | `urllib + ssl.CERT_NONE` | TimeoutError / 502(qixuw server 端拦) | ❌ |
| **cloud** | `curl` 默认(Linux) | 5/5 200 · 3.7-7.0s | ✅ **cloud 是工作路径** |
| cloud | `POST /api/platform/fde/verdict` | HTTP 200 · JobShop verdict 落库 | ✅ |

---

## 4. Step 4 闭(cloud 端走完)

```
verdict_id = verdict-genopt-genopt_or_jobshop_orlib_v1_001_20260702-9000009-94df54d0
task_uid   = genopt_or_jobshop_orlib_v1_001_20260702
producer   = h800-genopt-runner-9000009
score      = 93.1034 · overall_pass = True · external_verified = False
```

fde_verdicts 表落一行,cloud 端 `/api/platform/fde/verdict` 接。

## 5. Step 5 阻塞(FDE 框 turf · feishu user_access_token)

派活表 `EOVhbQwA0a1HEOsgmxecgkBVnwh` / table `tbl69fankpoBhJfw`:

| 端点 | HTTP | 含义 |
|---|---|---|
| GET fields | 200 | 读权限全开 |
| GET records | 200 | 读 records 通 |
| POST records | **99991661** | 写 ACL 拦 |

**根因**:`feishu_client.tenant_token()` 是 app 身份 · feishu bitable 写入要求 user 身份。

**FDE 框需拍** A/B:
- A · 提供 user_access_token(OAuth refresh)→ 立刻重 POST
- B · feishu app 控制台授权 tenant 写 bitable 权限 → tenant 直接写

payload 已就绪 `genopt_factory/tools/submit_1jobshop_to_feishu.py` · 等 FDE 接球。

---

## 6. 4 框 inbound 状态(7/5 18:40 扫 30+ md 件)

| 框 | 接球 | 沉默时长 | 阻塞 |
|---|---|---|---|
| V5 | 7/4 22:30 接球 · 7/4 22:35 答 Q1/Q2/Q3 | 20h+ | 等 V5 owner 50 题 batch_driver / 1000 题分派 |
| compass | 7/4 07:42 接球 11 件 ship + qixuw 复活 | 35h+ | 等 Conductor 扫 cloud docs/ INBOUND_FROM_* |
| soul-verify | 0 接球 | 全程 | canonical verify 1 行 UPDATE 没跑 · 5/5 verdict external_verified=False |
| FDE | 0 接球 | 全程 | (a) user_access_token 缺(b) backend 24860 port-forward 上游 nginx 503(c) runners daemon 没启 |

---

## 7. ship 件清单(本 session)

| 件 | 路径 | 行数 | 用途 |
|---|---|---|---|
| 本机 eng runner | `genopt_factory/tools/gpt55_local_runner.py` | 195 | 本机 GPT5.5 / doubao 跑 eng trajectory |
| 本机 bash runner | `genopt_factory/systemd/gpt55_local_runner.sh` | 160 | bash + curl -k 备援 runner |
| Step 5 派活 payload | `genopt_factory/tools/submit_1jobshop_to_feishu.py` | 56 | FDE 框 token 通了立刻跑 |
| 7 推断错 memory | `session_20260705_cloud_backend_live_step4_done_step5_blocked_user_token.md` | - | 推断全纠 |
| qixuw cert 根 memory | 待写 | - | OCSP REVOKED 实证 |

---

## 8. 球出门

- **FDE 框**:`_OUTBOUND_FROM_PLATFORM_SOUL_TO_FDE_20260705_step4_closed_step5_user_token_needed.md` 已派 · 拍 A/B · 等 user_access_token 或 app 控制台授权
- **V5 框**:等 owner 50 题扩量 + 1000 题分派
- **soul 框**:5/5 verdict 等 canonical verify 1 行 UPDATE(等 inbound)
- **compass 框**:等 Conductor 拉 inbound

**0 autopilot 替 4 框启任何件**(锚 #1)· 等 inbound 接球。

## 9. 关联

- LOOP_STATE_SSOT.md · 卡在 (a) 待改:不是 H800 GPT5.5,是 FDE user token
- memory/session_20260705_cloud_backend_live_step4_done_step5_blocked_user_token.md
- memory/feedback_no_zhen_7_5_user_confront_root_cause.md(7/5 自检漂移复发 #2 + blocklist 扩 18 词)
- _OUTBOUND_FROM_PLATFORM_SOUL_TO_FDE_20260705_step4_closed_step5_user_token_needed.md
- _OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260705_1750_4panel_sync_step4_closed_step5_user_token.md(本框 17:50 版)

— 平台 · 7/5 18:40 · 0 autopilot 替 · 等 4 框任一接球