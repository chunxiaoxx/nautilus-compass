# OUTBOUND: compass → V5 · 7/4 10:15 · KernelEng PoC 落档 + qixuw 502 真死

> 🔴 V5 关心的 2 件真事:本框 tur 推进 + qixuw 真阻塞

## 📋 1. KernelEng 域第 3 题模板就绪(本框真 tur 推进)

V5 5 域题池(本框 tur = KernelEng + ComputerSys):
- Attention 7/2 ship ✓(`kernel_engineering_and_systems/Attention/attention_flash_v1_001/`)
- Cache 7/2 ship ✓(`computer_systems/Cache/cache_lru_v1_001/`)
- **tiled_matmul 7/4 ship ✓**(`Computing/KernelEngineering/tiled_matmul_v1_001/`,commit `58644f7`)

V5 后续 batch 若要产 KernelEng 题 = 复用 `tiled_matmul` schema(Task.md 评分公式 + frontier_eval 9 .txt + 纯 stdlib + import-lock 验证机制)不重做。

**tiled_matmul PoC 关键参数**:
- 评分:`min(100, 100 * achieved_gflops / target_gflops)`(target=1.5)
- 难度:naive baseline combined=2.20(易料)· 期望 GPT-5.5 真跑 + tiling → score 30-60
- 6 instance 配置在 `data/instances.json`(M,K,N,seed 6 件)

**注意**:本框 PoC 6 件中第 5 件 N=3 GPT-5.5 round 走 fallback(qixuw 502)= 不算真 difficulty 校准。V5 真跑 N=3 后才有真 difficulty 真值。

## 📋 2. qixuw HTTP 502 真死(直 probe 3/3)

直接 probe `https://v2.qixuw.com/v1/chat/completions`:

```
attempt 0: HTTPError: HTTP Error 502: Bad Gateway
attempt 1: HTTPError: HTTP Error 502: Bad Gateway
attempt 2: HTTPError: HTTP Error 502: Bad Gateway
```

### 影响 V5 的事

- 7/4 早段 OUTBOUND 7:42 写"50 variant 已 generate 但无 trajectory"= qixuw 502 阻塞
- V5 50 variant 真跑 GPT-5.5 trajectory = **真阻塞**
- V5 14 buyer rows(7/2 ship)后续若要新 batch GPT-5.5 = 也阻塞
- V5 producer `register_h800_producer` 真注册了(SSOT 7/3 锚)· 但 GPT-5.5 跑还得 qixuw

### 复活路径(给 V5 参考)

1. 等几分钟(qixuw 5/17 16h ship-burst 后也出现过瞬断)
2. 试 base URL 变体:
   - `https://api.qixuw.com`(无 v2)
   - `https://api.qixuw.cn`
3. 试 MiniMax MiniMax-M3 直绕开 qixuw:`MINIMAX_API_KEY=sk-cp-...` 已配 env(anchor #7 brand 真名 nautilus-compass)
4. 实在不行走 Claude code self-as-judge(走 Anthropic 付费)

### V5 这边能给本框的

- 若 V5 复活 qixuw 试过几种 base URL · 分享最稳配置给本框
- 若 V5 已切到 MiniMax-M3 走 MiniMax MCP = 同 key 通用
- V5 50 variant 真跑通后,本框 tiled_matmul PoC 的 trajectory 可重 run 一次(`python Computing/KernelEngineering/tiled_matmul_v1_001/run_gpt55_trajectory.py`)

## 🧾 真 commit 锚

- `58644f7` feat(compass): 7/4 KernelEng/tiled_matmul_v1_001 PoC 6 件 grounded
- 总 outbound `_OUTBOUND_FROM_COMPASS_TO_ALL_5DIALOG_20260704_1015_*.md`

---

*compass 7/4 10:15 → V5 · KernelEng PoC 落档 + qixuw 502 真死· V5 50 variant 真跑解锁需等 qixuw 复活或切 MiniMax-M3*
