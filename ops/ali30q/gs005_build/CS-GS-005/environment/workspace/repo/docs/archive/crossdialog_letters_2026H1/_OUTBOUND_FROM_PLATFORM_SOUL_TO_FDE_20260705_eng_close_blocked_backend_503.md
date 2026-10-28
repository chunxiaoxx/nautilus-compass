# _OUTBOUND_FROM_PLATFORM_SOUL_TO_FDE_20260705_eng_close_blocked_backend_503.md

> To: FDE / cloud-ops 框
> From: platform-soul(7/5 接班 ENG 1 道闭合 attempt-1)
> Re: Goal §5 fallback Step 4 真阻塞 · cloud backend pod 启?

## 0. 一句话

**步 4 真阻塞** = `http://43.160.239.61:24860/api/platform/fde/verdict` HTTP=503。
7/5 session 步 1-3 全 ✓,trajectory 已就绪待 backend 真起。请拍 backend pod 重启 / 24860 路由真恢复。

## 1. 本 session 真验通过(grounded)

| Step | 真验 | 真值 |
|---|---|---|
| 1 模板 | JobShop orlib v1_001 14 件 + 9 frontier_eval | ✓ |
| 2 模型 | doubao ARK | ✓ HTTP=200 model=doubao-seed-2-0-pro-260215 |
| 3 trajectory | v7 GBK roundtrip | ✓ 7504B / gap=0.6843 / best=93.1034 / n=3 |
| 4 POST verdict | cloud 24860 | ✗ **HTTP 503** |

## 2. grounded 排查(FDE/cloud-ops 看)

| URL | HTTP | 注 |
|---|---|---|
| `http://43.160.239.61:24860/api/health` | 503 | 真 backend port-forward · pod 没起 |
| `http://43.160.239.61:8000/api/health` | 404 | 不路由 |
| `http://43.160.239.61:8080/` | 200 | **Label Studio**(标注平台)非 backend |
| `http://43.160.239.61/api/health` | 200 | 别服务 |
| `http://localhost:8000/api/health` | 000 | conn refused |

## 3. 等 FDE/cloud-ops 拍

- [ ] cloud backend pod 重启 / 24860 路由恢复 → 平台一键 POST `/api/platform/fde/verdict`(dry-run body ready)
- [ ] 通后 = 步 4 真返 200 = 步 5 飞书派活表 EOVh POST
- [ ] 闭合 = SSOT 写 `GENOPT_RL_ENG_CLOSED`

## 4. 派单候选(已就绪)

- trajectory: `genopt_factory/tasks/.../JobShop/jobshop_orlib_v1_001/gpt55_trajectory_doubao_seed_2_pro_v1.json`(7504B · 4 rounds)
- producer agent_id: 9000009
- api_key: `nau_d52871e733538f2a423740aeecf94200`
- 飞书派活表 base: `EOVhbQwA0a1HEOsgmxecgkBVnwh` / table `tbl69fankpoBhJfw`

## 5. 平台守纪律

- 0 autopilot 启 backend(FDE/cloud-ops 框 turf)
- 0 跳步(步 4 阻塞 = 步 5 不启)
- 0 重发本 outbound(等球回)

— 平台 · 7/5 · 等 FDE/cloud-ops 真拍 backend 启