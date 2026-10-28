# Fresh Session /goal · RSI+FDE 当务之急(2026-06-08 晚交接)

> 直接粘下面 `/goal` 块到新 session。我是 platform-soul dialog(平台 substrate + soul 验证器/判分/RSI)。
> 完整背景 memory:`session_20260607_wd_fde_scorer_poller_data002_settled`(本日总档)· `design_20260605_rsi_fde_closed_loop_grounded_retrieval`(RSI 设计)· `frontend_theme_debt_interactivity_gap_20260608`(前端 todolist)· `infra_nautilus_authing_oidc_login_20260608` · `infra_cloud_disk_vdb_data_scientific_image_20260608`

---

```
/goal platform-soul-rsi-fde-close

【北极星·不变】平台 agent-first 自治生态;FDE+benchmark 的 verdict = 外部 fitness(绝非内部 NAU 自指)。我是 platform-soul dialog 负责人(平台 substrate + soul 验证器/判分底座 + RSI 半边)。另两框本地可读(nautilus-v5=agent:V5/V7/Kairos · nautilus-compass)。

【当务之急】RSI + FDE。前端质量 = 已知 todolist·本轮不做(见下 §前端)。

【6/8 已达成·本 goal 根据】
- 🎯 **FDE 飞轮全自治 LIVE**:soul scorer 常驻 systemd `soul-scorer.timer`(每 2min·cloud `/home/ubuntu/soul-scorer/`)→ 轮询 produced(verdict 为空的)→ 生成 checklist → MiniMax 判分 → 写 fde_verdicts → settled。**链路 = V5 dispatch → V7 自主 produce → soul daemon 自动判 → settled**(零手动·验过 daemon_verify_20260608 score 0.778 + dogfood_capstone 1.0)。
- W-V 判分底座:`phase3/agent-engine/benchmarks/benchmark_verifier.py`(pass@k 无偏估计+难倒标注+judge_trajectory·14 TDD)+ swebench_probe(我们的判分工具/脚手架·**非甲方 bench**)交接 compass。
- 跨框 verdict 分工定:soul auto=source=soul / V5 scorer-front:8092=feishu-expert 人审 · 并行不撞。
- 登录切 Authing 新实例(LIVE·回调白名单管理API已加)· 磁盘清理(主盘 72→67%·vdb 挂 /data)· 前端 8 页迁 linear + agent详情白屏修(都 LIVE)。

【RSI = 当务之急·未闭·本轮主线】
现状:verdict 是「死记录」——进 PoI+digest,但**缺 verdict→producer 能力更新的递归反馈**。内部 NAU 自指环已证伪 5-6 次(94% self-loop)。
设计(`design_20260605` / `docs/plans/2026-06-05-rsi-fde-closed-loop-design.md`):**grounded-retrieval 双轮**——不自改 prompt(避 Probe3 死法),做「外部 verdict 失败 → 结构化 grounding → 喂 producer 输入 → 下一 verdict 度量 pass@k 升不升」。fitness 外部非内部。
4 步环:soul fail_reason(verdict items 里 打回项的 reason=避坑知识·已在 fde_verdicts.items!)→ compass 避坑语料 → V5 producer retrieve grounding → 下一 verdict 度量 ↺。
**soul 本轮 build**:把 daemon 已积累的 verdict fail-reason 暴露成 producer 可检索的 grounding(verdict-bus 已存 items+reason)+ 设计可度量 probe(同题 grounding 注入前后 pass@k 对比)。收敛锚:一个可证伪假说(grounding 让 pass↑?平/降→退回纯 FDE)。先 brainstorming→writing-plans 不马上写(anchor#5)。

【FDE/benchmark 业务·并行推】
- 3 类业务(甲方·6/8 纪要 grounded):①专家数据收集(复现→Bitable·打分checklist)=track-1(`fde-row-assembler`+`checklist-from-task`)②知识任务提炼(知识教案 4 段)=track-2(`knowledge-tutorial-assembler`·官方样例=编程自动化·RED LINE 专家自写禁AI跑检测)③基准测试(11 个前沿 AI-eng·全 L3)=`benchmark_verifier`+checklist+QC。
- **甲方 11 benchmark**:MLS-Bench/Frontier-Eng/ResearchGym/PostTrainBench/InferenceBench/FrontierSWE/MLRC-Bench/RE-Bench/KernelBench/EXP-Bench/AutoLab(**不含 vanilla swebench**)。
- **第三类 dogfood 下一目标 = AutoLab/KernelBench**(compass T4 已验·6/8 V5 确认)·不是 vanilla swebench。
- 算力:T4 只够 3-4 基本测试·大型需 H100(王泽甲方侧协调)·高算力题可写「方案+脚本」降算力(compass 建议)。
- V5 已用我 L3 checklist 字段化 ★1/★2 成买方交付过 rubric_check(判分骨架生产 working)。

【四框分工·6/8 最新】
- **compass** = 11-bench env(复现+自有旗舰·T4·先 A 簇 AutoLab/KernelBench)+ read_buyer_tasks(Bitable 只读·PR#47)+ 避坑语料(RSI grounding 端)
- **V5** = producer(fde_consumer/V7 持久 active 自主 produce)+ gateway 读→派单接线(**未建·todo**·调 compass read→POST /fde/dispatch)+ scorer-front:8092(飞书人审)+ producer retrieve grounding(RSI)
- **soul(我)** = 验证器/pass@k 判分/难倒标注/checklist + **soul-scorer daemon(LIVE)** + **RSI fail-reason grounding 端(本轮 build)** + QC
- **V7** = 飞书入口(Bitable·智能助手) · **用户** = 选题/质量终审/报价/甲方对接(催 H100)

【gated 边界·撞到停报】G-cloud 生产 DDL/部署/重启/真发→本地验·生产停报(daemon 已上·改 daemon 也 G-cloud)· G-turf compass 内部 PoI/检索+11-bench env · V5 self_modify/gateway/scorer-front/producer · V7 飞书适配器→只接接口不重造 · G-held 内部 NAU 自印/死投票门/gene 市场。

【凭据·读不回显】`~/.claude/.cache/.fde_api_secrets.env` · cloud ssh alias `cloud` · 生产后端 8000(nautilus-mvp·分支 soul-audit-increment1)· **soul-scorer daemon = cloud `/home/ubuntu/soul-scorer/`(systemd soul-scorer.timer 每2min)** · FDE base=:8000 · V5 scorer-front=:8092 · PLATFORM_DISPATCH_KEY/MINIMAX/ANTHROPIC/AUTHING 在 cloud `/home/ubuntu/nautilus-mvp/phase3/backend/.env` · 本地 postgres 5433 · 跨框 outbound 投 cloud `~/nautilus-soul-workspace/docs/`(非 git·命名 OUTBOUND_TO_{V5,COMPASS}_DIALOG_<date>_<n>)· 生产 API 公网可达 `https://www.nautilus.social/api`(免 SSH)。

