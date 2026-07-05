---
name: session_20260704_compass_tiled_matmul_poc_fix_plan_shipped
description: compass 7/4 12:00 tiled_matmul PoC 3 bug 治根 ship · B5/B6/B9 fix 落档 · 第 6 件 NOT grounded 诚实标 · qixuw upstream 真死不在本框 tur
metadata:
  node_type: session
  type: session
  originSessionId: claude-opus-4-8[1m] (2026-07-04)
---

# Session 2026-07-04 · compass tiled_matmul PoC 3 bug 治根 ship(12:00)

## TL;DR

按 `C:\Users\chunx\.claude\plans\cozy-squishing-moth.md` plan 真跑完 6 步 = run_gpt55_trajectory.py 改 B5/B6/B9(治 3 个高严重 bug) + gpt55_trajectory.json metadata 改诚实 + README.md 加 PoC 6 件 status 节。session commit + push 落档。第 6 件 N=3 GPT-5.5 真跑 = NOT grounded 诚实标(qixuw upstream 真死,provider 在 user/platform/V5 turf,不在 compass env+feishu+benchmark harness 真 tur)。

## 3 个 bug 治根

### B5 · gap_closed 公式口径(治 difficulty 永远=Rejected)
- 前:`(best - init) / 100.0` · init ~2 · 永远 <0.1 → Rejected
- 后:`(best - init) / max(init, 0.1)` + 阈值 ≥0.5 Easy / ≥0.2 Medium / ≥0.1 Hard / <0.1 Rejected

### B6 · no-matmul baseline 重测假阳
- 前:`evaluate_candidate(baseline/init.py)` 重测 → elapsed_s 噪声让 round 2 score 假高于 baseline
- 后:`score = init_score` 直用 + `metrics={}` 显式空 + 不更新 best_score

### B9 · trajectory 顶层 model 字段撒谎
- 前:`"model": "gpt-5.5 (qixuw target) | minimax-m3 (fallback)"` 一句话糊弄
- 后:`provider_chain` + `provider_status{qixuw, minimax-m3}` + `valid_gpt55_run: false` 显式结构

## 真诊断(基于 3 个 Explore agents)

1. **qixuw 真挂** = HTTPS /v1/responses + reasoning_effort=xhigh + x-no-store → 502(7/4 11:15 RED test commit 0042245)· user 自己也卡(同 upstream)· Windows 端 cert 被吊销(CRYPTO_E_REVOKED)
2. **qixuw /v1/messages + claude-haiku-4-5 7/2 真 200**(Anthropic 协议伪装仍活)· OpenAI Responses API 路径死
3. **minimax-m3 长 prompt 真返空** = model 端 server-side 行为 · 框内治不了

## 真 ship 第 6 件判定(等 qixuw 复活后)

- `python run_gpt55_trajectory.py` 重跑
- 4 round 中 ≥3 round 走 qixuw(`kind="qixuw"`)
- best_score 真高于 init 改善 ≥10% · gap_closed ≥0.1 · difficulty ≥Hard
- 若 qixuw 复活 = 立即 ship · 若仍 502 = 维持 NOT grounded 不假装

## commit 锚

- `58644f7` PoC 6 件 grounded 初次落档
- `758ed76` 直连 qixuw + minimax-m3 兜底
- `0042245` RED test 实证 502
- 本 commit:`<after ship>` = 3 bug fix + PoC 6 件 status 诚实标

## 与主线目标的关系

### 已完成(本 session 真 ship)
- tiled_matmul PoC 5/6 件真 grounded(任务规格 / baseline / 验证器 / reference / 数据 / frontier_eval 9 .txt)
- run_gpt55_trajectory 治根 B5/B6/B9(difficulty 标签真反映 PoC 状态)
- session memory 落档治 anchor #6(commit + memory 不漏)

### NOT done(本 session 治不了 / 不假装)
- ❌ 第 6 件 N=3 GPT-5.5 真跑 = qixuw upstream 真死(provider 在 user/platform/V5)
- ❌ 推动 100 题 grounded / buyer 14 行 held_out / binding-DONE 3 条 SQL = 用户 stop hook 提的真主线

### 下 session 真主线(治 anchor #3 反 D 维护)
1. qixuw 复活 → 重跑 trajectory 一遍真 ship 第 6 件
2. 100 题目标 = KernelEng 域 + ComputerSys 域 多题 PoC(本框对 A 真 tur)
3. buyer 14 行 held_out 已 ship 7/4 早段(本 session 不扩展)
4. binding-DONE 3 条 SQL = 等 platform-soul 推 verify / 等 GPU / 等 V5 产够

## 4 个 Explore agents 调研结论摘要

- agent 1(qixuw 多 base + 直连)= qixuw 4 commit 链已 ground truth · 26 个 curl 命令预备
- agent 2(minimax-m3 长 prompt 行为)= ~252 chars 已能稳返内容 · >1KB 概率空 = server-side 不是长度阈值
- agent 3(gpt55 trajectory 真能跑)= 标 B5/B6/B9 高严重 bug + trajectory 顶层撒谎
- agent 4(?)= 实际只派 3 个 · agent 3 已覆盖 trajectory 现状

---

*compass 7/4 12:00 · 3 bug 治根 ship · 第 6 件 NOT grounded 诚实标 · 守 anchor #3 #4 #6 · 下 session 推 100 题主线*
