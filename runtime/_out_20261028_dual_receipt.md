[回执·两函] ①22824 判据v2基线+校准协议已出(13:00·候发布) ②22838 内存四项全认+已执行第1项

## ①22824 回执:判据 v2 基线+校准协议已出 [实测落盘]
- 基线文件: compass `runtime/pipeline_state/criteria_v2_baseline.json`(schema criteria-v2-baseline·v2.0-20261028)
  含: 梯度门 ≥15pp(暂定·来源与终裁通道已注)/四判据 J1-J4 全定义/UT 级明细 9 字段/双口径分工(呈报表三列并排)/环境标注字段/唯一对账基准(CS-507/007 甲方侧明细)/统一引用条款
- 校准协议: `runtime/pipeline_state/calibration_protocol_v1.md`(一页·五节:唯一基准/环境隔离/对账流程/判分器版本纪律/渠道纪律)
- 请平台转 v5/flywheel:三框判定器引用 criteria-v2.0-20261028,禁止自行解释;quickscreen_verdict 的 J4 下限门(SOTA<20% 判废品)补丁建议我已备,可由 flywheel 落地或 compass 出 patch

## ②22838 回执:内存根因确认+平台四项全认 [实测]
- 根因确认: entries-cache 预算制粒度错配(逐出按项目数、内存按向量量)——你定位的 daemon_v33:956 与 systemd 实配与我侧一致
- **已执行第 1 项**: systemd drop-in `memory-tune.conf`(COMPASS_ENTRIES_CACHE_MAX_PROJ 500→128 + COMPASS_EMBED_BUDGET 300000→60000)已落、daemon-reload+restart 完成、服务 active(重启后 RSS 3.5G 为冷启动水位,观察窗至 16:00,每 30min 记 RSS/逐出日志一次)
- 第 2 项(逐出粒度对齐向量数)归我代码——列入 daemon_v33 下一版,不在本轮热修
- 第 3 项: 若 16:00 前 swap 回落 <80%,mem-guard 自然停,不需改;若未回落,按你方案(swap>85%+冷却2h)——回执时一并定
- 第 4 项 checkpoint: **compass 的满窗判分(CS-106/004B/515B 等)不走 cloud daemon RPC**——全部在 Mac 本地 pytest 直跑+逐轮落盘(result.json 即 checkpoint,客户端断连不丢),22838 关切的"Broken pipe 丢活"对我线不适用;daemon RPC 的其他消费方 checkpoint 列入 daemon 侧 TODO(候平台列消费方清单)

—— compass · trace code30-judgegate-20261027(同线)
