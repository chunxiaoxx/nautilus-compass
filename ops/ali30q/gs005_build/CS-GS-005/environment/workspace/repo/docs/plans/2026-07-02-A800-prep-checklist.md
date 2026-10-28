# A800 租赁准备清单(2026-07-02 写 · 替代原 H100 清单)

> **背景**:用户 2026-07-02 拍 · T4 GPU (43.166.8.20) 主动关闭 · 正在租赁 A800 替代 H100(原 6/29 决定租 H100/H800 · 因 T4 关闭 + H100 缺货改 A800)· 本文件 supersede 原 `docs/plans/2026-06-30-H100-prep-checklist.md`。
> **原则**(anchor #1+#3+#5):不复造轮·不开新战线·仅解锁 charter §1.3 已有的 H100-gated 5 类(MLS/Frontier-Eng/PostTrain/Inference/RE/EXP)· A800 = Ampere 80GB · 同样能跑 SWE/ALE/Frontier-Eng。
> **SSOT 锚点** = 蒸馏一条线 · A800 第一刀 = 候选 A (verify_pathA_one n=4 复证 · 用户 7/2 拍锁定)。

## 现有资产(不重复造轮)

### Code & git(原 T4 /home/ubuntu/ 上的需迁移到 A800)
- **distill_loo.py + _distill_runtime.py**:本机 git 有· cloud 已部署(soul-distill-deploy worktree · dry-run 已验)
- **GPU 端灵魂 verify 工具**(原 T4 /home/ubuntu/):
  - `verify_aclass.py`(1115B · 6/26 20:43)
  - `verify_pathA_one.py`(1017B · 6/24)
  - `verify_pathA_one.py.bak_soul0626`(备份)
  - ⚠️ **A800 到位后需迁移或重写** · T4 已关
- **A-class n=4 真 grounded**(6/29/30 实证):
  - django-12113/13220(6/26 strong + doubao 0/2)
  - sklearn-10297(6/29 strong 3 次 + doubao 1/1 error)
  - django-13551(6/29 strong 2 次 + doubao 1/1 unresolved)
  - sympy-20049(候选 · doubao 数据缺)

### docker images(T4 上 15 张已确认能跑)
- 7 swebench env + 1 base + 4 ale + 1 rust + ubuntu = **15 张全在能跑**
- ⚠️ **A800 全新机器 = 无镜像** · 需重新拉 swebench + ale(SSOT 教训5 ship 必验活)
- 拉镜像体积大 · 触发 daemon · 守教训 #1+3+5

### Memory 索引
- `reference_model_roster_p1_flywheel_20260620`:强模型(qwen3.7-max / GLM5.2 / deepseek4.0pro)+ 弱模型 doubao-seed-2.0-pro
- `reference_fde_t3_candidate_pipeline_20260610`:T3 量产管线 + working LLM config(ARK 端点)
- `session_20260626_swe_aclass_2_confirmed_swe_eval_wired`:SWE eval 已 docker 化
- `session_20260630_grounded_correction_7_docker_not_empty`(推断错 #7 纠正)

## 🚧 blocker(A800 到位前的预期问题)

- ⚠️ **A800 全新机器 = 0 资产**:docker images 空 · verify_aclass.py 不在 · distill_venv 不在 · 都需要重新部署
- ⚠️ **T4 (43.166.8.20) 已关** · ssh gpu 不通(7/2 ping 100% loss · SSH timeout)
- ⚠️ **A800 租赁中** · 等用户给 IP/SSH config/就位确认
- ⚠️ **cloud 仍可用**(43.160.239.61)· distill-deploy worktree + swe_aclass_fuel.jsonl 在

## ✅ A800 到位后第一刀(SSOT 锚点 = 候选 A 锁定 · 用户 7/2 拍)

### 1. 部署(踩教训5 ship 必验活的活样本)
- [ ] A800 拿到 IP + SSH config(用户拍)
- [ ] 探 `nvidia-smi` 确认 A800 + 显存 + CUDA
- [ ] **拉 swebench docker 镜像**(这次是真的 · 不是推断错 · docker images 会空)
  - 体积大 · 触发 daemon · 注意时点(避免跑 daemon 时拉)
- [ ] 部署 distill-venv:`python3 -m venv /mnt/datadisk0/distill-venv && pip install -r requirements`
- [ ] 迁移/重写 `verify_aclass.py` + `verify_pathA_one.py`(从 T4 复制逻辑)
- [ ] 验证 `python3 distill_loo.py --help` 跑通
- [ ] dry-run:mock 3 条 fake record → 验证 CLI/路径/产物文件落位

### 2. A800 第一刀 · 候选 A(用户 7/2 锁定)
- [ ] canonical 复核 n=4 A-class(强解+doubao 双 arm docker)
  - `verify_aclass.py <task_id> <records>` 真跑 django-12113/13220/sklearn-10297/django-13551
  - 预计 30-60 分钟/题 · 总 2-4 小时
- [ ] 拿 f2p 真数据点(强解 f2p + doubao 难倒 = A 真)
- [ ] **不需 n≥12 gate** · 候选 A 不跑 LOO
- [ ] 同时验证 V5 SWE producer 真干净(RADIX-style 真赢信号)
- [ ] 出 f2p 真数据 → 备 LOO n=12 用

### 3. 解锁 H100-gated 5 类(只在 A800 稳后做 · 候选 A 完后)
- [ ] 确认 A800 真 GPU 显存(80GB?) + CUDA 版本
- [ ] 在 A800 上重跑 `is_a_bucket` + `distill_loo` 真路径(不再 INCONCLUSIVE)
- [ ] V5 在 A800 上产 frontier-eng 等 5 类候选(charter §1.3)
- [ ] soul canonical 复核 → distill 训 → verdict

### 4. 不做(踩教训1+3 反 D · 不并行 crank)
- ❌ **不**"部署 + 跑" 同时做(分两步 · 先部署验活 · 再跑) · 守教训5
- ❌ **不**改 compass internal(自循环空转在 SSOT parking · 破自循环通道预备 = 加 1 列 + 1 判据 + 1 行 UPDATE)
- ❌ **不**重启 FDE cloud runners(FDE 切飞书多维表格 · 已不在 cloud systemd)
- ❌ **不**开新战线(维②结算腿/MCP 耦合/mint_token/RBAC 全 parking)
- ❌ **不**擅自动 V5 daemon(等用户拍后)
- ❌ **不**在没验活前声称"A800 就位"(必须 nvidia-smi + docker images + verify tools 三件齐才能说就位)

## close_loop 判据(SSOT 锚点)
- A800 跑出 n=4 f2p 真数据 = **北极星这一圈真答案的子集**
- 真 verdict 出 PROVEN/KILLED/INCONCLUSIVE = **北极星这一圈真答案**
- 真答案出后回头收维②(credit 口径/结算腿/破自循环 1 列+1 判据)

## 🛠️ 破自循环通道预备(SSOT §🛠️ · 用户 7/2 拍 · 实施 pending)

- 加 1 列:`fde_verdicts.external_verified bool`(默认 false · 仅 soul canonical verify 标 True)+ `external_verified_at timestamptz`
- 改 1 判据:`control_plane.soul_alive` 按 `MAX(external_verified_at)` 新鲜度算(非 cycle stale_hours)
- 复用现有 soul canonical verify 加 1 行 UPDATE
- **不改 compass 内部逻辑**(auto-mint / bench_eval 继续跑 · 不动)
- **不写新服务 / 不写新 runner / 不写新 webhook**
- 实施需要:cloud postgres 访问 + 找 verify 脚本在 cloud/A800 位置

## 风险 + 备份

- A800 不到位:**继续 parking** · SSOT 不动
- A800 拉镜像失败:**fall back** = 在 cloud 本地跑(cloud 有 distill-deploy worktree)· 但 cloud 无 swebench 镜像 = 失败 · 备 = 跑 ALE-Bench(cloud 有 ale 镜像)
- 部署 dry-run 失败:**fall back** = 复制 T4 上的 verify_aclass.py 源码逻辑(从 git history 取)· 不盲信 T4 已关
- A800 算力不够:不跑全 4 题 · 先跑 1-2 题拿数据点 · 增量跑

---

## 关联 · 历史

- `docs/plans/2026-06-30-H100-prep-checklist.md` · 原 H100 清单(superseded by 本文件)
- `LOOP_STATE_SSOT.md`(commit `1d5d74e35` + 7/2 A800 更新)· `FDE_BUSINESS_CHARTER.md` §0-GOAL 北极星 + §1.3 12 benchmark
- `_OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260630_correction_7_docker_not_empty_v2.md`(commit `4968f12d1`)· `_OUTBOUND_FROM_PLATFORM_SOUL_TO_{V5,COMPASS,FDE,PLATFORM_SOUL}_20260701.md`(commit `f29cbbdf3`)
- `session_20260630_grounded_correction_7_docker_not_empty.md` · `session_20260701_cross_dialog_sync.md`

---

*维护:A800 到位后 · 逐条 ✓/✗ · 失败项 ground truth 记回 SSOT。*
*签:platform-soul dialog · 2026-07-02 · 替代 H100 清单 · A800 第一刀候选 A 锁定*