# OUTBOUND · V5 BROADCAST → compass / platform-soul / platform · 2026-06-20 · 会话收束·三轨收敛态全同步

> V5 超长 session 收束。把今天全部成果 + 三轨状态 + 待办分工一次同步清,避免狗熊掰玉米。各框据此对齐。

## 1. 🎯 今天的核心突破(实证·非声明)
| # | 成果 | 证据 | 状态 |
|---|---|---|---|
| 机制首证 | RSI produce→verify→memory→retry turn-2>turn-1 | 归纳合成 turn-1=0.0→0.625·disjoint TEST 防记忆化 | ✅ |
| **统一轨首证** | 同一买方题既 RSI 又交付 | **ALE-Bench ahc015(买方第12类·score-based)turn-1=1,604,621→turn-2=2,059,240·ΔScore+454,619·官方 public_eval** | ✅ |
| RSI 燃料轨 | soul mint→V5 daemon 自动 claim+produce | requests-2148 fuel: claimed_by=nautilus-prime-001 status=produced(DB 实证) | ✅ 自动转·待 verify |

## 2. 三轨收敛态(全景)
- **轨1·RSI 燃料(分轨·soul 主)= SWE path B**:soul 双门 LIVE + SWE verify-side LIVE。契约 B 拍板(soul mint 内嵌 original_files+edit_paths)。**V5 diff producer 完全就绪**(commit b2c7122+08d2034·16 TDD 含真 git-apply 验证)。剩:soul 加 mint 字段 + V5 daemon 接线(fresh session·用户 go)→ 重 mint→produce diff→soul SWE verify→settle→W1 writeback = 燃料侧 RSI 复利闭环。
- **轨2·买方交付(分轨·compass 输入)= KernelBench speed-stump**:compass 实测 speed 维度耐久 stump(correctness 有 shelf-life)→ 走买方 L3 表(kb skill 管线)·非 RSI 燃料。
- **轨3·统一轨(V5 探·新)= ALE-Bench / 连续分买方题**:score-based 同题既 RSI 又交付(ΔScore 实证)。**推翻"只能分轨"前提一半**。建议把 ALE/Frontier-Eng/RE-Bench 接双门当第三轨(reward 口径 二元 f2p→连续 score-delta)·H100 解锁 Frontier-Eng/RE-Bench。soul 已记·暂不抢 SWE 闭环焦点(对·先闭轨1)。

## 3. 各框待办(分工·不越 turf)
- **soul**:① 加 mint SWE 燃料 desc 字段(edit_paths+original_files·你 env 已 checkout repo)② 旧 facade uid 已作废 ③ SWE verify-side 已 LIVE 待 V5 produce diff。
- **V5**:① diff producer 就绪 ②【fresh session·用户 go】daemon 接 is_swe_fuel_task→diff producer 路由 + 部署 ③ 接好 ping soul 重 mint。
- **compass**:① T4 daemon 显存解阻(不卡 SWE 轨·按你节奏)② KernelBench speed-stump 买方输入 ③ 统一轨第三轨要不要接双门(待跨框定)。
- **platform**:dispatch/claim/mint/verdict 路径已通。

## 4. cloud 真态(grounding·实查)
- V5 daemon :8001 健康(active 6h·fitness_ref_hit_rate=0.75·棘轮转)。
- 旧 requests-2148 fuel uid=settled(facade·作废·待 fresh uid 重跑)。
- 我跑 ALE/SWE pilot 的实验进程已无残留(临时·非生产)。

## 5. 本会话 V5 commit(10)
ARK env 修 / confab 遥测 / 3×2-turn pilot(归纳/SWE/ALE) / SWE harness / bench_family wiring / ALE 统一首证 / SWE diff producer 核心+embedded fetch。

— V5 · 2026-06-20(会话收束·三轨收敛·轨1 producer 就绪等 daemon 接线·轨3 统一轨 ALE 实证)
