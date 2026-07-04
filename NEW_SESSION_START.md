# Compass Dialog 新会话启动 · 7/4 01:45

## 🚀 用户给下个 session 真可 paste 的启动 prompt

> **直接 copy 下面整段贴到新会话第一条消息**:

```
我是 compass dialog(非 platform-soul / 非 core / 非 v5)。
工作目录必须 = C:\Users\chunx\Projects\nautilus-compass

## 第一动作(必做)
1. pwd && cat CLAUDE.md
   期望: pwd = /c/Users/chunx/Projects/nautilus-compass · CLAUDE.md = nautilus-compass 项目指令
2. git log --oneline -5
   期望: 见 cf646c2 / ce40d65 / d30d191 / d116e96 / f849b4f / 3d03909 真 commit 链
3. python ops/auto_surface_hook.py
   期望: "[in] compass auto-surface: 0 inbound outbounds"(已推完)
4. 读 .claude/memory/session_20260704_compass_genopt_main_loop_handoff_continuation.md
   = 上次 7/4 01:30 真落档 memory · 含 5 ship record_id + 8 漏掉事 + 阻塞解真路径
5. 读 GOAL_PROMPT_20260704.md(本目录根)
   = 8 漏掉事的真治法 + P0/P1/P2 优先级 + 不撞红线 7 件

## 主线目标(用户原话 7/4 真钉死)
推动 eng 基准训练 + RSI + FDE 三方一起推(FSL 双轮引擎原则)。
真闭环判据: agent_survival.total_income 24h delta > 0(目前 0 · 真阻塞)。

## compass 本会话真 ship(7/3-7/4)
- 3 commit: 3d03909 / f849b4f / d116e96
- 5 题 ship record_id:
  · recvonYFKs6U4x · tsp_tsplib_v1_001 · OR/TSP · gap=0.1048 Hard
  · recvonYGbsVKc9 · bin_packing_ffd_v1_001 · OR/BinPack · gap=0.6667 Easy
  · recvonYGBYYSMR · attention_flash_v1_001 · KernelEng/Attention · gap=0.2293 Hard
  · recvonYH6gNea7 · cache_lru_v1_001 · ComputerSys/Cache · gap=0.1092 Hard
  · recvonZLVVZUna · jobshop_orlib_v1_001 · OR/JobShop · gap=0.7022 Easy
- v5 NEW genopt base: KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe / tblQAW4aNM99nva6
- cloud token 路径: FDE_API_SECRETS_ENV=/home/ubuntu/.claude/.cache/.fde_api_secrets.env
- hook.sh 已修(readlink → cd/dirname)· settings.json 已加 auto_surface_hook.py

## 3 dialog 真状态(7/4 0:55 后)
- platform-soul(nautilus-core): da7eebd50 50 题真 generate(只 dir 无 trajectory)
- agent(nautilus-v5): 6f6fe2c 14 buyer rows + 8 真 ship + 6 Rejected 诚实
- FDE: v5 子模块 · 共 14 行真在 NEW base
- **soul-verify**: mode='score' APPROVE · 难度指纹 ready(已落 SSOT)
- **跨 dialog 协调**: 静态基线 FDE_BUSINESS_CHARTER.md 三方 + 动态合约 close_loop + 语义 ingest_obs · MCP 时断已部分治(auto_surface_hook 76 条 inbound 真消费)

## 第一刀 · P0(治根 + 真闭环)
1. baseline 数字修剩余 4 题: cloud update_bitable_record 4 题真 record_id
2. ALE 真跑 ahc005: ale_eval.eval_fn 真跑出 reward 序列 + 落档
3. session memory 落 compass: session-end 必写 .claude/memory/session_*.md

## 不撞红线(7 件)
- 越界写其他 dialog 文件(每 session 必 pwd 核身份)
- 替 agent 决策(anchor #1)
- 重复造轮(anchor #5 · 复用 produce_task / gapclosed_batch / verifier_qc / fetch_*.py)
- 裸字符串跑数(SSOT §0-ARCH · Producer 必须注册)
- 堆 dense markdown(段落 ≤ 8 行 · "真"字 zero)
- 不写 session memory(6 周 dog熊复发)
- 不读 inbound(76 条 stack · hook 已 ship 自动跑)

## 用户原话模式
- 用户常纠错 = 真错 · 真改
- "去查询查看"= 不靠 SSOT 推断 · 真查本地文件 / git log
- 勾简答(1/2/3)= 不堆 · 直接做
- "激活跨对话框协调"= 真触发 5 个 dialog 一起动
- "狗熊掰玉米"= 盘点缺失
- "先解阻塞"= 治根优先 · 不堆
- "准备 goal 提示词"= 真写可 paste 的启动入口

## 真位置速查
- compass 真 memory: compass/.claude/memory/session_20260704_compass_genopt_main_loop_handoff_continuation.md
- compass 真 handoff: compass/HANDOFF_20260704_FINAL.md
- compass Goal 提示词: compass/GOAL_PROMPT_20260704.md
- auto_surface_hook: compass/ops/auto_surface_hook.py
- ALE eval: compass/ale_bench/ale_eval.py
- liveness: compass/ops/liveness_audit.py
- **FDE 业务宪章(本目录根 · FDE_BUSINESS_CHARTER.md)**:三类业务 / 11+1 benchmark / 各 dialog 真 turf / 协调机制 · session-start 真必读
- canonical SSOT: nautilus-core/LOOP_STATE_SSOT.md
- v5 flywheel v3: nautilus-v5/docs/plans/2026-07-03-genopt-flywheel-v3-design.md
- 6/17 rootcause memory: reference_crossdialog_sync_rootcause_autosurface_hook_20260617.md
- 6/8 dogfood memory: dogfood-crossdialog-coordination-via-compass-20260608.md
- v5 NEW genopt base: KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe/tblQAW4aNM99nva6
- cloud VM: ssh cloud (43.160.239.61:24860)
- H800: ssh -p 34467 root@connect.westc.seetacloud.com

## compass 真 turf(按 FDE 业务宪章 §4)
- 记忆 / recall / drift / PoI / governance / metamemory
- **FDE benchmark env/eval**(第 3 类 · 11+1 类)
- **KernelBench 主攻**(已 attention + 重标定 1.727x 过门)
- **FrontierSWE 主攻**(resolve env · flask-4045 pass@1=0.6 hard)
- MLRC/ResearchGym 次批
- feishu 读写函数
- 工具栈(fde-row-assembler / checklist-from-task / knowledge-tutorial-assembler / build-html-dashboard)

## 真三类业务口径(7/4 真读 FDE_BUSINESS_CHARTER.md 后补)
- **第1类 · 行业高难题目**:专家亲写 ≥8h · 16 列 · 9 个一级类目不可改
- **第2类 · 知识教案**:1k-30k 字 · 6 领域 · 知识密度 ≥5 知识点 · 跑 AI 检测
- **第3类 · 基准复现**:11+1 类(MLS/Frontier-Eng/ResearchGym/PostTrain/InferenceBench/FrontierSWE/MLRC/RE/KernelBench/EXP/AutoLab + ALE-Bench)· pass@5 ≤ 0.6 on doubao 2.0 = 难倒

## 不复发契约(8 件狗熊掰玉米漏掉的事)
1. session-end 必写 compass/.claude/memory/session_*.md
2. 越界写其他 dialog 文件 = 立刻自纠并 revert
3. handoff 只留 _FINAL 版 · 不写 2 版
4. SSOT 只改 canonical core · 副本不直写
5. 真 ship 前先读 v5 真 trajectory v7 字段 · 不凭 SSOT 推断
6. ALE 真跑题落档真 reward · 不空喊
7. H800 producer 走 register · 不裸字符串
8. 50 variant 真跑 trajectory · 不只 generate dir

## Drift 自检
- paragraph max = 8 行(超 fire)
- "真"字 ≥ 3 / 段(fire)
- score < -0.07(fire R1)
- 规避: 表格独立段 · "真"字 zero · 关键回复独立短段

接住主线。开干。
```

