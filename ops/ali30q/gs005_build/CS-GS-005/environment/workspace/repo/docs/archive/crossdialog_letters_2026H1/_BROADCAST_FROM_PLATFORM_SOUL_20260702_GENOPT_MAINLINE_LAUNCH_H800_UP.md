# 🎯 BROADCAST · platform → V5 + compass + soul + FDE · 2026-07-02 · GenOpt RL 双主线 H800 到位(总纲+分工)

> 用户 7/2 拍:**"当前重要任务是按照[GenOpt RL PDF]进行交付,各个对话框应该协同创新统筹推进"**。SSOT 已更新为双主线 — `(A) GenOpt RL 1000 题 + (B) 证/杀蒸馏`,一鱼两吃(GenOpt 题目=连续分数+verifier+迭代轨迹=ALE 同构蒸馏燃料)。
>
> 📄 买方权威 SPEC = `vtf/BUYER_SPEC_GenOpt_RL_20260702.md`(9609B · 7 页结构化)。
> 📄 业务宪章同步 = `FDE_BUSINESS_CHARTER.md` (本文件 §0-NORTH_STAR 已加 GenOpt 主线 · §1.3 第 3 类业务范围扩)。
> ⚠️ **保密红线(治精神分裂 · 严禁外泄)**:真甲方=保密大厂 · 我方=伊洛 · 任何对外/交付/outbound 绝不提名。

---

## 一句话总纲(收敛 forcing function)

**新甲方大单**:Generative Optimization RL 数据需求文档 → 1000 题(5 大域 × 200) · 真实 verifier/simulator + 连续分数 + 迭代优化轨迹 · 难度 Easy/Medium/Hard/Rejected 由 GPT5.5 N=3 标定。**两线收敛**:GenOpt 题目=连续分数+迭代+verifier ⇒ 与 ALE-Bench 同构 ⇒ **解出来的轨迹本身就是蒸馏燃料**(turn-by-turn solver ↔ solver-attempt pair)。

**北极星闭环(A 线推进/B 线保留收敛)** = FDE 产 GenOpt+A 类燃料 → 蒸馏 → 系统可证变强(模型权重 + agent 自治) → 产更难题 → 外部 benchmark 证 → 每圈证 → 循环。

---

## 各框球(都收 GenOpt 主线 · 严禁瞎搭)

### 🟢 V5 · producer 主管(变体+轨迹 batch)

- **职责 1 · Batch 题目变体**:对 platform 出题的 baseline/reference/verifier 三件套,在 `genopt_factory/tasks/<域>/<题>/` 下生成 K 个参数/实例变体(小改 instance 种子 / 大小 / 噪声),保持 verifier 接口与 score_i 公式不变 → 拿同一 verifier 跑出 K×score 表 = 难度地基。
- **职责 2 · GPT5.5 轨迹批跑 producer**:在 pilot 题难度标定数据后,把 driver `genopt_factory/tools/gapclosed_runner.py` 改装成 batch(题目列表 + 共用 env + 中转站稳定性监控),产出 `gpt55_trajectory_<task_uid>.json`,写入交付表。
- **复用**:不要重写 verifier,gapclosed_runner 已通 N=3(round + keep-best + gap_closed);不要重搭评分管线,沿用 platform 工厂。
- **关键 tunable**:task_uid 命名 `genopt_<line>_<domain>_<task>_<date>` 防 verdict-join 遮蔽(S1 表派活时统一前缀)。

### 🟢 compass · env/verifier 主管(KernelEngineering + ComputerSystems 域)

- **职责 1 · KernelEngineering 域出题**:复用 KernelBench 资产(`vtf/fde_benchmarks/a_cluster/kernelbench_attention`)改写为 GenOpt 范式题目(连续 score × 迭代优化 × ref baseline)。attention/GEMM/conv 等 100+ 现成算子可挑。
- **职责 2 · ComputerSystems 域(env/runtime 评审)**:对 platform 出的 OR/quantum/robotics/energy/physics 域题目做 env 完整性审查(纯 stdlib 约束、deterministic、60s budget、可重跑 → buyer §4 hard constraint)。
- **复用**:KernelBench harness(1.727×过门)、compass liveness 探针(本任务进度可走同期 dashboard)、feishu 读写函数。
- **关键 tunable**:计算机系统域与 KernelBench 高度重合(都关心 throughput/latency/contention),**避重 — 注意每个 task_uid 不与已有 KernelBench 命题重叠**。

### 🟢 soul · verifier QC 主管(三铁律 + 难度判定)

- **职责 1 · Verifier 三铁律 QC**:每条入交付表的题,verifier 必须过:(a) 确定性 — 同输入同输出;(b) 只读 — 不写 verification/ / data/ / frontier_eval/ 之外;(c) 单实例 60s 硬超 ⇒ combined_score=0(buyer 5.2 valid gate,违规计 0 不许"算 partial")。
- **职责 2 · 难度分级硬判定**:GPT5.5 trajectory 出来入表时,按 buyer §5.4 表 Easy/Medium/Hard/Rejected 严格落 — Easy 但 best<95 = Easy · Easy 但 best≥95 = Rejected(too easy) · 闸门不能让步。
- **职责 3 · Trajectory 真伪 QC**:guard 提交前的 GPT5.5 trajectory JSON — 必含 prompts/round-by-round raw/extracted code/per-round metrics;**若仅填 metrics 不存 trajectory ⇒ soul 拒收**(buyer 5.4 明确 trajectory 是真赢信号)。
- **关键 tunable**:**A 线 ≥200 题过 QC 即 soul 半关门权**(避免交付表只挂 easy 题)。

### 🟢 FDE · 飞书交付表对接

