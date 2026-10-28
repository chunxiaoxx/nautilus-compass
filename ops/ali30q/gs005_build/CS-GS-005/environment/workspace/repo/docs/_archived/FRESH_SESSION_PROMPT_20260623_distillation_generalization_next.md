# 🎯 /goal · 蒸馏泛化首证(续)· 2026-06-23 交接(防烂尾·照命令跑即接上)

> 上个 session:中心环最硬一步(蒸馏)从"从没真跑过"推到**机制证活 + 泛化首证拿到真负结果**。本文是机械化续接——**不靠记忆,照下面 exact 命令跑**。

## 0.6 🎯 LOO 泛化第2测结果(6/23 晚·confound-clean·中心环第2枪)
- **verdict=KILLED · n=9 · win_rate_vs_base=0.22**(confound-clean:补了 confound_check.py + expandable_segments 治 OOM·重跑干净)。
- 🟢 **第一个真泛化信号**:`distilled_valid_rate 0→0.22`(第1测全 0)= distilled 在 **2/9 未见 held-out 题产出 scoring 解**(ahc002=2595 等)·base 全 9 题 0 分。distilled 从"啥都产不出"→"解出 base 解不了的"。**graded 信号(本 session 加)才看得见这个趋势**。
- **仍 KILLED 因**:base 全 0(赢 base 门槛低)+ distilled 只 2/9 有分且远低 doubao(56K vs 1.67M·解很弱)。
- **收敛判定**:KILLED 但"样本太少"未排除(valid_rate 在涨)→ **非死刑·继续攒料跑第3测**(n 9→20→50)。方向对量不够。
- 🔴 **第3测 trigger 降到 A 类 ≥12**(V5 grounded 确认:A 类卡 10=难题救活率低+glm timeout 非 merge lag·"A 类产率=强模型解出率"墙·易题救完剩 19 道难·死等 15 太久)。n~11 比第2测 n=9 仍有意义增量(看 valid_rate 0.22 那条线加几点涨不涨)。**最快补 A 类路=compass KB 腿**(不同题源不受 ALE 难题限·已邀切 cuda 接)。命令同 §2(带 expandable_segments)。
- ⏳ **现状**:A 类 11(ahc027 mer·差 1 到 12)·ALE 难题救活慢。
- 🎯🆕 **7B 容量假设实验 RUNNING(用户拍板·6/24 01:13)**:不干等燃料,改用 **7B(Qwen2.5-Coder-7B-Instruct)在同一批 ~10 A 类**跑 LOO k=4(`loo_run_7b`/`loo7b.log`)→ 对比 1.5B 的 valid_rate 0.22 = **拆解"容量 vs 样本太少"**。7B valid_rate≫0.22=容量瓶颈(上 H800 值)·≈0.22=数据/根本(别花钱)。**关键 infra**:compass 切 CPU(`zzz-cpu-failover.conf`·ZMM_DEVICE=cpu·释 4.5G)→ 7B QLoRA 在 T4 16G 装下(实测 12.7G·LoRA 161M 可训)·expandable_segments+HF_HOME=/mnt/datadisk0/hf-cache(7B 在 hub/ 子目录·15G)。~2-4hr。守候器 bg084soyc。
- 🔴 **7B 跑完后**:① 读 verdict+graded 对比 1.5B ② compass 跑完可切回 cuda(`rm zzz-cpu-failover.conf`+restart)③ 记 SSOT+memory+报 V5。
- 🎯 **7B 实验结果(6/24)**:① 7B@4096 OOM T4(激活超 16G·即便 compass 让出)→ 必须降 seq ② **7B@2048 = KILLED·valid_rate 0.0**(confound-clean·OOM=0·9 折全跑·distilled 全产真解 2000-4600 字符但全 0 分)< 1.5B@4096 的 0.22。**但被 seq 混淆**:7B 用 2048·1.5B 用 4096·疑 seq 2048 截断 ALE 长解致学不会。
- 🔬 **拆解中:1.5B@2048 对照**(`loo_run_1p5_s2048`·守候器 b8a8jv0sk):1.5B@2048 也→0=**seq 截断是元凶**(ALE 解需 4096)→ 干净测 7B 容量须 4096→**7B@4096 OOM T4→真需 H800 80G**。1.5B@2048 仍 0.22=则 7B 模型问题(蹊跷)。
- 🎯 **容量实验三组全数(6/24·全 confound-clean·OOM=0·n=9)**:1.5B@4096=**0.22**(2/9)· 1.5B@2048=**0.11**(1/9·赢 ahc005)· 7B@2048=**0.0**(0/9)。
- 🎯🎯 **H800 终判 = 暂不上(no-go for now)**:① seq 有影响(1.5B 4096→2048 valid 腰斩 0.22→0.11)② **同 2048 下 7B(0)≤ 1.5B(0.11)= 大模型没显容量优势·反更差** ③ 但 n=9 噪声大(2/1/0 胜·差异在噪声内)。**证据指向瓶颈是燃料量+题型(ALE 连续优化难蒸馏·distilled 解能跑但 0/低分)·非模型容量**。7B@4096 干净测虽须 H800,但 lukewarm 2048 信号不值现在花钱。**先做便宜的**:更多燃料(第3测 n=11 跑中·看 valid_rate 涨否)+ SWE 路。H800 = 数据-scaling 到顶 + 有理由信容量是墙 时再上。
- 🎯 **三测全数(confound-clean·OOM=0)**:1st n=6→0.0 · 2nd n=9→0.22(2胜) · **3rd n=11→0.18(2胜·ahc044/005)**。**燃料 9→11 赢题数没涨(还是 2)=小增量没推高信号**。蒸馏 ALE 泛化=**弱正但 KILLED**(0.18<<0.6·三测都 KILLED·7B 没帮·小燃料增量没帮)。
- 🎯🎯 **收敛判断(6/24)**:ALE-蒸馏在当前规模 = **弱 KILL**(便宜杠杆 fuel 9→11/7B 都试过没用)。诚实下一步 fork(待用户拍):① 大幅扩燃料 →30-50 再测(ALE 慢·强解墙)② 转 SWE 路(bug-fix 二元·可能更易蒸馏)③ 接受弱 KILL·转 V5 审计 5 断点(agent 自治维)。compass 已切回 cuda(实验完)。