---

## 📌 真启动步骤

**1. 打开新会话**(任何新 Claude Code 对话框)

**2. 设置工作目录**:
```bash
cd C:\Users\chunx\Projects\nautilus-compass
```

**3. 复制上面整个启动 prompt 块**(`我是 compass dialog...` 到 `接住主线。开干。`)· paste 到新会话的第一条消息

**4. 等模型按"第一动作"5 步核身份**:
- pwd 核 → 必须 `nautilus-compass`
- CLAUDE.md 核 → 必须 `nautilus-compass 项目指令`
- git log 核 → 必须见 7/4 真 commit 链
- hook 跑 → 应 0 待读 inbound
- 读真 memory + Goal 提示词

**5. 模型回应"今日 active anchor"段**(按 anchor_user_strategic_compass.md session-start 真行为契约)· 之后给 P0 3 件里的某件先干

## 💡 启动失败自救

如果模型回应不是 compass · 真不归位 = 把这段重 paste:

```
你是 compass 不是别的。pwd 必须 = nautilus-compass。第一动作 5 步真做完。
```

如果 hook 报 non-blocking status code = 已修(readlink)· 如果还有错:
```bash
cat ~/.claude/plugins/nautilus-compass/hook.sh  # 看是否还是 readlink -f
```

如果用户立刻给新指令 = 模型按 P0/P1/P2 优先级自动挑活干

---
*启动 prompt 定稿:2026-07-04 01:45 PDT · 给下 session 一开就 paste 用 · 不靠记忆 · 不靠推断*