# 交接 · BioMysteryBench P1(2026-07-16 · compass 对话框)

> 贴进新 CC 会话作为 goal。上一会话已把 infra 抢修 + BioMysteryBench 脚手架/设计做完并 push,本会话专注 P1。

---

你是 **compass 对话框**(nautilus-compass · 记忆/探针/feishu/FDE benchmark turf)。

## 今日 goal:BioMysteryBench **P1 — 证 1 个模板端到端**

甲方外部需求:500 道**生物信息学反向推理题**。上一会话已建好脚手架+500 规模化设计,走**路 A(compass 自产)**。本会话只做 **P1:把 1 道题的完整生产环(选源→匿名→出题→定 rubric→真解验证→过验证器→打包)真跑通一遍**,沉淀成管线雏形。**不铺量、不建全模板库**——先证 1 道过买方验收档。

**推荐模板**:`VCF → 变异临床意义`(数据小 MB 级 / 解法清晰 / 难度稳),或另挑一个小数据型。**避开 qes1 那种 721MB 原始 FASTA**。

## 开工先做(session-start)
1. `recall` 召回:`session_20260716_biomysterybench_scaffold`(需求+脚手架+环境+500设计)、`session_20260715_cloud_box_health_audit`(bio 环境决策)。
2. 读:`vtf/fde_benchmarks/biomysterybench/` 下 `README.md`、`DESIGN_500_scale.md`、`bmb_validator.py`。

## 已就绪(别重造 · anchor 5)
- **验证器** `bmb_validator.py`(已验:自检过 + 买方样例 qes1 实测过)——挡格式/泄露/白名单。
- **bio 环境**:Windows Python + **Biopython 1.87 已装** + **NCBI Entrez 实连通**(远程调库/BLAST)。🔴 **WSL 网络坏,别用 WSL**;需本地重工具(samtools/全量 BLAST)才上 cloud box(43.160.239.61,共享+刚从过载恢复,慎)。
- 买方格式:`problems.csv`(id/question/answer_rubric/allowed_domains/human_solvable)+ `data/<ID>.zip`;白名单 14 域名见 README。

## P1 验收(达成才算完成 · 铁律:独立验证非自报)
1. 产出 1 行 `problems.csv` + 对应 `data/<ID>.zip`(真数据、已匿名剥答案)。
2. `bmb_validator.py` 跑过 **0 REJECT**。
3. 🔴 **真把它解出来**(用预期工具链),坐实:答案能从匿名数据推出 + **唯一** + 无泄露 + **20-30min/≥10 工具调用难度**(不是 <5min)。这步是买方 bmb-infer 的命门,**不能跳、不能自报"应该能解"**。
4. 把 P1 的解题脚本沉淀进 `vtf/fde_benchmarks/biomysterybench/`,作为管线雏形(P2/P3 复用)。

## 红线 / 护栏
- 真数据真分析,**AI 不得凭空造**题目/数据(买方跑 AI 检测)。
- **优先小数据**(存储/带宽);NCBI 有 rate limit(限速/API key)。
- R1-R5 长 session 护栏;**件数≠价值**(P1 的价值=1 道过验收,不是产了多少);SSOT drift 病根,自报别信。

## 侧挂(非本会话重点,知悉即可)
- 2 份合约 due 7/18(platform SSOT canonical 同步 / V5 SSOT+mint 跳已铸题)——compass scanner 会盯,到期核销。
- nautilus-db MCP 本会话应已激活(上一会话修复,CC 重启后生效)——可用它直查生产库。

## 上一会话大事(背景 · 详见 memory)
backend 502 已修 / BGE runaway 已限流(load 14→3.35)/ live 真值 income 703·自治 89%(靠同 11 题重刷,真瓶颈=新题供给)/ 跨框合约已派 / security pass 无入侵。
