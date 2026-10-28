# 🎯 /goal · FRESH SESSION 启动(三框联动)· 2026-06-24 · 蒸馏弱KILL→转燃料供给侧(agent自治5断点)+ 蒸馏第4测条件

> 接 6/23-24 超长session(蒸馏首次真跑3测全弱KILL)。本文=下个session无缝接·三框各自的球钉死。SSOT细节:`docs/FRESH_SESSION_PROMPT_20260623_distillation_generalization_next.md §0.6` + memory `session_20260624_distill_3tests_weak_kill_fuel_starved_pivot_autonomy`。

## 0. 一句话现状 + 战略重定性(用户拍板)
- **蒸馏(中心环最硬一步·从没真训过)第一次端到端真跑完**:三测 confound-clean = 0.0(n6)→0.22(n9)→0.18(n11)·**绝对解出题数卡 2·扩料9→11无正梯度**·机制活(distilled解出base解不了的)但泛化弱·KILLED at 0.6门槛。
- **🔴 诊断收窄(V5 6/24 grounded更正·排除法)**:① **不是容量**——7B那次是seq2048截断confound(7B对长题看到零解token·KILLED是artifact)·**容量根本没干净测**(干净测需7B@4096=H800)② **不是recipe**——completion掩码+r64+MLP已修·第3测train_loss 0.83→0.5生效·**第3测是clean真负**③ **不是机制死**——over-fit PROVEN ④ ✅ **剩:料的同质性/可迁移性**——11道独立ALE题各自启发式·蒸馏学不到跨题可迁移结构→泛化弱(valid卡~0.2·绝对2题·扩料9→11无梯度)。
- **重定性(用户同意)= 非杀非花钱(H800暂不上)·机制活·泛化弱** → 两条并行验证路:**(A)转SWE测同质性假设**(bug-fix同质·可能少样本泛化·区别ALE每题独立)**(B)攻燃料供给侧=北极星第②维agent自治**(修5断点让更多agent产燃料)。SWE弱→更可能"小样本蒸馏需几百条料"→诚实退护城河。

## 1. 🔴 三框联动(各自的球·别越界别重复)
### platform-soul(本框·DB/infra turf)
- **主修 V5 审计的 5 断点**(下方§2)·从 #1 A2A(物理前提)入手。
- 蒸馏第4测的执行端(料够/H800到时跑·命令见§3)。
- 协调中枢:收 V5/compass 入站·写 outbound·维护 SSOT。

### V5(producer turf)
- **ALE 续跑慢凑 A 类**(给第4测/7B备料·glm超时限·捡能救的)。
- **#4 的 V5 侧**:atoms reinforce 接线(boost_on_access·recall命中强化·plan `nautilus-v5/docs/plans/2026-06-24-feedback-loop-systemic-repair.md`)。
- 不复活已杀的僵死daemon·SWE producer待soul specs(若转SWE路)。

### compass(memory/recall turf)
- **#4 复活 agent_memory_records**:复用 compass B轨Phase1(reinforce_count+1 on recall hit·23 pytest绿·未部署)接活这张冻结78天的表=跨agent学习通道。
- **KB A类腿补燃料池**(不同题源·不受ALE难题限·跑KB GPU批前ping soul错峰)。
- 已切回cuda(实验完)。

## 2. 🔴 5 断点(优先级·platform turf·先连生产库诊断真schema)
1. 🔴🔴 **#1 A2A链物理断**(最优先·三agent自治物理前提):PG触发器引用不存在字段`to_agent_id`(`record "new" has no field to_agent_id`)·a2a静默62h。**诊断已做:该触发器是生产Postgres活对象·不在代码/migration**(grep全repo只在V5审计消息出现)·残留`_tmp_patch/fix_dispatch_trigger.sql`是另一个触发器(bounty→stake)非此修复。**起点:连生产DB → `\d+ platform_agent_messages`看真列名 + 查引用to_agent_id的触发器 → 改字段对齐真列名 → 应用+验证a2a通**。
2. 🔴 **#2 dead-letter/unread无消费者**:2728 unread+1038 dead-letter。加重投+消费worker。
3. 🟠 **#3 evolution指标facade**(soul 6/10裁定的):evolution_score全=3 cron批写·停cron→接provenance派生·或诚实弃用列。
4. 🟠 **#4 agent_memory_records冻结4/06**:compass B轨reinforce接活(见§1 compass)。
5. 🟡 **#5 Kairos死螺旋**:insolvent(8NAU)还被stake派死单·stake派单前查solvency·跳过insolvent。

## 3. 蒸馏第4测条件(料够/H800时·别在小n上空转)
- **触发**:A类→30-50(V5 ALE续凑+compass KB腿·别再9→11小增量·无梯度已证)·或获H800。
- **命令(同§2历史·带confound防护)**:过滤ahc008 → `distill_loo.py --records ... --k 4 --epochs 3 --max-seq 4096`(1.5B)+`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`。**先核confound**(grep -c OutOfMemory·各折没崩·n>0)。
- **若上H800**:7B@4096干净测容量假设(T4装不下)·这是分清"容量vs料"的唯一干净法。
- **判**:valid_rate>0.6=PROVEN破墙;仍~0.2平=可能ALE蒸馏天花板·转SWE或诚实杀回护城河副产品。

## 4. 🔴 红线/gotcha(别重踩)
- **R3**:5断点=生产DB改动·别在超长session尾rush·fresh专注做+逐个验证。
- **生产DB变更**:先只读诊断真schema(`\d+`)·改前备份触发器定义·改后验证a2a真通(发条消息看收到)。
- **confound-discipline**:任何KILLED/失败先核confound(adapter没存/seq截断/进程死/prompt-skew/OOM/缺模块)·今晚抓了6个假失败。别基于单fold外推(V5 0.33教训)。
- **SSH走`ssh gpu`**·瞬断退避别硬敲(重负载/多框撞)。**根盘50G易满**(containerd在根盘·docker build涨它)·满了清pip cache/旧loo_run残留/docker rmi sweb.*。datadisk0=99G。
- **compass=cuda**(已切回)·GPU实验占用时才切CPU。
- **GPU盒**=43.166.8.20=T4 16G·distill-venv/swe-rsi venv·ale judge=python-202301镜像。

— 交接soul · 2026-06-24(蒸馏弱KILL重定性=燃料饿转agent自治·三框联动:soul修5断点+第4测·V5凑料+atoms reinforce·compass复活memory_records+KB腿·#1 A2A生产触发器先修·料n→30-50或H800再跑第4测·confound-discipline+R3生产DB别rush)