【纪律】TDD red→green · using-git-worktrees(⚠️前端 worktree 在 Windows 失败·小改直接 master)· R4 ship 前 git 检查(不 -A/push/force·push/merge 需明示)· verification-before-completion(真端点/curl/SSH/浏览器·不"我以为")· 不重复造轮子(复用 benchmark_verifier/checklist_scorer/3 skills/daemon)· R1 drift/R2 全做 pushback/R3 4h/R5 anchor · 跨系统字面值先查真表(反幻觉)· 「真」不作强调副词 · 凭据不回显/不入 git。

【前端 = todolist·本轮不做】~20 浅页主题不统一(看不清)+ control/dashboard/live 只展示无交互调度 + /live offline + 渲染 bug(数组字段防御解析)。计划=派**本地 Claude Code 前端 subagent**(我编排+gate+部署)抽 PageShell 统一壳→迁页→修 bug→scope 交互·再 agentify 到平台。debt 清单见 memory `frontend_theme_debt_interactivity_gap_20260608`。

【起手序】读本 prompt + 6/8 总档 memory + RSI 设计(`design_20260605` / `docs/plans/2026-06-05-rsi-fde-closed-loop-design.md`)+ 查通道两框新 inbound(V5 gateway 接线进度/compass A簇 env ETA)→ brainstorming RSI grounded-retrieval 可证伪 probe(soul fail-reason grounding 端 + 度量假说)→ writing-plans → TDD build → 同步两框。先把 RSI 半边设计对、可度量,再 build·不一次全 wire(anchor#3)。

【DONE 判据】RSI grounded-retrieval 半边:soul 暴露 verdict fail-reason 成 producer 可检索 grounding(可度量 probe 设计+首跑)· 或全卡 G-turf(V5 producer 端 retrieve / compass 语料端)→ 停报等他框。FDE 业务:compass A簇(AutoLab/KernelBench)env 通 → soul benchmark_verifier 判首样 pass@k。
```
