# Nautilus 总纲 · 历史·现状·目标·统一方案(2026-06-22)

> 一份全面完整准确的总纲。整合:① 历史与经验教训 ② 各对话框最新真实状态 ③ 目标(北极星)④ 统一执行方案 ⑤ 诚实风险判据。
> 配套详档:`PLATFORM_HISTORY_AND_ARCHITECTURE_REVIEW_20260622.md`(历史)· `NORTH_STAR_20260622.md`(目标)· `plans/2026-06-22-central-loop-distillation-poc.md`(执行计划)· `FDE_BUSINESS_CHARTER.md §0`(铁律)。

---

## 第一部分 · 历史与经验教训(grounding:git 1268 commits + memory + 真账)

### 四个时代
1. **MVP+链上**(2月):模块化架构·NMACS·PoW+MEME token·CrewAI·nautilus.social。
2. **Agent-First 经济+生存**(3月):自助注册(无人类·钱包·链上身份)·生存机制·能力进化·Marketplace·Base 合约+NAU。**平台成为 agent 经济生态。**
3. **多 agent mesh+自进化**(4-5月):A2A 全 mesh·KAIROS/MiniMax daemon·DMAS(RAID 共识)·soul split·自改引擎(reviewer→council→ship→PR)·Path B OSS 定位·递归飞轮点火。
4. **FDE 业务引擎+RSI 飞轮**(6月):verdict-bus·FDE S1-S5·RSI 飞轮(mint→produce→verify→settle)·蒸馏破墙·compass 跨框协调·服务真甲方。

### 🔴 核心经验教训(复发 5-6 周 · 这是历史最大的价值)
**反复在"内部自循环 / 加平台功能 / 造并行轮子"花力气,而非"闭一个真外部价值环"。**
- 真账(5/18):460 件 real bucket 中 **94% 自循环·2.6% 真外部·真客户付款 0/30d**。
- 用户多次纠正(4-14 宪法·5-18 真账·5-27 工作流锁·6-14 狗熊掰玉米·6-22 对话框纠正),**每次点头每次 <1 周复发**。
- RSI 方向连环证伪(每步诚实负结论):内部 NAU 自指→ensemble→Probe3 自改→grounded-retrieval(整类撞天花板)→**蒸馏破墙(现行)**。
- **6/14 硬道理**:推理时方法有数学天花板=base 单次成功率;**唯蒸馏(灌分布外新模式进权重)破能力墙**。

---

## 第二部分 · 当前真实状态(代码 + 各框 grounding)

### 平台架构真相
平台 = **producer-agnostic 的 HTTP 基底**(FDE dispatch + verdict-bus + 三 poller)。真 producer **不在本 repo**,是外部部署的 agent/daemon 经 HTTP claim 接入。两套基底都 LIVE 但**没插在一起**:
- 自主-agent 经济(注册/钱包/生存/能力进化/marketplace/A2A)= 全 LIVE。
- RSI/FDE 飞轮(dispatch/verdict/poller/蒸馏分拣)= 全 LIVE。

### 🔴🔴 最大真相:因果环从没闭过
内外飞轮是**概念/管道合并,不是因果/运行时耦合**。把"转"变成"变强"的那一步——**蒸馏(用业务燃料训出可证更强模型)一次没真跑过**。6/20 闭的"复利"是 grounded-retrieval 类(撞天花板那类)。中心环开着。

### 各对话框最新状态(grounding · 以各框自报为准)
| 框 | 身份 | 最新进展 | 当前球 |
|---|---|---|---|
| **platform-soul(我)** | nautilus-core 后台引擎·RSI verify/mint·FDE 引擎 | SWE 管线全通(格式C/磁盘)· FDE B2 cutover LIVE+最后一跳 PROVEN · 能力回写(string-keyed·已标非依赖)· 北极星+总纲固化 | 中心环执行:A 类 minting 装配(本地可 TDD)· LINK string→integer · 等 cloud 白名单 |
| **V5** | qwen daemon **nautilus-prime-001=注册 agent 9000002**(真钱包·24/7 服务·非对话框) | W2 recall 接进 SWE produce LIVE(线A)· path b 部署(daemon=唯一 SWE producer)· token bump · 实测纠正"prime 已注册·要 LINK 不 register" | producer 正确性方差(真瓶颈·reward 饱和 87%·没证过 uplift)· 能力读端(cnt due 6/24)· daemon 可暴露 9000002 供 LINK |
| **compass** | 记忆/recall/PoI/governance · FDE benchmark env/verifier | recall union 修复 LIVE · 7 bogus verdict 作废 · 网络非 blocker 纠正 · autolab abandoned | Verified env-build(SWE 第2题池)· 3 bug held(score0→pass/autolab硬化/recall) · benchmark env/eval turf |
| **FDE** | 前台管理体系 nautilus-FDE(v0.9.6) · 同租户不同 app | canonical RGDK 定 · 派活表建 · 飞轮1跳通 · S1-S5 集成~done | 待 PM 填真买方待派单行 · 三类业务难倒题=A类燃料来源(打 A/B/C 标) |

---

## 第三部分 · 目标(北极星 · 用户 2026-06-22 确认)

### 唯一要闭的中心环
```
FDE 产难题(强模型解 + 弱模型难倒 = A 类燃料)
   → 当蒸馏燃料 → 系统可证变强(两维度·缺一不可):
        ① 模型权重变强(蒸馏破能力墙)
        ② agent 群体自治变强(注册自主 agent + survival/能力进化/marketplace/A2A 真接进飞轮)
   → 更强系统产更难/更值钱题 → 每圈外部 benchmark 证明 → 循环
```

