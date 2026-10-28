# B7 对照表 · disabled unit 19 个"有意停 vs 被忘掉"(2026-10-07 实测,呈用户勾)

> 实测:org 相关 disabled 共 19(static+timer enabled 的组合为正常模式,不计)。分四桶:

## 桶 1 · 有意停用(有明确拍板史,8 个)——建议维持

| unit | 依据 |
|---|---|
| nautilus-v6.service | v6 老实验,叙事中不存在 |
| nautilus-v5-telegram.service | v5 TG 通道弃用(v7-telegram 才是现役 TG) |
| kairos-cron-tick.timer | kairos 止血(10/4)+今日拍修复换道——将重配而非原样启用 |
| v5-wave-kairos.timer | 同上 |
| ecc-fde-scanner.service | FDE 线已收口 |
| compass-t4-tunnel.service | T4 GPU 隧道=按需手动档 |
| compass-mcp-tcp.service | TCP scope 实验后由 mcp-http 替代 |
| v7-llm-judge.timer | service 常驻模式(timer 冗余,非问题) |

## 桶 2 · v7 迁管组(6 个)——随 B6 迁 B 账一起裁定

v7-aligned-tick/v7-audit-24h/v7-registry-export/v7-singleton-audit/v7-spool-monitor/v7-telegram(.service)
→ 处置随"v7 迁 B 账受管"打包:迁管后逐个评估启用,不迁则连状态一起退役。

## 桶 3 · 遗忘候选(5 个,需逐一核态)——**建议下轮逐一测活**

| unit | 疑点 |
|---|---|
| compass-bge-daemon.service | BGE 召回=compass 现役功能——disabled 却可能有影子进程(systemd 外 nohup)在跑,需查 9876 端口 |
| compass-gateway.service | 疑被 compass-mcp-http(enabled)替代——确认后永久退役 |
| soul-scorer.timer | 疑被 soul-executor(enabled)替代——确认后退役 |
| nautilus-truth-weekly.timer | 疑被晨报 digest 替代——确认后退役 |
| nautilus-sot-reconcile.service | service disabled 但 timer enabled——确认 timer 能否独立拉起 |

## 桶 4 · 待核(1 个)

ecc-fde-scanner 已列桶 1;**compass-keeper/mem-guard 等为 static+enabled(正常)**不计。

## 呈批
1. 桶 3 五个:下轮逐一测活(影子进程查/替代关系确认),结果回填此表;
2. 桶 1 八个:确认"维持停用"或点名复活;
3. 桶 2 六个:并入 v7 迁管打包件。

## 测活结果回填(10/7 午后)

| 候选 | 实测 | 定性 | 处置 |
|---|---|---|---|
| compass-bge-daemon | **9876 有影子进程**(9/2x 起,systemd 外运行)+今日 compass 记忆召回在用 | 影子活体+现役 | **已转正 enable**(现进程保留,开机自启) |
| compass-gateway | 目标进程不存在;同机另有 openclaw gateway(19789)+hermes gateway | 被 openclaw/hermes 替代 | 永久退役(留 disabled) |
| soul-scorer | 无进程;soul-executor 为现役替代 | 被替代 | 永久退役(留 disabled) |
| nautilus-truth-weekly | timer disabled 后无产物产出 | 被晨报 digest 替代 | 永久退役(留 disabled) |
| sot-reconcile | **今日 03:03 正常跑**(agents_real=237 synced=247)| service disabled+timer enabled=正常模式 | **除名**(非问题) |

影子进程教训:bge-daemon systemd 外手起→台账与真实状态脱节——"影子进程=台账裂缝"例证(与双账割裂同类)。
