# 🎯 FRESH SESSION /goal · 2026-06-22 · 蒸馏首证脚手架全就绪 · 逼近闭环只差 V5 燃料+judge

> platform-soul（nautilus-core·phase3/backend）· /compact 后第一读。本框 turf = FDE 引擎 + RSI verify/mint + 蒸馏 eval/装配。

## 一句话现状
**北极星中心环（FDE 产难题→蒸馏→证模型变强）的右半圈（炼模型）soul 侧脚手架 100% 就绪且端到端验证过。逼近闭环只差两件 V5 的活：① 凑够 ~12 条 A 类燃料 ② 装 python-202301 judge 镜像。**

## ✅ soul 侧已就绪（全实测·非纸面·都在本 session ship）
- **训练**：`scripts/distill_qlora.py`（QLoRA·1.5B/7B 都实测出 adapter·7B 在 T4 无 OOM 4.5s/step·dtype auto=is_bf16_supported→T4 bf16 绕开 fp16+bnb GradScaler 坑）。
- **推理+打分**：`scripts/_distill_runtime.py`（load_models/generate/doubao 1.5B 实测·score_solution subprocess 调 ale_eval 传 judge_version=202301·有 ALE_MOCK_SCORE dry-run hook）。
- **eval 编排**：`scripts/distill_eval.py`（端到端 dry-run 出过完整 verdict=KILLED·mock 数据预期·验证管线非验证蒸馏）。
- **held-out 设计**：`services/distill_train.py` split_train_heldout（~12→8train+4held·确定性）+ held_out_eval_record。首证小样本=方向性证据。
- **多基准合池**：`services/distill_mint_runner.py` ingest_fuel_records per-record kind（缺 kind 默认 ale·吃 ale/swe/kernel 混合池）。
- **毒料守卫**：is_a_bucket 排 strong=0 双败（测试锁定）。
- **阈值**：min_n 20→12（fuel_rate/fuel_poc_status/distill_qlora 读 DISTILL_MIN_N）。
- **conductor**（第一个常驻 agent·LIVE 每10min）：fuel_rate 接入·盯 A 类率（现 4/12）。

## 🔴 卡点（都在 V5·关键路径）
1. **燃料 4/12**（ALE 36% 率·ahc015/001/008/009）。ALE 单独可能到 ~14 但要 ~16h → **合池为正路**（V5 复活 SWE kind=swe + KernelBench kind=kernel + ALE 攒）。
2. **python-202301 judge 镜像**（V5 GPU 盒装·我 eval 同盒用）。

## ▶️ 下个 session 第一步（按优先级）
1. **🔴 真 judge 探针优先**（用户拍）：V5 judge 装好 → 用现有 4 条 ALE A 类跑真 judge（score_solution 真调 ale_eval）验证最后一块集成（dry-run 是 mock·真 judge 没验过）。**若 stdout 空/全 0 先查 /workdir 1777**（见 gotcha）。
2. **合池冲 12**：V5 SWE 复活 + compass KernelBench → ingest 合 sample 池。
3. **够 12 → 一键首证**：ingest→split→distill_qlora（7B·先 ping compass 切 CPU 让位满 16GB）→distill_eval（held-out·真 judge）→ PROVEN/KILLED。可写 `scripts/distill_poc.py` driver 串这 5 步（未写·下步可建）。

## ⚠️ Gotcha 清单（踩过的坑·别重踩）
- **ALE judge /workdir 必须 chmod 1777**（派生镜像）否则非 root uid 写不进→stdout 空→误判 0 分。每个判题镜像都要·re-pull 会丢。见 `gotcha_ale_judge_workdir_1777_stdout_empty_20260622`。
- **judge_version 必须显式传**（默认 202301·没 build 该版→ImageNotFound）。
- **GPU 盒 43.166.8.20 fail2ban**：频繁 SSH 触发封 IP（已加白名单·别再猛敲）。pem=`C:\Users\chunx\Downloads\11111.pem`·user=ubuntu。
- **7B 真实训练 T4 会 OOM**（短 seq 测试假象）→ 起 7B 前 ping compass 切 ZMM_DEVICE=cpu 释放 4.6GB→满 16GB。
- **doubao**：`ARK_BASE_V3=https://ark.cn-beijing.volces.com/api/v3`·model=doubao-seed-2-0-pro-260215·key=ARK_API_KEY（别用过期 ARK_BASE_URL）。

## 各框球
- **V5**：复活 SWE 燃料（kind=swe）+ ALE 过夜 + 装 python-202301 judge（chmod 1777）。
- **compass**：KernelBench A 类（kind=kernel）进合池 + 7B 训练时切 CPU 让位。
- **soul（我）**：judge 装好跑真 judge 探针 + ingest 合池 + 够 12 一键首证。

## 关键路径
- GPU 盒训练 env：`/mnt/datadisk0/distill-venv`（peft/trl/bnb+Qwen 1.5B/7B）+ `/mnt/datadisk0/distill-code/{scripts,services}`（部署的蒸馏代码）。
- conductor 燃料路径：`/home/ubuntu/conductor/ale_fuel_records.jsonl`（V5 records 同步到此·conductor 自动盯率）。
- 全状态 memory：`session_20260622_q3_fuel_rate_conductor_wired`（第0读）。