## 0.5 续接更新(6/23 晚·infra 全打通后)
- ✅ **SWE verify 链证通**:gold `django-12113`=resolved:true(`--namespace none` 本地构建修 404·见 §3①)。但 **V5 2 道真 diff verify=0 A 类**(strong 没解对:12113 改了没修对/13220 diff 非法)=producer 质量非 verify 问题。**SWE park·verify 链就绪随时可验**。
- ✅ **磁盘**:datadisk0 扩到 99G(56G 空)·🔴 **根盘 50G 反复满**(结构根因=`/var/lib/containerd` 在根盘·每次 docker build 涨)·SWE django 镜像已删回收·**一切落 datadisk0 别落根盘**·偶尔 `docker container/image prune`。
- ✅ **ALE 迁 GPU 盒**(用户拍板·迁出过载 cloud):8 核·judge 复用 `ale-bench:python-202301`·ALE_OUT 写 datadisk0·distill(GPU)vs judge(CPU)并行不冲突。+ 用户授权杀 cloud 僵死 `nautilus_v5.main_singleton`(90% 空转)。**V5 执行中**。
- **球在 V5**:杀 daemon + 迁 ALE → 8 核爬 A 类 7→10-12 = trigger soul LOO。

## 1. 一句话现状
- ✅ **over-fit PROVEN**:蒸馏机制证活(train_loss 0.0003·distilled 精确复现 strong 解)·4 次 KILLED 全是 confound(已揪清)·commit `70948752d`。
- 🔴 **held-out 首证 = KILLED·confound-clean**(3-fold LOO·6 道 ALE A 类·distilled 全 0 不泛化)= **第一个真负结果(非工具 bug)**·证 **4 训练样本太少**·非 distillation 死刑。
- **唯一开放问题**:**距离够大的 A 类燃料,distilled 能否泛化?**(记忆→泛化相变需远多于 4·通常数百-千例)

