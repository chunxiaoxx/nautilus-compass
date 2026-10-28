# /goal · platform-soul · 2026-06-22 · 落地 FrontierSWE 类飞轮(第一类高价值自转闭环)

我是 platform-soul(nautilus-core·phase3/backend·FDE 后台引擎 + RSI 飞轮 verify/mint turf)。

## 元规则(铁律)
- 先验证后动手·诚实·**报 LIVE 前必 grounding 亲测**(daemon 验 systemctl MainPID==端口持有者+lstart·非 etime;血教训)。
- 第 1 个 response 报 active anchor(#2 RSI 闭环·#3 反 D 规划必落地·#1 agent 自治)。
- 🔴🔴 **规划必落地·不再重规划**(用户 6/21 铁律):**充分用已建机制·外化上下文到 memory/文件不押注人脑(这本身是 RSI 燃料)·小的运行切片 > 大设计文档·我当"运行强制者":任何"先设计个 X"前先确认能否接现有已跑飞轮**。
- 🔴 **飞轮别变 facade**(V5 认知审计警示):churn ≠ 变强·产 artifact ≠ 回灌行为·要真能力梯度非 reward 饱和微调·记忆→动作回路要真闭。

## 北极星(单一真相源·先读不重发现)
**12 类飞轮收敛 = memory `strategy_12category_flywheel_convergence_use_existing_20260621`**:甲方 12 类基准 + RSI = 同生产线。飞轮已自转(auto-mint 1287 settled)但喂易 dev-历史经验题(全 pass=liveness churn 无递归信号·未对齐 12 类)→ 收敛 = **换甲方级难燃料(double-gate 筛 true_wall)+ 打 buyer_category 标 = 一鱼两吃**。SWE≈FrontierSWE(甲方第 6 类)。零新设计·全用现有件。

## 唯一 forcing function = 落地 FrontierSWE 类飞轮(binding-DONE·冻结 scope)
**P0(gated 等 V5 produce root-fix ping·合约 cnt_v5_soul_produce_rootfix_restart due 6/22)**:
1. 开场读未读 → 有 V5 produce-rootfix+restart ping → **grounding 验 daemon 新码**(systemctl MainPID==:8001 持有者·非孤儿·lstart 分钟级)
2. **re-mint 3362** 验跨题复利:`ssh -p24860 cloud 'export PLATFORM_DISPATCH_KEY=$(grep ^PLATFORM_DISPATCH_KEY= ~/nautilus-mvp/phase3/backend/.env|cut -d= -f2-|tr -d "\""); cd /home/ubuntu/fde-double-gate && python3 scripts/mint_swe_fuel.py psf__requests-3362 requests --swe-repo psf/requests --turn1 2 --turn2 6 --n-f2p 1 --prep-file prep_requests3362.json'`(prep 已在 cloud)
3. 监控 daemon claim→produce **干净 diff**(code=swe-unified-diff·非空 n_files>0)→ fde-bench.timer 自动 SWE verify(GPU)→ settle → V5 W1 写回 bench_family=requests
4. **验收**:3362 settled + verdict source=compass/bench_eval + W2 召回到题1(2148)learning(=跨题复利真证·非单题首证)
5. 绿 → **翻 SWE auto-mint 开关**(见 P1)= FrontierSWE 类飞轮自转

**P1(P0 绿后·我的 turf·让它自转·✅ 已建 OFF-ready)**:SWE auto-mint sibling **已建好** `/home/ubuntu/swe-automint/`(swe_automint_poll.py + service + timer·DISABLED·dry 验过)·镜像 auto_mint_poll 模式·网络无关池(2148 models.py + 3362 utils.py·排除 2317 联网)·防重(在途 instance 跳过)+ 产量 cap(TARGET_OPEN_SWE=1)·fresh-uid。**P0 绿后一键开**:`ssh -p24860 cloud 'sudo systemctl enable --now swe-automint.timer'` → FrontierSWE 飞轮自churn。reaper/drain/janitor/eval-超时 已是安全网。
- 待补(小·非阻塞):`buyer_category=FrontierSWE` 标(mint_swe_fuel 加 1 字段·买方交付时用)· 扩池(更多网络无关甲方级难 instance·等 compass HF 清单)。

**没 V5 ping 先做(不空转·my-turf)**:SWE auto-mint 已 OFF-ready(✅)。可:① 扩网络无关燃料池(compass HF 清单到了)② buyer_category 字段 ③ 复查 infra LIVE。**别盲 mint(produce 没修=空 diff)**。

## LIVE 清单(已建·勿重造·anchor #5)
- reaper(claimed→open)+ drain(produced-error→abandoned)+ **fde-janitor.timer**(每10min 自维护队列)= 队列自治 · commit 7d0b1d7b6/55d751547
- **eval 超时治本**(remote_swe_eval 1200s + 超时清远端孤儿)· commit 7493bfa76
- auto-mint 飞轮(compass_exp 燃料·1287 settled·TARGET_OPEN=1)= RSI 飞轮 infra 自转模板
- double-gate(true_wall 分桶筛甲方级难)· SWE verify-side(is_swe_task→swe_docker.remote_swe_eval)· mint 内嵌原文(mint_swe_fuel --prep-file)
- 题1 SWE 燃料环首证闭(2148·f2p 10/10 resolved·W1 6/6)

## turf 不重建
soul=双门/SWE verify/mint/队列自治 infra;V5=daemon produce/diff producer/W1W2/produce root-fix;compass=GPU env/bench_eval/KernelBench+AutoLab 燃料/charter 维护/OKF-GEP 融合(插已跑飞轮当记忆层);platform=dispatch/claim/verdict/buyer_category 透传。

## 跨框待办(球态·6/22)
- **V5**:produce root-fix(非 band-aid·换非 reasoning producer)+ clean restart → ping soul(合约 due 6/22)· 认知断回路 root-fix(记忆→动作 / 棘轮 reward 梯度 / 反 facade)
- **compass**:charter 更新到 12 类(ALE 第12)· KernelBench/AutoLab 燃料打 category 标接 auto-mint · OKF/GEP 插已跑飞轮 · HF 查网络无关 instance 清单
- **soul(我)**:P0(等 ping)+ P1 备好

## 坐标
- memory:`strategy_12category_flywheel_convergence_use_existing_20260621`(北极星)· `session_20260620_swe_fuel_loop_CLOSED_bucketA_first_proof`(全状态·gotcha)· `fde_business_charter_ssot_must_read_20260609`
- 业务基线:`FDE_BUSINESS_CHARTER.md`(12 类权威 §1.3)
- broadcast:`_OUTBOUND_FROM_PLATFORM_SOUL_BROADCAST_20260621_12category_flywheel_convergence_use_existing.md`
- 合约:cnt_v5_soul_produce_rootfix_restart(V5→soul·due 6/22)
- creds:`~/.claude/.cache/.fde_api_secrets.env`(已 scp cloud)· PLATFORM_DISPATCH_KEY 在 cloud `~/nautilus-mvp/phase3/backend/.env`
- infra:cloud `ssh -p24860`(dispatch localhost:8000·我出口 IP 1.192.65.33+216.36.114.95 已 fail2ban 白名单)· GPU box `ubuntu@43.166.8.20`(swebench/Docker·密钥 /tmp/gpu.pem)
- 跨框:`_OUTBOUND_FROM_PLATFORM_SOUL_TO_<X>_*.md` / `_OUTBOUND_FROM_<X>_TO_PLATFORM_SOUL_*.md`

## 起手
① 报 anchor ② 读未读(V5 produce-rootfix ping?)③ 有 → grounding 验 daemon → P0 re-mint 3362 闭跨题复利 → 绿则开 SWE auto-mint;无 → P1 备 SWE auto-mint+燃料池(OFF·不空转)④ 闭环达成 → PoI+memory+outbound 三框 ⑤ binding-DONE·负结论 ABORT 不硬撑·不重复盲试。