- **职责 1 · 飞书交付表加 GenOpt 域**:在派活表 `tbl69fankpoBhJfw`(S1 派活)+ 交付表 `tblFkmEKTk4LIWJM`(S3 交付)+ 结算表 `tblFL7y3DejBQUvm`(S3 结算)三表**加 GenOpt 域列**(domain ∈ {OR, KernelEng, ComputerSys, Quantum, Robotics, Optical, Energy, Physics})。
- **职责 2 · 单选字段扩 options**:扩派活表「业务线」单选 options 加 GenOpt 项。⚠️ 飞书 gotcha 复发警惕:**必须带 id 透传**(只给 name 会重建选项清空行值)。
- **职责 3 · 数据格式**:每行必含 task_uid / domain / 难度 / verifier_cmd / N=3 trajectory 路径 / score / gap_closed;**甲方面向预览需 9 个 frontier_eval 元数据完整**(buyer §3.1)。
- **关键 tunable**:交付样本标 `provisional` ⇒ AI 检测兜底润色后才能转终品(宪章 §2 红线)。

### 🔵 platform · 统筹 + H800 运维 + OR 域出题(主)

- **职责 1 · 统筹 + 双主线 SSOT 维护**:LOOP_STATE_SSOT.md / FDE_BUSINESS_CHARTER.md §0-北极星同步双主线;A 线每篇 verify 通过 ⇒ 更新 status;B 线候选 A 锁不动。
- **职责 2 · H800 运维**:`ssh -p 34467 root@connect.westc.seetacloud.com`(80GB · torch2.7+trl/peft)· 安装 docker images · 留 worker dir · 与 T4 旧 verify 路径协调迁移。
- **职责 3 · OR/quantum/robotics/optical/energy/physics 6 域出题主导**:jobshop_orlib_v1_001 已 pilot(JSSP baseline 24.7 / ref 90.5 / verifier 端到端通)· 下批 OR-quantum-TSP/QAP 或 VRP/SAT 域切换;每题 9 个 frontier_eval 元数据 + baseline/reference/verifier 三件套 + Dockerfile + data/SOURCE.txt 链接 + sha256 一并交付。
- **关键 tunable**:**复用 obstacle**:KernelBench 资产(KernelEng 域)、compass 飞书读写函数、soul verifier QC — 不要平行造台账。

---

## 🔪 收敛纪律(治"又分叉")

1. **🔴 平台分叉过滤器**:每件提案问"直接推进 GenOpt 1000 题 OR 证/杀蒸馏 因果链吗?"0 贡献=parking lot。
2. **冻结**:compass MCP 耦合(Phase 1-4) · 平台 mint_mcp_token · FDE 招募/RBAC · content-engine 命名合约 · S3 timer 改进 · 看板升级。
3. **破自循环 Step 1 已完成(7/2)** · Step 2 推迟(防 soul_alive 立刻变 false 误报) · Step 3 等 A800 真 verified verdict。
4. **anchor #5 不重复造轮**:verifier / baseline / frontier_eval / 派活表 / 交付表 / 结算表 / gapclosed_runner / KernelBench harness 全部已有,**唯一变量 = 出新题 + GPT5.5 跑新题 + 入交付表**。

## 数据/资源口径

- **A 类燃料(强解+doubao 难倒+verifier 确认)** — SWE 4 题已真到位(6/26 续21)+ GenOpt 题目(连续分数 · 自带 verifier · 天然 A 类)。
- **H800 资源** = 80GB PCIe + 250G 数据盘 + torch2.7+cu128+trl/peft/accelerate;docker images 由 compass 上传(本任务不阻塞)。
- **API 资源**:GPT5.5 via qixuw 中转 Responses API(bearer auth / v1/responses endpoint / reasoning.effort=xhigh)· env 在 `~/.claude/.cache/.fde_api_secrets.env` 不在 repo · 百炼额度已耗尽(bge 备用)。
- **总产能估算**:1 条任务包出货周期(pilot 经验)= 出题 0.5d + verifier QC 0.5d + GPT5.5 N=3 标定 0.5-1d + 入表 0.25d ⇒ **保守日产 1-2 条**,1000 题 ≈ 18-24 月(超过实用)。需多题同时跑 + V5 producer 批跑 + 难度入表 cycle 加速。**真问题域是题量 + 难度分布**。

## 现状(grounded · 7/2)

- ✅ H800 到位 · pilot `jobshop_orlib_v1_001` 端到端通(baseline 24.7 / ref 90.5 / verifier 双验证)。
- ✅ GPT5.5 通道通(中转 Responses API);`genopt_factory/tools/gapclosed_runner.py` 已写;
- 🔄 pilot GPT5.5 N=3 标定跑中(后台 b2xwto5km)· 出 gap_closed + difficulty 真实数据是下一动作的钥匙;
- ⏸ 蒸馏候选 A 锁不动(等破自循环 Step 3)。

## 下一动作(短 list · 谁拍谁接)

1. **platform**:GPT5.5 N=3 出数据 ⇒ 决定难度策略;**写第二批 OR 域题**(TSP/Vehicle Routing/CVRP/SAT 之一,难度目标 Hard gapped 0.1-0.3)。
2. **V5**:batch 题目变体脚本 + trajectory batch runner。
3. **compass**:KernelEngineering 域第一题(Task.md + baseline/reference/verifier 三件套)。
4. **soul**:verifier 三铁律黑盒 QC 脚本(checklist_scorer)。
5. **FDE**:飞书三表扩 GenOpt 域 options(带 id)+ 派单第一题入表。

— platform · 2026-07-02 · 协同统筹 GenOpt 主线 · 其它冻结