## 1. 🔴 RESUME TRIGGER(怎么知道该接 + 接什么)
**触发 = V5 的 overnight 迭代救活批量跑完并 merge/re-sync 到 GPU 盒。**
- V5 在跑:26 道 strong=0 → 4-turn 迭代救活(ahc002 已证 `[0,1149634,0,0]`→A 类)。输出 `/home/ubuntu/conductor/ale_fuel_iter.jsonl`(V5 盒)→ 跑完 V5 merge 进主池 → 重 sync 到 GPU 盒 `/mnt/datadisk0/distill-code/ale_fuel_records.jsonl`。
- **先确认扩料到了**:
```bash
ssh gpu 'cd /mnt/datadisk0/distill-code && python3 -c "
import json
recs=[json.loads(l) for l in open(\"ale_fuel_records.jsonl\") if l.strip()]
print(\"total records:\", len(recs))
import sys; sys.path.insert(0,\".\")
from services.distill_mint_runner import ingest_fuel_records
s=[]; r=ingest_fuel_records(recs,kind=\"ale\",sink=s.append,ale_rel_margin=0.2)
print(\"A类:\", len(r[\"a_bucket\"]), r[\"a_bucket\"])
"'
```
- A 类 **从 6 涨到 ≥10-12** = 扩料到了,跑下面;还是 6 = V5 没跑完,等/ping V5。

## 2. 🔴 EXACT 重跑命令(扩料后·泛化第 2 测)
```bash
# 过滤超长题(ahc008 类·6170>4096 截解尾)+ 跑 LOO(料够用 LOO·≤8 用 --k 0=LOO·>8 用 --k 4)
ssh gpu 'cd /mnt/datadisk0/distill-code && python3 -c "
import json
recs=[json.loads(l) for l in open(\"ale_fuel_records.jsonl\") if l.strip()]
recs=[r for r in recs if r.get(\"task_id\")!=\"ahc008\"]
open(\"ale_fuel_noahc008.jsonl\",\"w\").write(\"\".join(json.dumps(r,ensure_ascii=False)+\"\n\" for r in recs))
print(\"filtered:\",len(recs))
" && rm -rf loo_run2 && setsid bash -c "/mnt/datadisk0/distill-venv/bin/python scripts/distill_loo.py --records ale_fuel_noahc008.jsonl --workdir loo_run2 --base-model Qwen/Qwen2.5-Coder-1.5B-Instruct --k 4 --epochs 3 > loo2.log 2>&1" < /dev/null & echo launched'
# 等结果(后台·~1hr·proc慢因max_new_tokens 4096):
ssh gpu 'until [ -f /mnt/datadisk0/distill-code/loo_run2/loo_result.json ]; do sleep 30; done; cat /mnt/datadisk0/distill-code/loo_run2/loo_result.json'
```
- **判据**:win_rate_vs_base > 0.5 + 正 uplift on 扩大 held-out = **distillation 泛化首证(中心环真闭合)**;仍 0 = 继续扩料 / 转 SWE(下)。
- confound 自动旁注(已接 distill_eval):`.pertask.json` 有 `confound_checks`·KILLED 先看 adapter_effective/solution_nonempty 是否 ok(否=别信 verdict 先排 confound)。

## 3. 第 2 条泛化路(已开·球在 V5 产 diff)
SWE bug-fix 结构比 ALE 独立优化题**更可转移** → 可能更少样本就泛化。**6/23 已 mint 3 道 specs**。
- ✅ **specs 已 mint**:GPU 盒 `/home/ubuntu/swe_specs.jsonl`(3 道 django 易/中/难·单文件·全过 `edit_paths⊆original_files.keys`)。批量 minter=`scratchpad/mint_swe_specs_batch.py`(GPU 盒 `/home/ubuntu/`·可复用·改 N_PICK/跨仓再 mint)。
- **球在 V5**:scp specs→cloud `/tmp/ale_fuel_run/swe_specs.jsonl` → `swe_fuel_batch`(keys 在 cloud)产 strong/doubao 双 diff → 回传 GPU 盒 `/home/ubuntu/` = trigger soul verify。
- soul:收 diff → SWE verify(GPU 盒 resolve env)→ 攒 SWE A 类 → 同 `distill_loo.py`(per-record kind=swe)= 路2 泛化测。**下批跨仓**(flask/requests/sympy)增多样性。
- V5 schema 契约:3 必需 `task_id`/`problem_statement`/`edit_paths` + `original_files`(key⊇edit_paths)。
- 🔴🔴 **SWE verify de-risk(6/23·gold smoke 抓到 2 个真 blocker·trace 见下)**:
  - **① 已修**:swebench 4.1.0 默认从 `swebench/` Docker Hub 拉预构镜像→多数 instance 未发布→**404 报错不本地构建**。修=`run_evaluation` 加 `--namespace none` 强制本地构建(repo + 盒 vendored `/mnt/datadisk0/swe-rsi/backend/services/swe_docker.py` 都已加)。
  - **② 未解·磁盘墙·gated 用户决策**:根盘 100% 满(已清 pip cache 救到 95%/2.9G)· **datadisk0 92%/仅 4G 空**(docker data-root 在此)。django swebench env+instance 镜像本地 build ~3-5GB → **4G 装不下且与 V5 ALE job 共盘**(build 填满会搞崩 V5 overnight)。**SWE verify 跑不了 until 扩盘/清空间**。可清候选:`rust:1.79.0-buster`(1.87G·疑未用·需确认)· 不可动=ale-bench 镜像(中心环 judge 命脉)。
  - 验 verify 通的最小动作(有盘后):`gold_verify_smoke.py django__django-12113`(gold 必 resolved=True·gpu 盒 `/home/ubuntu/`)。
