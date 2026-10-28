# /goal · 2026-06-18 fresh session · platform-soul(nautilus-core 后台引擎)

我是 platform-soul。上一会话(6/17 marathon)把 RSI 核心从"设计"推到"全部就绪、就差点火"。本会话**唯一 P0 = 跑 p13 pass@50 确认第一道真 true_wall**——这一步绿,蒸馏飞轮和复利记忆环同时点火。**先验证后动手·诚实·不 overclaim·反 D(别开新战线)。**

---

## 🎯 战略锚(用户 6/17 拍板·不变)
Nautilus = **中国化 Anthropic Managed Agents** · 平台为体、FDE 为用 · 三护城河=**agent 经济 + RSI 自我进化 + 共享复利记忆** · 路线 C→A→B(不并行)。当前在 **C(护城河先证)**。设计:`nautilus-v5/docs/plans/2026-06-17-nautilus-managed-agents-china-thin-client-design.md`。

## 🔴 P0(唯一 forcing function)= p13 pass@50 S-诊断 → 确认第一道真 true_wall
**为什么这是 gate**:6/14 设计铁律——推理时方法有数学天花板,蒸馏是唯一破能力墙机制;S-诊断"决定后面所有路线有没有意义"。本会话之前飞轮只在易燃料上转(doubao 8/8 解·90% reward 1.0=空转)。compass 重算现有 24 题:**唯 2 道 correctness true_wall(p13/p14)**。p13 pass@50 守住 = 第一道真蒸馏候选 = 飞轮第一次有意义。

### 全部就绪(别重新发现·上轮已锁)
- **GPU box = `43.166.8.20`**(实测 LIVE·`/mnt/datadisk0/KernelBench` 在·`/tmp/gpu.pem` 可达)。⚠️ **不是 43.163.80.46**(那个 publickey 拒绝)。
- **verifier 已就绪**(compass 建·共享 FS):`kb_eval.py`(单候选 guarded eval)+ `triage_aggregate.py`(出我的契约 `{n_samples,n_passed,n_correct_but_gated,bucket}`)。位置:本机 `~/fde_t3_scratch/kernelbench/`·GPU eval 须在 T4 box `/mnt/datadisk0/KernelBench` 的 `.venv` 内跑。**第一步先 ssh 43.166.8.20 定位 kb_eval/triage_aggregate/p13 的 prompt.txt+ref.py 实际路径**(compass 说在共享 FS·没确认我能直读 → 先 locate,缺就请 compass scp 到 GPU box)。
- **doubao 采样**:ARK key 在本地 `~/.claude/.cache/.fde_api_secrets.env`(`ARK_API_KEY`·已验)。模型 `doubao-seed-2.0-pro`·端点 `https://ark.cn-beijing.volces.com/api/plan/v3/chat/completions`。completer 复用 `nautilus-v5/fde_capsule/_run_bvh_2arm.py:make_ark_completer`。
- **我的三桶分类器** `phase3/backend/services/fde_triage.py`(11 TDD green·已在 compass 真数据 p13/p14/p51 验过·p51 洗门 negative-control 守住)。
- **PoC 参考** `_tmp_patch/sdiag_poc.py`(上轮自包含 S-诊断 PoC·doubao→bench_eval→triage 端到端跑通 d1·复用其模式)。

