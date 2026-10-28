# GenOpt RL ENG 基准测试 · 甲方交付 + 蒸馏收敛 完整规划

> **给 Claude**:本规划分阶段 · 每阶段含负责框 + 文件 + 命令 + 验收判据 + 阻塞。执行时用 executing-plans 逐阶段推进,跨框任务不替对方 autopilot(锚 #1)。

**目标**:把 GenOpt RL ENG 基准测试从当前 57 题 ship / 11 题完全符合,推进到甲方可交付(飞书多维表格 + doubao 难倒验证)+ 规模化(1000 题)+ 蒸馏收敛(北极星中心环闭)。

**架构**:GenOpt 题 = 买方交付物 + 蒸馏燃料同构(一鱼两吃)· 连续 gap_closed 打分替蒸馏二元饱和 · producer 走注册 agent(9000009)· 5 域 adapter pattern(每题 14 文件契约)。

**技术栈**:GPT5.5(qixuw · cloud Linux 直连 / 本机 requests verify=False)· doubao-seed-2-0-pro(ARK · 难倒测试)· evaluate.py verifier(三铁律)· fde_verdicts(cloud backend)· 飞书 bitable(派活表 EOVh)。

---

## 背景:过去两周演进(grounded · 两阶段)

### 阶段一(6/22 - 6/30)· 蒸馏主线「先证或先杀」

| 日期 | 节点 | grounded 结论 |
|---|---|---|
| 6/22 | 北极星确立 | 唯一中心环 = FDE 产难题 → 蒸馏 → 系统两维变强(①模型权重 ②agent 自治)→ 外部 benchmark。forcing function = 先证/先杀蒸馏 |
| 6/23 | over-fit PROVEN | 机制活(ckpt-18 win_rate_vs_base=0.75 · ahc009 distilled 精确等于 strong)· held-out n=6 LOO win_rate=0.0(样本太少非死刑) |
| 6/24 | 三测全弱 | held-out 0.0/0.22/0.18 · 赢题数不随料增长 = 燃料饿非杀 · loo3 里 ahc044/ahc005 泛化成立(distilled 解 base+doubao=0) |
| 6/25 | INCONCLUSIVE + verdict-gate | 信号 0.08-0.22 < 0.6 阈值(非 PROVEN 非 KILLED)· gate 硬门 wire(commit 210e0fd24 · n<12 BLOCK) · 3B@4096 OOM |
| 6/26 | 认 KILL 当前配置 | T4 + 稀缺易料 + 小模型 = 结构性不可证 → pivot 维② · V5 产 2 道 SWE A 类(django-12113/13220) |
| 6/29 | 推翻 KILL | 用户拍用够料重测 · 正确 unblock(n≥12 + 非易料,非 n=2 whipsaw) |
| 6/30 | 纠 7 推断错 | docker 15 张不空 · A 类 grounded n=4(+sklearn-10297/django-13551) |

### 阶段二(7/2 - 7/5)· GenOpt RL 新主线

| 日期 | 节点 | grounded |
|---|---|---|
| 7/2 | T4 关 + A800 替 + H800 到位 + 用户拍 GenOpt RL 1000 题 | GenOpt 连续分数替蒸馏二元饱和 · 一鱼两吃 |
| 7/2-7/3 | 5-6 题 grounded | JobShop Easy 0.68 / TSP Hard 0.10 / Attention Medium→Hard 0.23 / Cache Hard 0.11 / BinPack Easy 0.67 / QAOA 待标定 |
| 7/4 | producer 9000009 注册 + 5/5 verdict persist | wallet 0xfa7b… · external_verified 全 False(等 soul verify) |
| 7/5 | qixuw cert REVOKED 根因 + 本机 runner + ENG 盘点 | cert 2025-09-23 吊销 · Step 4 闭(verdict 落库)· Step 5 阻塞 user_access_token |

### 中心环状态(诚实)
**证/杀蒸馏 = INCONCLUSIVE**(从未达 n≥12)· SWE A 类累计 5 道(V5 2 + compass 3)· 未达 LOO 门。GenOpt 上线 = 新主轴,蒸馏 hold(等 n≥12 或 GenOpt 燃料接蒸馏)。

---

## ENG 现状盘点(grounded · 7/5)

| 指标 | 数 |
|---|---|
| task ship(Dockerfile+Task.md+evaluate.py) | 57 |
| 有 GPT5.5 trajectory | 55 |
| **完全符合(ship 5/5 + frontier_eval 9/9 + GPT5.5 + valid diff)** | **11**(全 OR JobShop · 全 Easy) |
| 含 doubao 难倒验证 + verdict 落库 | 1(jobshop_orlib_v1_001) |
| 难度分布(55 题) | 22 Easy / 11 Medium / 22 Hard |

**5 域覆盖**:OR 33 · KernelEng(Attention)11 · ComputerSys(Cache)11 · Quantum 1 · Robotics 1。

---

## 收敛缺口(8 项 · 决定"完全符合甲方需求"的题从 11 → 1000)

1. **doubao 难倒测试**(buyer §2 第②条 pass@5 ≤ 0.6):只 1/11 完全符合题跑过 doubao
2. **飞书多维表格上传**:0 题入表(Step 5 阻塞 user_access_token · FDE 框)
3. **46 题 ship 件不齐**:Cache/Attention/BinPack/TSP variant frontier_eval 只 4/9
4. **Quantum + Robotics** 域各 1 题未跑 trajectory
5. **1000 题量产**:57/1000 = 5.7%
6. **soul canonical verify**:external_verified 全 False(1 行 UPDATE 没跑 · soul 框)
7. **蒸馏收敛**:GenOpt 连续分数燃料未接蒸馏验证
8. **中心环 INCONCLUSIVE**:证/杀蒸馏未达 n≥12

---

## Phase 0 · 立即可做(不阻塞跨框 · 本框 turf)

### Task 0.1 · 补 10 题 doubao 难倒测试

**目标**:11 题完全符合中,10 题缺 doubao 验证 → 全 11 题达 buyer §2 三条。

**Files**:
- 用现成 `genopt_factory/tools/gpt55_local_runner.py`(已 ship · 支持 `--model doubao-seed-2-0-pro-260215`)
- 10 题 task-dir:`genopt_factory/tasks/operations_research_and_decision_science/JobShop/{ft06,ft10,la01,la16,la21}_v2_v1_001` + `orlib_instance_pack_{a,b,c,d,e}_v1_001`

**Step 1**:本机跑 doubao 难倒测试(ARK endpoint · 无 cert 问题)
```bash
for t in ft06 ft10 la01 la16 la21; do
  ARK_API_KEY=<key> python3 genopt_factory/tools/gpt55_local_runner.py \
    --task-dir genopt_factory/tasks/operations_research_and_decision_science/JobShop/JobShop_${t}_v2_v1_001 \
    --rounds 5 --model doubao-seed-2-0-pro-260215
done
```
**验收**:doubao pass@5 ≤ 0.6(≤3/5 解出)= 难倒成立 = buyer §2 第②条达标。

**阻塞**:无 · ARK 本机已通(HTTP 200)。

### Task 0.2 · Quantum + Robotics 域补 trajectory

**Files**:`genopt_factory/tasks/quantum_information/qaoa_maxcut_v1_001`(已 ship · 缺 trajectory)· `genopt_factory/tasks/robotics_control/pathplan_astar_v1_001`(缺 Dockerfile + trajectory)

**Step 1**:Robotics 补 Dockerfile → **Step 2**:两域各跑 GPT5.5 N=3 → **Step 3**:标定 difficulty。

**验收**:2 域各 ≥1 题有 valid trajectory + difficulty bucket。

**阻塞**:无(GPT5.5 cloud/本机可跑)。

---

## Phase 1 · 解锁跨框阻塞(等各框接球 · 0 autopilot 替)

### Task 1.1 · FDE:user_access_token(阻塞 Step 5)

**根因**:feishu bitable 写需 user 身份 token · tenant_token 是 app 身份 · POST records = 99991661。

**FDE 框需拍 A/B**:
- A · 提供 user_access_token(OAuth `authen/v1/oidc/refresh_access_token`)
- B · feishu app 控制台授权 tenant `bitable:app` 全写

**通后**:平台跑 `genopt_factory/tools/submit_1jobshop_to_feishu.py`(payload 已就绪)→ 11 题入派活表 base `EOVhbQwA0a1HEOsgmxecgkBVnwh` / `tbl69fankpoBhJfw`。

**验收**:飞书派活表出现 11 row(GET records 回读验证)。

### Task 1.2 · soul:canonical verify 1 行 UPDATE(解锁 §4 判据 1')

**根因**:5/5 GenOpt verdict external_verified=False · canonical verify 那 1 行 UPDATE 没跑。

**soul 框需**:走 `verify_pathA_one` / `services/fde_verdict.py` 对 5 verdict 跑 canonical verify → `UPDATE fde_verdicts SET external_verified=true, external_verified_at=now() WHERE verdict_id IN (...)`。

**验收**:5 verdict external_verified=True · control_plane soul_alive 按 MAX(external_verified_at) 转 GREEN。

### Task 1.3 · V5:50 题 batch_driver + 1000 题分派

**V5 框需**:用 `gapclosed_batch_runner.py`(已 commit)跑 50 题扩量(commit da7eebd50 · 5 域 × 10 variant · 已生成未跑 N=3)+ 拍 1000 题 5 域分派(每域 200)。

**验收**:50 题各有 GPT5.5 N=3 trajectory + difficulty · 入 fde_verdicts。

### Task 1.4 · compass:Conductor 扫 inbound(恢复 4 框通信)

**根因**:cloud docs/ 是 push-only · 4 框 scanner 未扫 · compass 34h+ 沉默。

**compass 框需**:Conductor(已活)加配置每 10min 扫 cloud `INBOUND_FROM_{V5,SOUL,FDE,PLATFORM}_*` → ingest_obs 入 Compass。

**验收**:conductor pulse 文件恢复 + inbound surface 4 框。

---

## Phase 2 · 补 ship 件 + 扩域(本框 turf · 可并行 Phase 1)

### Task 2.1 · 46 题补 frontier_eval 9/9

**根因**:Cache/Attention/BinPack/TSP variant frontier_eval 只 4/9(缺 reference.py + baseline/init.py + 5 个 frontier_eval txt)。

**Files**:用 `genopt_factory/tools/produce_task.py`(工厂 · template → K variant)重新派生补齐 9 件。

**验收**:全 55 题 ship 5/5 + frontier_eval 9/9。

### Task 2.2 · 46 题补 doubao 难倒验证

同 Task 0.1 模式 · 批量跑 doubao pass@5。

**验收**:全 55 题达 buyer §2 三条 = 全 55 题"完全符合"。

---

## Phase 3 · 扩量到 1000 题(等 Phase 1/2 稳)

### Task 3.1 · produce_task.py 工厂量产

**目标**:5 域 × 200 题 = 1000。当前 57 → 缺 943。

**Files**:`genopt_factory/tools/produce_task.py` + `gapclosed_batch_runner.py`(H800/cloud worker)。

**验收**:1000 题各有 ship 件 + GPT5.5 trajectory + doubao 验证 + difficulty · 入飞书表。

**阻塞**:算力(A800/cloud/H800 liveness)· GPT5.5 稳定性(cloud 5/5 · qixuw 偶发 502 · 多跑取众数)。

---

## Phase 4 · 蒸馏收敛(北极星中心环 · 一鱼两吃)

### Task 4.1 · GenOpt 连续分数燃料接蒸馏

**目标**:GenOpt trajectory(连续 gap_closed)作蒸馏燃料 → QLoRA 小模型 → 外部 held-out benchmark 对比 base。连续分数破蒸馏二元饱和(ALE 同构)。

**路径**:GenOpt N≥12 题 trajectory → `distill_loo.py --kind genopt`(需扩 kind-threading)→ verdict-gate(n≥12 门)→ 对比 ALE 0.0833。

**验收**:LOO win_rate 或连续分数 delta · 破 0.6 阈值 = 证;平/输 = 诚实杀回护城河副产品。

### Task 4.2 · 或 SWE 续产到 n≥12(备选路径)

V5 续产 SWE A 类(当前 5 道)到 n≥12 → soul verify → distill_loo --kind swe。

**验收**:同 4.1。

---

## 各框分工(grounded · 过去两周实际做了什么 + 问题)

| 框 | turf(CHARTER §4) | 两周进展 | 当前问题/沉默 |
|---|---|---|---|
| **platform-soul(本框)** | infra/dispatch/部署/DB + benchmark verify + 标准 QC | GenOpt 5-6 题 grounded + producer 9000009 + Step 4 闭 + 本机 runner + ENG 盘点 | Step 5 阻塞 user_access_token(FDE turf)· 中心环 hold |
| **V5** | 出题主体 + RSI producer + gateway | 6/26 SWE A 类 2 道 + GenOpt 50 题扩量 + 7 件 ship | 沉默 19h+ · 瓶颈 glm 解出率低(解药 qwen3.7-max)· qwen daemon 6/24 dormant |
| **compass** | 记忆/PoI/env/eval + feishu 读写 | MCP durable v2.3.1 + PoI 飞轮 + 3 道 SWE A 类 verify | 沉默 34h+ · 7/4 越界撤回(commit c97567a · anchor #6 第 5 周复发)· 等 Conductor 扫 inbound |
| **soul-verify** | canonical verify + 难度门 + verdict-gate | verify_pathA_one 复核 V5 2 道 A 类 + SWE eval kind-threading | 全程 0 接 · 5/5 verdict external_verified=False 那 1 行 UPDATE 没跑 |
| **FDE** | 飞书业务派活 S1/S2/S3 | S1/S2/S3 引擎 binding-DONE(6/11-6/14) | 全程 0 接 · Step 5 user_access_token 阻塞 · daemon 装好没启 |

---

## 里程碑 + 验收判据

| 里程碑 | 判据(外部可证) | 依赖 |
|---|---|---|
| **M1 · 11 题完全符合甲方** | 11 题各:ship 5/5 + frontier_eval 9/9 + GPT5.5 valid + **doubao pass@5 ≤ 0.6** | Task 0.1(本框可做) |
| **M2 · 11 题入飞书多维表格** | 派活表出现 11 row(GET 回读) | Task 1.1(FDE user_access_token) |
| **M3 · 55 题完全符合** | 全 55 题达 buyer §2 三条 | Task 2.1 + 2.2 |
| **M4 · 5 域覆盖** | Quantum + Robotics 各 ≥1 题 valid | Task 0.2 |
| **M5 · 1000 题量产** | 1000 题入飞书表 + trajectory + doubao | Task 3.1(算力) |
| **M6 · 蒸馏收敛(北极星)** | LOO 破 0.6 = 证 / 平输 = 诚实杀 | Task 4.1/4.2(n≥12) |

---

## 阻塞 + 依赖矩阵

| 阻塞 | 影响里程碑 | 负责框 | 解 |
|---|---|---|---|
| user_access_token | M2, M5 | FDE | 拍 A(OAuth token)/ B(app 授权) |
| soul canonical verify | §4 判据 1' | soul-verify | 1 行 UPDATE |
| V5 SWE n≥12 | M6 | V5 | 续产非易料 |
| GPT5.5 qixuw 偶发 502 | M1, M3, M5 | 平台(已解) | cloud 5/5 · 多跑取众数 |
| 算力(A800/cloud/H800) | M5, M6 | 用户 | 充值/租赁 |
| Conductor 扫 inbound | 4 框通信 | compass | 加配置 |

---

## 立即行动(下一步 · 本框可做不阻塞)

1. **Task 0.1**:本机跑 10 题 doubao 难倒测试(ARK 已通)→ M1 达成 11 题完全符合
2. **Task 0.2**:Quantum + Robotics 补 trajectory → M4
3. 等 FDE 拍 user_access_token → M2(11 题入表)
4. 等 soul 跑 canonical verify → 解锁 §4 判据 1'

**守护栏**:0 autopilot 替 4 框 · SSOT 改动先广播 · ship 前 grep 真字 · 反 D(ship 件数 ≠ 价值 · 中心环闭才算进展)。
