# H100/H800 租赁准备清单(2026-06-29 写 · 2026-07-02 SUPERSEDED)

> **🔴 2026-07-02 SUPERSEDED**:本文件被 `docs/plans/2026-07-02-A800-prep-checklist.md` 替代 · 原因:用户 2026-07-02 主动关闭 T4 GPU (43.166.8.20) · 正在租赁 A800 替代 H100(原 6/29 决定)· A800 = Ampere 80GB · 同样能跑 SWE/ALE/Frontier-Eng。
> **历史保留**:本文件保留作 historical record · 所有"明早 H100 到位"假设已过期 · 见新 A800 清单 + SSOT commit(7/2 更新)。
>
> ---
> *(以下是原 6/29-6/30 内容 · 已 superseded)*
>
> **背景**:用户 2026-06-29 决定明早租 H100/H800(记 SSOT 锚点不变 = 蒸馏一条线)。本文件 = **上算力前的最小准备**+ **到位后的最小第一刀**。
> **原则**(anchor #1+#3+#5):不复造轮·不开新战线·仅解锁 charter §1.3 已有的 H100-gated 5 类(MLS/Frontier-Eng/PostTrain/Inference/RE/EXP)。
>
> **🔴 2026-06-30 接地纠正(SSOT §🔴 6/30 grounded 纠正)**:本清单"1. 部署"段原写"部署 distill-venv"·但 6/30 grounded 实测发现 `docker images 15 张全在且能跑` · "H100 第一刀 = 部署 swebench 镜像"是 6/30 outbound 第 7 推断错·真阻塞不是镜像空。**改**:H100 第一刀改 = 候选 A/B/C 待用户拍(详 SSOT)。

## 现有资产(不重复造轮)

### Code & git
- **本机 nautilus-core** 已 push origin master(`87b7bb33c`):含 SSOT + distill 资产
  - commit `3a03934d4` SWE held-out eval kind-threading
  - commit `210e0fd24` verdict-gate 硬门 wire 进 LOO
  - commit `4892ddafa` is_a_bucket ALE 方向感知
  - commit `b78440d81`/`70948752d` LOO runner + CV aggregator
  - commit `bbd5cfafb` LOO 每折自动清 adapter
- **distill_loo.py + _distill_runtime.py**:本机 git 有· **cloud 没部署**(踩教训5 ship 必验活)

### Memory 索引
- `reference_model_roster_p1_flywheel_20260620`:强模型(qwen3.7-max / GLM5.2 / deepseek4.0pro)+ 弱模型 doubao-seed-2.0-pro
- `reference_fde_t3_candidate_pipeline_20260610`:T3 量产管线 + working LLM config(ARK 端点 `https://ark.cn-beijing.volces.com/api/plan/v3/chat/completions`)
- `session_20260626_swe_aclass_2_confirmed_swe_eval_wired`:SWE eval 已 docker 化(`swebench.harness.run_evaluation --namespace none`)
- `session_20260623_swe_verify_chain_proven_disk_ale_migrated`:ALE 已迁 cloud→GPU 盒 8 核 LIVE(但 GPU 盒是 A 簇 T4 = H100 不到位前的临时)

### Charter 锚点(SSOT 同步)
- §0-GOAL 北极星 forcing function = 证/杀蒸馏
- §1.3 第 3 类 12 benchmark·**5 类 H100-gated** = MLS / Frontier-Eng / PostTrainBench / InferenceBench / RE-Bench(本研究)
- §1.3 A 类口径 = 强解+弱难倒+验证器确认(pass@5 ≤ 0.6 on doubao 2.0)

## 🚧 blocker(明早 1 分钟搞定)
- ⚠️ **cloud pull 失败**(divergent branches:cloud HEAD `7f939c247` 6/6 + 11k uncommitted·本机 master 6/29)
- 解:**手动 merge 或 rebase**(cloud 工作树不能盲覆盖)→ 建议:`cd ~/nautilus-mvp && git stash && git pull origin master && git stash pop`·冲突手工解

## ✅ 明早到位后第一刀(SSOT 锚点 = 蒸馏一条线·GPU 真干活)
按顺序(踩教训5 ship 必验活·每步 curl/SSH 实测再声明):

### 1. 部署(踩教训5 ship 必验活的活样本)
- [ ] cloud merge master(见上)
- [ ] 部署 distill-venv:`python3 -m venv /home/ubuntu/distill-venv && source it && pip install -r requirements`(或复用已有 swe-rsi venv)
- [ ] 验证 `python3 distill_loo.py --help` 跑通(参数 OK·没 import 错)
- [ ] dry-run:mock 3 条 fake record → 验证 CLI/路径/产物文件落位

### 2. anchor ③ 跑 LOO(决策 A·n=4 小样本)· **改=候选 A 推荐**
- ⚠️ **6/30 grounded 后改**:H100 第一刀不再"部署镜像"(已不空)· 见 SSOT §🎯 H100 第一刀候选
- [ ] **候选 A(推荐)**:verify_pathA_one 真跑 n=4 复证(`verify_aclass.py` 强解+doubao 双 arm docker)· 不需 n≥12 · 真 grounded f2p 数据点
- [ ] **候选 B**:LOO n=4 INCONCLUSIVE(`distill_loo.py --records swe_aclass_fuel_verified_20260629_163936.jsonl --kind swe`)· verdict-gate 自动降级
- [ ] **候选 C**:等 V5 H100 上续产到 n≥12 → 真 verdict · 但零数据点
- [ ] canonical 复核 4 道 A-class: django-12113/13220/sklearn-10297/django-13551(`swe_fuel_record_from_verify` 归一化)
- [ ] 借 compass GPU(`flush_pending_nau` runner liveness 已确认 + 真 GPU 烧·本步让 GPU 真干活·烧钱止)

### 3. 解锁 H100-gated 5 类(只在 H100 到位后做·今晚不做)
- [ ] 确认 H100 真实 GPU 显存 + CUDA 版本
- [ ] 在 H100 上重跑 `is_a_bucket` + `distill_loo` 真路径(不再 INCONCLUSIVE·verdict-gate 不降级)
- [ ] V5 在 H100 上产 frontier-eng 等 5 类候选(charter §1.3 已列)
- [ ] soul canonical 复核 → distill 训 → verdict

### 4. 不做(踩教训1+3 反 D·不并行 crank)
- ❌ **不**"部署 + 跑" 同时做(分两步·先部署验活·再跑)·守教训5
- ❌ **不**改 compass internal(自循环空转在 SSOT parking·等 verdict 出后收)
- ❌ **不**重启 FDE cloud runners(FDE 切飞书多维表格·已不在 cloud systemd)
- ❌ **不**开新战线(维②结算腿/MCP 耦合/mint_token/RBAC 全 parking)

## close_loop 判据(SSOT 锚点)
- LOO verdict 出 PROVEN/KILLED/INCONCLUSIVE = **北极星这一圈真答案**
- 真答案出后回头收维②(credit 口径/结算腿/破自循环 1 列+1 判据)

## 风险 + 备份
- H100 不到位:**继续 T4 跑 INCONCLUSIVE 路径**·GPU 烧钱但能续
- 部署 dry-run 失败:**fall back** = 在 GPU 盒本地跑(`/mnt/datadisk0/distill-code/`)+ 跳过 cloud 部署(踩教训5 ship 必验活只在能验的环境做)
- cloud merge 冲突多:**保留 cloud 工作树**·仅在 cloud 旁建分支装 distill_loo·不污染主分支

---
*维护:明早 H100 到位后·逐条 ✓/✗·失败项 ground truth 记回 SSOT。*