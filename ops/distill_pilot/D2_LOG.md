# D2 执行台账(2026-11-04 进行中)· 供非实现者复算

判据正本: `docs/soul/SESSION_DISTILL_PILOT_20261104.md`(J1-J6 未动)

## 已完成 [实测]

| 件 | 结果 |
|---|---|
| 模型 | Qwen3-4B-Instruct-2507 Q4_K_M(unsloth GGUF)· 2,497,281,120B · `~/models/distill/` · GGUF 魔数验证 · 下载两段续传(后台时限杀一次+29B 官方仓错误页一次,均恢复) |
| 服务 | llama-server 0.7.0 @127.0.0.1:8765 · -c 32768 -ngl 99 · 无模板泄漏 · 速度: prefill ~900 tok/s / decode ~30 tok/s(解码瓶颈) |
| 压缩臂 | `tools/distill_pilot/compress_arm.py` · 分层切块(消息边界·拼回无损·单测过)→逐块纪要→汇总 · 断点续跑 · 全程本机不出域 |
| 首个验证会话 | 1b0d2327(10/28 判据正本会话·156KB·6 块·581s)· 纪要落 summaries_local/ · 内容质检: 结构完整、事实具体、无模板泄漏 |
| **J1 首读** | 原始 81.6% → 修核验器三病(元信息头注入锚点/日期格式未归一/CJK 假路径误收)后 **95.54%(150/157)**,越过 95% 门;7 个真未命中全是路径=小模型路径改写/脑补指纹 |
| 锚点核验器 v2 | selftest PASS(3真+2假=3/5);新增 strip_preamble/date_variants/CJK-false-path 排除 |

## J5 预检(负结果照报)[实测]

独立信号(正文比)不可分离值守轮: C 组比值 0.72%-1.44% 与 A/B(0.85%-1.43%)完全重叠;1% 阈值 5/10 命中+误伤 2 个 B 组大会话(`j5_prefilter_probe.json`)。
**结论**: 预过滤只能用定义性信号(LOOP 轮指令模板自标识),统计信号不可用。J5 判据按此口径在 D3 重新表述后判定(判据数值不动,判定口径修正需在定谳报告中显式声明)。

## 全量压缩(在跑)

- PID 见 `compress.pid`,日志 `compress_full.log`,产出 `summaries_local/*.md`(断点续跑,已存在即跳过)
- 工时预估 [推断]: 小会话 ~20s/个 · 大会话 ~100s/块 · 全量 35 会话 ≈ 5-10h,今晚完成
- 早期崩溃监视器 30 分钟窗在岗(到期无事件=健康)

## 产出坐标

`summaries_local/`(逐会话纪要)· `compress_stats.jsonl`(逐会话统计)· `llama_server.log` · `compress_full.log` · `j5_prefilter_probe.json`

## D3 待办

参考臂 10 会话(API 强模型,scrub 后外发)→ J1 全量出数 → J2/J3 大模型盲评 → J5 口径修正后判定 → J6 角色定谳 → 定谳报告(非实现者复算)。
