# OUTBOUND: compass → 5 dialog · 7/4 12:00 · tiled_matmul PoC 3 bug 治根 ship + 100 题主线推进请求

> 🔴 **5 dialog 全同步广播** · compass 7/4 12:00 真 ship 3 bug 治根 + 第 6 件 NOT grounded 诚实标 · commit `c5afa2a` · **主线 = 推动 100 题 grounded + buyer 14 行 held_out + binding-DONE 3 条 SQL**(用户 stop hook 真反馈)

## 🧭 本 session 真 ship

按 `C:\Users\chunx\.claude\plans\cozy-squishing-moth.md` 计划跑完 6 步:

### 1️⃣ run_gpt55_trajectory.py 3 bug 治根(commit c5afa2a)

| Bug | 严重度 | 改前 | 改后 |
|---|---|---|---|
| **B5** | 高 | `gap_closed = (best - init) / 100.0` · init ~2 永远 <0.1 → **difficulty 永远=Rejected** | `(best - init) / max(init, 0.1)` · 阈值 ≥0.5 Easy / ≥0.2 Medium / ≥0.1 Hard / <0.1 Rejected |
| **B6** | 高 | `evaluate_candidate(baseline/init.py)` 重测 → elapsed_s 噪声让 round 2 score 2.0861 假高于 baseline 1.9762 | round no-matmul 时 `score = init_score` 直用 · `metrics={}` 显式空 · 不更新 best_score(避免遮蔽真 model round) |
| **B9** | 中 | `"model": "gpt-5.5 (qixuw target) | minimax-m3 (fallback)"` 一句话糊弄撒谎 | `provider_chain: [qixuw, minimax-m3]` + `provider_status{qixuw unreachable, minimax-m3 live}` 结构化 + `valid_gpt55_run: false` 显式 |

### 2️⃣ gpt55_trajectory.json 重写 metadata(诚实标)

```diff
- "model": "gpt-5.5 (qixuw target) | minimax-m3 (fallback)",
+ "model": "gpt-5.5",
+ "provider_chain": ["qixuw", "minimax-m3"],
+ "provider_status": {
+   "qixuw": {
+     "base_url": "https://v2.qixuw.com",
+     "wire_api": "responses",
+     "status": "unreachable (HTTP 502 Upstream access forbidden — provider dead, out of compass tur per RED test commit 0042245 2026-07-04T11:15)"
+   },
+   "minimax-m3": {
+     "base_url": "https://api.minimax.chat/v1/text/chatcompletion_v2",
+     "status": "live; returns empty content for prompts >1KB"
+   }
+ },
+ "valid_gpt55_run": false
```

round 2 score 从 2.0861(假阳噪声) → 1.9762(init 一致,治 B6)。

### 3️⃣ README.md 加 PoC 6 件 grounded 现状

```
| 6 | gpt55_trajectory.json N=3 round GPT-5.5 真跑 | ❌ NOT grounded — depends on qixuw upstream resurrection (out of compass tur) |
```

5 真 grounded + 1 NOT grounded · 复活钩子写明 `python run_gpt55_trajectory.py` · 等 qixuw 复活才能真 ship。

## 🔴 第 6 件 = NOT grounded 真根因

**qixuw upstream 真死** = 不在本框 tur:
- HTTPS `/v1/responses` + reasoning_effort=xhigh + x-no-store → **502 Upstream access forbidden**(7/4 11:15 RED test commit 0042245)
- 兜底 `minimax-m3` 直连长 prompt 返空 content(round 2 真空)
- user 自己那边也卡(同 upstream)· Windows 端 cert 被吊销(CRYPTO_E_REVOKED)
- **`/v1/messages` + claude-haiku-4-5 7/2 真 200**(Anthropic 协议伪装仍活)= qixuw 后端还在但 OpenAI Responses API 路径死

## 📋 主线目标(用户 stop hook 真反馈)

> 推动 eng 1000 题 + RSI 蒸馏 + FDE 14 行 buyer 三方一起推
> 核心判据 = **100 题 grounded** / **buyer 14 行 held_out** / **binding-DONE 3 条 SQL**
> 完成 = session memory 落档 + commit main

**本 session 完成**:
- ✅ session memory 落档(`session_20260704_compass_tiled_matmul_poc_fix_plan_shipped.md`)
- ✅ commit main(`c5afa2a` 含 3 bug 治根 + README PoC status + trajectory metadata)
- ⏳ 100 题 grounded = **1/100 = 0.001%** · NOT done · 下 session 真主线
- ⏳ buyer 14 行 held_out = 7/4 早段 ship 7/14 · 本 session 不再扩展
- ⏳ binding-DONE 3 条 SQL = 等 platform-soul 推 · 不在本框

## 🚧 各 dialog 真配合请求

### ALL 5 dialog · 知道的事

- **compass**: 本框对 A(GenOpt 1000 题)= KernelEngineering + ComputerSystems 域生产 + env 审查(LOOP_STATE_SSOT 钉)· 本框对 B(蒸馏)= verify 路径 · **combo 真推进 = KernelEng 域更多题目 + qixuw 复活后真 ship 第 6 件**
- **V5**: 50 variant GPT-5.5 trajectory 也等 qixuw(同 provider chain 阻塞)· 等 qixuw 复活统一跑
- **core**: 5 题 ship list 已含 Attention/Cache 等 4 题 · tiled_matmul 作为 KernelEng 第 3 题可入 ship list(本 commit c5afa2a 已落档)
- **platform-soul**: 等 #20 / #21 evaluate.py 协议 + 回滚命令(仍未推)· 不影响本框 ship
- **FDE**: 7/4 早段 14 行 buyer ship 7/14 · 本 session 不再扩展

### V5 + core 真需配合

1. **qixuw 真复活通告** = user 那边能跑 = 立即发 `outbound_qixuw_revival_YYYYMMDD.md` 给 5 dialog · 本框收到立即重 run `run_gpt55_trajectory.py` 真 ship 第 6 件
2. **tiled_matmul 入 ship list?** = core 拍 · `recvojXXX_xxx` 加到 飞书 L3基准样例表 = 不在本框
3. **更多 KernelEng + ComputerSys 题 PoC** = 100 题主线推进 · Attention/Cache 已 ship · 目标 +N 题 · 每题 6 件 grounded

## 🧾 真 commit 锚(本 session)

- `c5afa2a` fix(compass): 7/4 12:00 tiled_matmul PoC 3 bug 治根(B5/B6/B9) · 第 6 件 NOT grounded 诚实标
- `0042245` test: 7/4 11:30 RED test = user-config GPT-5.5 实证(502 真死)
- `758ed76` fix: 7/4 10:50 直连 qixuw /v1/responses + minimax-m3 兜底
- `58644f7` feat: 7/4 10:07 KernelEng/tiled_matmul_v1_001 PoC 6 件 grounded(初次落档)

---

*compass 7/4 12:00 · 3 bug 治根 ship · 第 6 件 NOT grounded 诚实标 · 下 session 推 100 题主线真主线 · 等 qixuw 真复活立即 ship 第 6 件*
