---
name: anchor-fde-business-charter-20260609
description: "🔴 FDE 业务宪章 · 跨对话框单一 source of truth(三类业务/我方-甲方/甲方需求红线/产出清单/各框 turf/协调机制)· 所有对话框 session-start 必读 · 解\"平台不知道业务\"根因"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4664f93f-bb90-415b-ba46-df561a78a142
---

# 🔴 FDE 业务宪章 · 跨对话框单一 SOURCE OF TRUTH(2026-06-09 建)

> 解决"平台/各对话框不知道三类业务/甲方需求/产出"的根因 = 缺一份所有对话框都读的权威业务锚。本文是那份锚。canonical 在 compass memory,副本在各 repo 根(`FDE_BUSINESS_CHARTER.md`)。**所有对话框 session-start 必读。** 变更走此文件,不另起炉灶。

## 0. 我方 / 甲方(🔴 保密)
- **我方 = 伊洛科技**(用户的公司)。
- **真甲方 = 保密大厂**(用户私下告知 · **任何对外/交付/呈现/outbound 绝不提名**)。
- 我们(伊洛)给甲方提供下面三类业务的样例/交付物。

## 1. 三类业务(都同一个甲方)· 🔴 类号以甲方/用户为准(用户 6/9 校正 · compass 不自拍业务定义 · 之前编号是从 reference 自编、错了)
1. **行业专家 / 专家复现**(L1/L2/L3 分级 · 16 列出题格式)— **6 样例** = `vtf/data_001~006_task.txt` + `data_00N_checklist.json` · 买方官方示例 = `~/Downloads/行业高难题目项目 示例.xlsx`(16 列锚)。
2. **知识教案**(FDE 知识任务沉淀 · 四段:任务标题/一Instruction/二KnowledgePoints/三BackgroundKnowledge/四Task示例)— 黄金样例 = `~/Downloads/_行业评测萃取/本原-行业数据集样例/编程自动化/编程自动化.md`。
3. **基准测试样例**(大模型/agent benchmark · 11 前沿 benchmark)— 脚手架 = `vtf/fde-toolbox/出题脚手架_前沿AIeng_11benchmark.md` · A 簇 env(GPU `/mnt/datadisk0`)· B 腿候选 daemon-cpu/capstone/blas。
- ⚠️ **资料散在 `vtf/` + `~/Downloads/`,不在平台/各 repo** → 这是平台"找不到/不知道"的直接原因。fresh session 要把这些位置纳入宪章 + 考虑集中。
- **素材来源 = 我们自身**:平台/soul/compass/各 agent 开发过程的问题 + 用 Claude Code 的经验教训 → 自身总结反思 → 产成样例(B 腿 daemon-cpu/capstone/blas = 真实经历非编造)。
- **过程中打通 RSI+FDE 整链** → 对外招募各专家开展 FDE 知识沉淀 + agent 工作流训练业务。

## 2. 甲方需求 / 红线(铁律)
- **难度 = ≥8h 人类专家复杂度**(不是 pass@5≤0.6 · 那是内部 proxy · pass@k 仅附加证据)。
- **🔴 专家亲写 · 甲方跑 AI 检测 · 不能 LLM 批量生产 · 附件真实**(脱敏/减英文附件)。AI 框只能结构化/搭环境/验证,**叙述内容靠真人专家**,AI 文字需真人润色过检测。
- L1/L2/L3 分级(L3=系统性·环境检查+工具调用+权限)。
- 算力:A 簇 T4 够 · B/C 簇需 H100(王泽协调)。
- **交付载体 = 飞书多维表格 + 网页**(不能拿 md 交付)。

## 3. 当前产出清单(2026-06-09)
- **compass**:检索 CLI(f004223)· PoI consumer(4c6640c)· feishu create_bitable_record(f2de04b)· 凭据参数化(4d1fb51)· A 簇 env(KernelBench/AutoLab)· 工具栈(fde-row-assembler/checklist-from-task/knowledge-tutorial-assembler/build-html-dashboard)· B 腿候选(daemon-cpu/capstone/blas)。
- **soul**:escapes 终判(radix=TRUE / bvh=FALSE·model confound)· 难度指纹折 RUBRIC · 教案表(base Y7ZFbMbJqaWSxHs27chcC706nZb / table tblZKcpcSYeACj5J)+ 第一篇《CPU饥饿诊断》。
- **agent(v5)**:bvh 2-arm(deepseek 复跑定泛化)· 提交出题表(base EOVhbQwA0a1HEOsgmxecgkBVnwh / table tblhD4O4f0esTyXc 14列)。
- **RSI 飞轮**:radix 单题 escapes=TRUE(护城河)· bvh 待 deepseek 复跑定性 · c3(ΔReward→PoI)defer 到泛化定性。
- 🔴 **未决撞车**:教案表两张(soul tblZKcpcSYeACj5J vs agent tbl9c6mvPRTuq9sD)需统一。

## 4. 各对话框 turf(不越界)
- **compass**:记忆/recall/drift/PoI/governance/metamemory · FDE benchmark env/eval · feishu 读写函数 · 工具栈。
- **soul(platform-soul)**:标准/QC(checklist_scorer)· benchmark_verifier(pass@k/escapes)· 难度门 · 提交编排。
- **agent(v5)**:出题主体(产候选/轨迹)· 建提交表 · gateway · RSI producer。
- **platform(nautilus-core)**:平台 infra · dispatch · 部署端点 · 数据库。
- **用户(真专家)**:题干/教案内容定稿 · AI 检测兜底润色 · 算力协调。

## 5. 跨对话框协调机制(吃狗粮 · 复用不重造)
- **静态基线(本宪章)**:放各 repo 根 `FDE_BUSINESS_CHARTER.md` + ingest 到各 project → 各对话框 session-start 必读。
- **动态协调**:① 合约通道 `contract.py` close_loop(session_*.md frontmatter `contracts:` block · scanner 跨 project surface)② 语义通道 `ingest_obs(project=对方)`→recall(per-project)。
- 🔴 **当前不便根因**:MCP 时断(语义通道挂)+ 散落 outbound md 靠对方碰巧读 + 本宪章之前不存在。**修复=本宪章 + MCP 稳定 + 未来统一控制面(平台看板 W-A)。**

## 6. 维护
- 业务/甲方/产出有变 → 改本文件(canonical compass memory)+ 同步各 repo 副本 + ingest 各 project。
- 不另起炉灶、不让认知再散。

关联 [[project_fde_three_tracks_one_buyer_presentation_gap_20260609]] · [[dogfood_crossdialog_coordination_via_compass_20260608]] · [[plan_compass_PRODUCTION_handoff_20260609]] · [[reference_yiluo_buyer_spec_two_tracks_difficulty_8h_20260608]]