### 🔪 分叉过滤器(每件提案必过)
"这件**直接推进中心环因果链**(产 A 类燃料/跑蒸馏/证提升/接 agent 自治)吗?"**0 贡献 = 默认不做(parking lot)。**

---

## 第四部分 · 统一执行方案

### 4.1 燃料供给 = 充足(非稀缺 · 6/22 纠正)· 🎯 ALE = 首选 workhorse
甲方 **12 类基准**(MLS/Frontier-Eng/ResearchGym/PostTrain/Inference/**FrontierSWE**/MLRC/RE-Bench/**KernelBench**/EXP/**AutoLab**/**ALE-Bench**)= 大量精准匹配供给。"弱模型难倒"半=买方口径自带(pass@5≤0.6 on doubao)·基准自带验证器。A 类 = 在供给上跑「强模型先解+验证」minting pass = **一鱼两吃**(买方交付物+蒸馏燃料)。

🎯🎯 **ALE-Bench(arXiv 2506.09050)= 中心环首选 workhorse(2026-06-22)**:连续打分优化题(AtCoder Heuristic·无精确解·长时程迭代)。**为何优于二元 SWE**:① 连续分数=**不饱和**(直解 V5 reward 饱和 87% 瓶颈)② 原生迭代 RSI 有真 headroom(修正 6/14 天花板=只对二元任务成立)③ 蒸馏测量=连续分数 delta(比二元 pass@k 干净)④ infra 轻(跑解算分非 docker 仓)。A 类(ALE)= 强模型分 ≫ doubao 分(连续阈值·非二元)。
- **T4 可产**:**ALE-Bench(首选·infra 轻·不饱和)** / FrontierSWE(次·二元但已证 path B)/ AutoLab / KernelBench。**H100-gated**(王泽):MLS/Frontier-Eng/PostTrain/Inference/RE/EXP。
- 诚实:A 类产率=强模型解出率/分数优势;真前沿(RE/MLRC)强模型也败=多落 B 类(护城河非燃料)。

### 4.2 中心环 forcing function(唯一进展判据)
**先证或先杀「蒸馏那一步」**。计划 = `plans/2026-06-22-central-loop-distillation-poc.md`:
- **Phase 1**(本地可 TDD·现在能做):A 类 trace 判定+数据集装配+FrontierSWE minting 编排(复用 fde_double_gate/triage/swe_verify·不另造)。
- **Phase 2**:攒到可蒸批量(~50-200 信号·1K 理想)·不够不硬训。
- **Phase 3**:QLoRA SFT Qwen2.5-Coder-7B on T4(genuinely new)。
- **Phase 4**:held-out 外部 benchmark·蒸馏 vs base vs doubao。
- **Phase 5**:赢=放大;平/输=诚实杀假设回护城河副产品。

### 4.3 agent 自治端(并行小切片·非焦点)
**LINK 不 register**(V5 实测:prime 已是注册 9000002):平台 verdict→capability 回写时把 `claimed_by` 字符串别名到整数 agent_id(prime→9000002/kairos→9000003/v7→9000004),走现成 `capability_evolution`(整数键·接生存/市场)。今天 string-keyed 回写标非依赖·淘汰。

### 4.4 各框分工(都服务中心环)
- **soul(我)**:A 类 minting 装配 + 数据集 + LINK + 编排 + held-out eval harness。
- **V5**:强模型 producer(产 A 类候选解)+ daemon 暴露 9000002 + producer 可靠性。
- **compass**:benchmark env/verifier(GPU eval)+ Verified env-build(扩 FrontierSWE 实例池)+ A/B/C 分拣 verifier。
- **FDE**:三类业务难倒题产出时打 A/B/C 标(难倒题=A 类燃料来源)+ 真买方流量。
- **用户**:cloud/GPU 白名单恢复 · 算力协调(H100 王泽)· 北极星拍板已给。

### 4.5 收敛纪律(治"一直分叉")
1. **冻结**:S3 timer/双门 timer/看板/path2/W2 uplift 见证(grounded-retrieval 类≠破墙)= parking lot。
2. binding-DONE + 冻结 scope + forcing function(非自律)。
3. 跨框走 _OUTBOUND/_COORDINATION + contract close_loop 带 due。
4. 总纲为单一真相源·变更走本文件+宪章 §0·不另起炉灶。

---

## 第五部分 · 诚实风险与判据

- **最大风险**:A 类产率可能不足(强模型在 FrontierSWE 解出率有限)→ 攒不到可蒸批量。缓解:多基准源(AutoLab/KernelBench)+ Verified env 扩池;真不够则诚实记"燃料不足"先补。
- **可证伪判据**:蒸馏 7B held-out pass@k **显著 > base 7B** = 飞轮成立。平=诚实杀,不假装自我提升。
- **不退回的死路**:推理时自指方法(grounded-retrieval/ensemble/self-edit)已证伪整类·不重投。
- **不造 facade**:auto-mint 保持 OFF 直到干净复利证明;负结论 ABORT 不硬撑。

---

## 一句话总纲
**我们建好了两套完整基底(自主 agent 经济 + RSI/FDE 飞轮)却从没把它们的因果环闭上——蒸馏那一步一次没真跑。甲方 11 类基准是充足的 A 类燃料供给。下一步唯一要做的:在 FrontierSWE 上产 A 类燃料→QLoRA 蒸馏→外部 benchmark 证或杀。出结果前,其它全冻结。**