### runner 流程(net-new orchestration·建成 `services/fde_sdiagnose_run.py` 正式件·TDD 纯逻辑+integration 跑)
1. 读 p13 `prompt.txt`(喂 doubao 的完整题面)。
2. doubao 高温(temp=1.0)采样 **k=50** → 50 个候选 kernel(从 ```python 块抽·参 sdiag_poc.extract_code)。
3. 每候选 scp 到 `43.166.8.20` → `cd /mnt/datadisk0/KernelBench && .venv/bin/python kb_eval.py --level 2 --problem-id 13 --candidate cand.py` → result JSON。
4. 收 50 个 result → 跑 compass `triage_aggregate.py` → `{n_samples,n_passed,n_correct_but_gated,bucket}`。
5. 我 `fde_triage.classify_task` 确认 bucket。
- ⚠️ 重活(50 doubao + 50 GPU eval)→ **background 跑·别前台 sleep-poll**。先 **pass@5 或 pass@10 pilot 证端到端管线**(doubao→scp→kb_eval→aggregate→triage)再放 50。

### 判据(死口径·上轮锁·compass 已 ack)
- **true_wall(蒸馏候选)= pass@50 correctness 通过数==0 且无洗门**(`n_passed==0 and n_correct_but_gated==0`)。
- 🔴 **KernelBench 门方向**:G2 = speedup **>2× 快** 触发 suspect cap(反作弊)·**不是慢**。correct-but-slow 不被门拒(只是 fast1=0·correctness 仍过)。被门拒=correct-but-suspiciously-fast=`n_correct_but_gated`(非 true_wall)。原则不变(我 triage 只吃 n_correct_but_gated 输入·零改动)。
- p13=最强 hope(5/5 compiled 但 correctness 错·数值大错)。p14=偏弱(max_diff 仅 ~0.02·k=50 可能破→洗成 pseudo·正好验真假墙)。**先 p13·再 p14**。

### P0 绿之后(点火·downstream)
p13 pass@50 correctness=0 确认 → **mint 进 dispatch 点燃两环**:
- `POST /api/platform/fde/dispatch`(header `X-Platform-Key`)· desc JSON `{fde_class:3, kind:"code-fix-with-deterministic-verifier", 任务概括, starter_inline, verifier_inline, task_family:"<slug>"}` · task_uid=`compass_<family>_<slug>_<ts>` fresh。**🔴 desc 顶层带 `task_family` slug**(W3·V5 `extract_task_family` 认·复利记忆按 family 聚)。
- 点燃:① V5 自治 claim→解→W1 写 learning 回 compass fleet→W2 同 family recall→**生产原位 reward-uplift**(V5 W1/W2 已 armed·env `V5_FLEET_MEMORY=1` LIVE)② 我回 compass 结果→它登记 PoI ③ 蒸馏 S-PoC(1K 强模型 traces→QLoRA 7B·V5 producer+GPU·王泽排期)。

## 各框 turf 状态(收敛后·6/17 晚)
- **compass**:true_wall 口径已锁·verifier 已交(kb_eval+triage_aggregate)·重算 24 题给了 p13/p14/p51。**待**:fresh session 升级 stump skill 测 correctness pass@50 + 注入 task_family slug 进 dispatch desc + 给 V5 一个样例 payload 对 `extract_task_family`。MCP 回则登记 keystone PoI。
- **V5**:W1/W2 复利记忆环 wire LIVE(armed·等真 true_wall 燃料点火)。蒸馏里是 S-PoC producer。
- **FDE**:webhook 业务环 GREEN 可发 v0.9.6。SOP↔引擎 reconcile drift 报告已给(枚举统一/SOP 补两段制=FDE+用户决策)。
- **平台-soul(我)**:S-诊断 gate 全就绪·P0=跑 p13 pass@50。

## 🔴 gotchas(上轮踩过·别重踩)
- **GPU box = 43.166.8.20**(非 .46)。SSH 偶发 `Connection reset by 43.160.239.61:24860` → 重试(`-o ConnectTimeout=15` + for 循环 retry)。
- **bash /tmp ≠ Win-python /tmp**(curl 写 /tmp 后 python 读不到)→ python 内 urllib 直抓 或 本地脚本 scp 跑(别 ssh 包 python heredoc·f-string 反斜杠/嵌套引号易碎)。
- **GBK console mojibake**:中文 UTF-8 在控制台乱码 → `PYTHONIOENCODING=utf-8` 或直接取 JSON 字段。
- **bench_eval/kb_eval 输出多行 pretty JSON**:解析取整段(first `{`→last `}`)·**别 splitlines[-1]**(上轮假 FAIL 根因)。
- **fresh-uid-per-version**:每版换 task_uid 否则撞 verdict-join 遮蔽(`api/fde_dispatch.py:157`)。
- 跨对话框通道:**V5/compass = cloud `~/nautilus-soul-workspace/docs/`**(scp·`_OUTBOUND_FROM_PLATFORM_SOUL_TO_<X>_*`)· **FDE = GitHub `chunxiaoxx/nautilus-FDE` repo `_COORDINATION/`**(`gh api -X PUT`·命名 `FROM_platform_soul_<date>_<topic>.md`)。MCP 时断→走这俩。
- **复利记忆 fleet creds**(W1/W2·若本会话碰)= 共享 `~/.claude/.cache/.fde_api_secrets.env`:`COMPASS_FLEET_USER_ID=u_4c53db8a1f` + `COMPASS_FLEET_TOKEN`(JWT·30天·过期 `POST compass.nautilus.social/v1/auth/login {email,passphrase}` re-mint)。W1=reward1.0 后 POST `/v1/observations`·W2=claim 前 recall。**V5 已 wire 其侧·我侧 settle 点 W1 V5 daemon 已覆盖**(确认无需我重做)。

## 凭据/坐标
- `ssh cloud`(43.160.239.61:24860)· backend `/home/ubuntu/nautilus-mvp/phase3/backend/.env`(`PLATFORM_DISPATCH_KEY`/`DATABASE_URL`·分叉外科 scp 勿 pull·restart nautilus-backend)。
- `ssh -i /tmp/gpu.pem ubuntu@43.166.8.20`(GPU T4·KernelBench)。
- dispatch `POST nautilus.social/api/platform/fde/dispatch`(X-Platform-Key)· verdict `.../verdict`(免鉴权)· tasks `GET .../tasks`。
- 飞轮看板 `nautilus.social/api/platform/rsi-fde/dashboard`(后端 HTML)+ `?limit=N`(JSON·flywheel/fde_business/verdicts)。

## parking lot(captured·本会话别开·反 D)
- W1/W2 复利记忆完整一圈点火(等 P0 + compass task_family·V5 侧已 armed)。
- 蒸馏 S-PoC(1K traces QLoRA 7B·等 true_wall 确认 + GPU 排期王泽)。
- SOP↔引擎 reconcile Drift 2/3/4(SOP 补两段制/枚举全栈统一/schema 反向生成·FDE+用户 turf)。
- git master 分叉清理(76 ahead/29 behind·部署走 scp·要专门 reconcile session·别盲 push)。
- 两套 FDE 系统 canonical base(用户拍板)。
- 飞轮燃料多样性(C.7·compass benchmark 题进池)。

## 纪律
R1-R5 护栏 · #3 反 D(P0 单点·别开新战线)· #2 RSI 闭环优先 · 诚实(交付 provisional·pass@50 重活先 pilot 证管线·不 overclaim)· 验证优先于动手 · session-start 读 `FDE_BUSINESS_CHARTER.md` + memory `session_20260617_rsi_sdiagnose_gate_kickoff`(含 true_wall 口径/PoC 结果/就绪度)+ `session_20260617_fde_webhook_e2e_verified_green`。