- 🔴 **元教训(6/23)**:gold smoke 先验 verifier 再等 producer = de-risk 范式·抓到 404+磁盘墙·避免 V5 diff 堆积才发现"装环境地狱"。

## 4. 跨框球(都在自驱·不靠我盯)
- **V5**:① 26 道迭代 overnight → merge → 重 sync(主动)② SWE specs 一落即产双 diff。
- **compass**:🔴 **实查纠错(6/23)=compass daemon 仍 `ZMM_DEVICE=cuda`·占 T4 4.5G**(非 12G·那是过期数·"已切 CPU 释 16GB"从没真生效=改了没验的坑)。T4 16G - 4.5G = 11.8G 空·1.5B QLoRA(~4-8G)够·**GPU 非瓶颈不用动 compass**。要上 7B(需 12-16G)才切 compass CPU 释 4.5G(代价=全框 recall 走 CPU 变慢)。
- **soul(下个 session)**:扩料到→§2 重跑;决定是否开 §3 SWE。

## 5. 关键 gotcha(别重踩)
- **SSH 走 `ssh gpu`**(别名已配·`~/.ssh/config`)。GPU 盒=43.166.8.20=VM-0-13=Tesla T4·内网 172.29.0.13。
- 🟢 **SSH 加固已完成+已验证(6/23)**:reset×3 是**瞬时突发**(多框+scp 撞·非持续高负载·连上时盒子 load 0.16 很闲)。加固 drop-in `/etc/ssh/sshd_config.d/99-nautilus-hardening.conf`:**MaxStartups 200:30:500**(主配置第124行旧 100:30:200 已注释·消冲突)+ MaxSessions 50 + LoginGraceTime 30 + ClientAlive 60s·**`sshd -T` 确认 live 生效**(上次改完没验的坑这次补了)。若再 reset:大概率仍是瞬时突发→退避重试即可(`scratchpad/ssh_watch_harden.sh` 守候器·连上自动探数)·别再盲改 sshd。
- **eval 慢**(max_new_tokens 4096·模型在没见过题 ramble 到满 budget)·12 样本 LOO ≈ 2-3hr·setsid 后台跑别前台等。
- **prompt 必须对齐训练模板**(`### Instruction/Problem/Solution`·非 chat template)·`_distill_runtime` 已修(prompt-skew 是第 4 confound)。
- **judge_version 全链锁同版**(ale_eval 202301)·别用 ALE_MOCK_SCORE。
- distill_loo workdir 用绝对路径(已修)·`/mnt/datadisk0` 偶发文件不一致先 `sync`。

## 6. 自举阶梯(§泛化 PROVEN 后才建)
`docs/plans/2026-06-23-bootstrap-ladder-design.md`:viability=泛化(本 gate)·PROVEN 才阶段1(distilled-v1 produce strong=0 残余·数净贡献)。**泛化没证前不建阶梯**(反 facade)。

— 交接 soul · 2026-06-23(蒸馏机制证活 + 泛化首证真负=4太少·续接=扩料重跑 LOO·防烂尾照命令跑)
