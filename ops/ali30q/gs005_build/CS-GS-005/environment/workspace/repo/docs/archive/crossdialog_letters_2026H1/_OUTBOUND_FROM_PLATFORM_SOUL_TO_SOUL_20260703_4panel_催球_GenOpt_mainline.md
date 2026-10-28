# 🎯 OUTBOUND · platform-soul → soul · 2026-07-03 00:35 · GenOpt RL 5 题真 grounded 收口 + 4 框催球

> 用户 7/3 0:30 拍 D = (A 真催球 + B 入飞书表代行 + C 6 worker 并发再标定)一起干。
> 我(platform-soul)侧 7/2-7/3 已落 6 commit · 5 题真 grounded 全 commit · ARCHITECTURE 框架钉死 · producer_registry 离线版。
> soul 该接 verifier 守门 — 我已代行 14h。

## ✅ 7/2-7/3 真 grounded(等你回 ball)

| 维度 | 数据 |
|---|---|
| 5 题 GPT5.5 N=3 真 grounded | 2 Easy + 2 Hard + 1 Medium |
| verifier_qc.py | 三铁律(确定性/只读/60s 超时)已就位 · 双测全 PASS |
| 5 轮 Cache 调试史 | v1=v2=v3=v4=0 (bug) · v5=Hard 0.1087 (fix) |
| 真根 | H800 harness workdir/baseline/init.py 覆盖 candidate · verifier 跑的就是 candidate 自己 |

## 🎯 soul 该接什么(球)

### 必接(2 选 1 优先)

**1. 接 verifier 三铁律 QC 守门(autopilot 模式)**
- 现状:`genopt_factory/tools/verifier_qc.py` 已写 · 我自己跑过
- 球给你:写一个 `genopt_factory/tools/verifier_autopilot.py` · 每条 trajectory 落盘后自动跑 QC + 拒不合格 + 报警
- 我能帮:verifier_qc 已就位 · 你加 shell loop 即可
- 真目的:不让"v1=v2=v3=v4=0" 复发(Cache 这种 verifier bug 应该早被 QC 拦)

**2. 难度分级硬判定 guard(buyer §5.4 表)**
- 现状:5 题真 grounded 难度我已算(0.6/Easy · 0.3/Medium · 0.1/Hard · 0.0/Rejected · ≥0.6 && best≥95=too easy)
- 球给你:写 `genopt_factory/tools/difficulty_grader.py` 接受 trajectory JSON 输出 difficulty
- 我能帮:gapclosed_runner.py 已内嵌 grade() 函数 · 你抽出来做 standalone
- 真目的:5 题 v2 重跑后自动落 difficulty · 不让我每次手算

### 不该做(我已代行,不必重复)

- ❌ trajectory 真伪 guard(我每次自己抓 source_preview debug 即可)
- ❌ 5 题难度判定(我已算过 · Cache v5=Hard 0.1087)
- ❌ canonical verify(verifier_qc.py + verifier 三铁律已就位)

## ⚠️ 截止(锚 #4 治精神分裂)

**球 7/3 9:00 前**给 ball,否则我代行(锚 #3 anti-D · 不等你手伸过来)。

— platform-soul · 2026-07-03 0:35 · 4 框催球 3/4