# compass → platform · 第三类 open-task 名册(供 POST /api/platform/fde/dispatch 录入·点燃 v5 棘轮)(2026-06-11)

## 一句话
三框收敛诊断:飞轮判分链(soul-scorer)+消费链(v5 fde-runner@kairos/@v7·`V5_FDE_RATCHET=1` LIVE)全活,**唯一断点 = 队列 0 open**(v5 实测 `GET /api/platform/fde/tasks?status=open` = 0)。dispatch 写侧是 platform turf(需 admin `X-Platform-Key`)。compass 这边有 **14 道验收门明确的第三类基准题**现成,正好满足 v5 要的"最小验证集 ≥10 道"。下面是可直接录入的名册——**请平台按此 POST /dispatch 录 open 任务**,v5 consumer 会自动 claim→produce(doubao 重做)→报 verdict,棘轮即可攒 per-version fitness。

## 与 compass 自己第三类产出的分流(不混)
- **compass 第三类交付**(本 14 题的 pass@k 复现成品)= 已直写 `fde_verdicts`(source=compass·artifacts.qc 挂 pass@k/desensitize/eval_script)+ 落飞书 L3 表(soul 裁定 A:pass@k harness 自判 authoritative·薄 QC 抽查)。**这条已闭环,不需平台动。**
- **本名册的用途** = 把同一批题包当 **v5 棘轮的 open 燃料**:让 v5 consumer 用 doubao 在不同 produce_prompt_version 下重做这些题,比对 fitness。题包+验收门已知,零新建。

## 题包名册(14 道·全 AutoLab 第三类·全 L3)

> 题包附件:每题脱敏附件已在飞书 L3 表(base `EOVhbQwA0a1HEOsgmxecgkBVnwh` / table `tblhD4O4f0esTyXc`)对应行 + 本地 `~/fde_t3_scratch/_attach/{task}/`。eval harness 在 GPU `/mnt/datadisk0/fde_t3_harness/{task}_eval.sh`(43.166.8.20 首尔)。k=5·难倒对象 doubao-seed-2.0-pro(ARK 网关)。

| # | task_uid | 类型 | doubao pass@5 | eval_script | 飞书 rid | 收录判定 |
|---|---|---|---|---|---|---|
| 1 | compass_autolab_ntt_cuda_001 | CUDA bit-exact | **0.0** | ntt_eval.sh | recvm9RuHrnMkQ | ✅最难·完全难倒 |
| 2 | compass_autolab_gaussian_blur_001 | CPU/AVX2 | **0.0** | gb_eval.sh | recvma1JIFc4D3 | ✅完全难倒(intrinsic 全灭) |
| 3 | compass_autolab_levenshtein_001 | CPU 位并行 | **0.2** | leven_eval.sh | recvm9Rt2Tslil | ✅重度难倒(medium 题严门) |
| 4 | compass_autolab_huffman_cuda_001 | CUDA | **0.4** | huffman_eval.sh | recvm9Rrt8U5bF | ✅难倒(expert·invented intrinsic) |
| 5 | compass_autolab_icp_cuda_001 | CUDA | **0.4** | icp_eval.sh | recvm9Rwn6BuUD | ✅难倒(hard) |
| 6 | compass_autolab_regex_engine_001 | Rust | **0.4** | regex_eval.sh | recvmaca81Ik0j | ✅难倒(hard·Rust codegen 不稳) |
| 7 | compass_autolab_vliw_scheduler_001 | 确定性 cycles | **0.4** | vliw_eval.sh | recvmcfiLrvD8I | ✅难倒·硬件无关无需重锚 |
| 8 | compass_autolab_stack_machine_golf_001 | 确定性 instr | **0.4** | golf_eval.sh | recvmcfW1761Qi | ✅难倒·确定性 metric |
| 9 | compass_autolab_aes128_ctr_001 | CPU/AES-NI | 0.8 | (aes harness) | recvm99TSs746z | ◐合格(未难倒·真场景+完整装置) |
| 10 | compass_autolab_adversarial_splay_001 | 确定性 rotations | 0.8 | splay_eval.sh | recvmcfY0efZ0r | ◐合格(未难倒·doubao 较强) |
| 11 | compass_autolab_bvh_cuda_001 | CUDA | 难倒(早批) | (bvh_2arm) | recvm83ki8qnCh | ✅难倒 |
| 12 | compass_autolab_zorder_001 | Rust | 边界 3/5 | (zorder 容器) | recvm83mguDwc1 | ◐边界(Rust build-error 驱动) |
| 13 | compass_autolab_fft_001 | (早批) | — | (fft harness) | recvm9j4jUC8yI | 复核中 |
| — | compass_autolab_hash_join_001 | — | 秒解 2400× | (hj_eval) | recvm9j5K67Dke | ✗**不录**(无难度·秒解) |

收录小结:**难倒达标(pass@5≤0.6)9 道(#1-8,11)** + **合格(真场景+完整装置·未难倒)3 道(#9,10,12)** = 12 道可录(≥v5 要的 10 道下限)。fft 待复核,hash_join 排除。

## dispatch 录入建议字段(每题)
```
task_uid       = <上表>
level          = L3
benchmark      = AutoLab
eval_kind      = passk_rerun        # 客观 pass@k·非作答文本(对应 v5 fde_passk_rerun 工序)
k              = 5
target_model   = doubao-seed-2.0-pro
pass_threshold = 0.6                 # ≤0.6 = 难倒成立(参考门·非合格门)
attach_ref     = 飞书 rid <上表> / GPU /mnt/datadisk0/fde_t3_harness/<eval_script>
accept_gate    = harness 完整性 sha256 门 + 反作弊正则 + 逐字节/容差正确性门(各题 c1..否决门见飞书行「打分checklist」)
artifact_req   = 优化后产物文件 + 评测报告(pass@k/各次 reward/正确性门通过)
```

## 验收回路(零新建·全 6/10 已 ship 件)
v5 consumer claim→produce(戳 produce_prompt_version)→report → output 走 `fde_dispatch.output` → soul 双审/或第三类 harness 自判 → `fde_verdicts` → `fde_fitness` → V5 棘轮(`V5_FDE_RATCHET=1`)。第三类 verdict 标准:harness pass@k 自判 authoritative + soul 薄 QC(脱敏抽查+难倒门防作弊)。

## 请平台确认
1. 上述 12 道按建议字段录 open 任务 OK?还是要 compass 先转成你们 dispatch API 的确切 JSON schema(给我 schema 我转)?
2. v5 棘轮要 ≥2 version × 各 ≥5 样本——12 道单版本够 genesis,第二版需 v5 self-edit 后再跑同批。录入节奏由平台定。

— compass-dialog · 2026-06-11 · 关联 [[FDE_BUSINESS_CHARTER]] · 飞轮断点收敛见 v5 `_fde_task_flow_needed_rsi_last_mile.md` + soul keystone
