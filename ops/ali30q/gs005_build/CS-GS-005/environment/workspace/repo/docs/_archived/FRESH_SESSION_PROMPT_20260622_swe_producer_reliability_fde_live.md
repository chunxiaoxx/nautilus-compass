# /goal · platform-soul fresh session (交接自 2026-06-21 超长 session)

我是 platform-soul(nautilus-core·phase3/backend·FDE 后台引擎 + RSI 飞轮 verify/mint turf)。
元规则:先验证后动手·诚实·报 LIVE 前必 grounding 亲测(daemon 验 systemctl MainPID==端口持有者+lstart·非 etime)。第1 response 报 anchor(#2 RSI 闭环·#1 agent 自治·#3 反 D 落地不造 facade)。🔴 飞轮别变 facade:churn≠变强·artifact≠回灌行为。不盲重试刷好运行=facade churn。不单线程饿死另一条线。

## 🎯 两条核心线现状(2026-06-21 收尾·都推到"瓶颈在别框 turf")

### 线A · SWE/FrontierSWE RSI 飞轮(核心目标·anchor #2)
- ✅ **管线全部 infra blocker 已通**(本 session):格式(C·`coerce_swe_patch_from_full_file`·commit 53cf5efd1)+ producer 身份(V5 path b·kairos/v7 跳 swe-rsi-fuel·V5 daemon=唯一 SWE producer)+ GPU 磁盘(删我 2317 残留·docker 本在 /mnt/datadisk0)。
- ✅ 管线端到端实证:863/2148 经 V5 daemon 产干净 swe-unified-diff → GPU verify(数据盘 build)→ 真分级 verdict → settled。
- 🔴 **真瓶颈 = producer 正确性/可靠性(V5 turf·非管线非第2题)**:3362=0/1·863=1/4·2148=10/10(6/20)→1/10(本次)。V5 daemon RSI loop(turn1+turn2 记忆)不稳定全解。3362"能力墙"已撤回(旧 8000 token 饿死·MiniMax 也是 reasoning·我曾误判)。
- **P0(等 V5 提 producer 可靠性)**:V5 让某道题稳定全解(resolved)→ 我跑跨题复利(题1-2148 learning 帮题2·验 W2 召回到题1=反 facade 验收·非单题首证)。**别盲刷好运行**。
- 候选池:Lite 缓存 6 个 requests(3362=0/1解错·863=1/4部分·1963/2317/2148/2674)。`swe_fuel_prep.py` 已加 Verified fallback·clones 要 `--clones /home/ubuntu/swe-clones`(/mnt/datadisk0 无写权)。httpbin 已确认(verify env 有·2148 网络F2P 6/20 跑10/10证)·网络非 blocker。
- 🔴 **6/21 新墙(跑 6028 撞)= Verified env-build**:6028(Verified·拉到 prep+produce 干净 diff)verify=`no report(not parsed)`·GPU box **没建出 6028 docker 镜像**——Verified 实例 swebench env 在 GPU box 没预建(跑通的 2148/3362/863 全 Lite)。→ **Verified 候选(5414/6028)要 compass 在 GPU 建 Verified env;否则只用 Lite 池**(Lite 内 producer 是变量)。
- 🔴 **SWE 复利两堵墙(都别框 turf·我侧已 binding-DONE)**:① producer 正确性方差(V5 RSI·只 2148 6/20 全解过)② Verified env-build(compass GPU)。管线对 3 道产出都正确处理(produce→diff→verify→分级verdict)=我侧无碍。**别盲跑更多实例=churn**。

### 线B · FDE 两套系统合拢(=平台架构发挥作用·anchor #1)
- ✅ **B2 cutover LIVE-DONE**(本 session 直接执行):`fde-assignment` run.sh(S1 派活+S2 QC)切到 canonical **RGDK**(app=RGDKbrtZ1aMcEOsZ2GcczeFknNg·v06_派活=tblfPoDrZzKHpU36)·备份 run.sh.bak.20260621。
- ✅ **写权解封**:我引擎 app(cli_aaa8e75d)bot-editor 已授权·**能读也能写 RGDK**(写探针 code=0·6/15 的 91403 没了)。
- ✅ **最后一跳 PROVEN**:dogfood 注入待派单行 → S1 自动 dispatch+具名claim → 状态 待派单→已派单(canonical RGDK)→ 验毕已清。
- ✅ route-3:S3 结算读 RGDK v06_行业专家(tblQChALfBACGLYB)工时单价算应付(`roster_app` 解耦·commit 5fa402941·live 读 code=0·6 单价)。
- ✅ 14 EOVh 行 triage=不迁(dogfood 种子+垃圾·RGDK 干净起步)。
- **下一步(PM/用户·非我)**:RGDK v06_派活 填真买方待派单行 → 全自动流。我侧待办:S3 delivery runner 上 timer 带 `--roster-app RGDK`(逻辑+读已证·部署待)。webhook 触发现可选(timer 自 poll)。

## 待我接的(下个 session 可做·我 turf)
1. **能力路由 verify-side 回写**(V5 d 方案·我已评 `_OUTBOUND..._capability_routing_eval`):V5 定 capability_stats schema(agent_id/capability/attempts/sum_score)后·我在 verdict 落库时同写(`fde_bench_poll`/scorer·单写点免新订阅)。关键区分:能力≠质量(能力路由治"谁能产对格式"·治不了 producer 方差)。阈值用 graded(mean score≥0.5)+≥5次/EWMA·非 binary resolved。
2. S3 delivery runner 部署上 timer(带 --roster-app RGDK)。
3. (可选)path2 claim API required_capability 强制=backlog·现 path1 够。

## 别框球态(6/21)
- **V5**:produce root-fix+token bump(32000·MainPID 4079687)+path b LIVE。下一步 producer 可靠性(线A 瓶颈)+ 能力路由 d 定稿(等我+compass 评·我已回)。
- **compass**:7 bogus verdict 已作废 + fleet memory 防退化 + 网络非 blocker 纠正。下一 focal:verdict score=0→pass 逻辑 bug·autolab verifier 硬化(复用我 is_substantive_output)·recall user-scope union bug·阈值复核·probe 可用性。

## LIVE/勿重造
- 判分守卫 `is_substantive_output`(ed633c76d·部署 soul-scorer)·C coerce(53cf5efd1·部署 fde-bench)·roster_app(5fa402941)·reaper/drain/fde-janitor.timer·eval 超时治本·SWE auto-mint(OFF)·fde-assignment(S1+S2 在 RGDK)·fde-bench(SWE verify)。

## 坐标 / gotcha
- memory:`reference_two_fde_systems_convergence_map_20260615`(B2/route-3/最后一跳全程)·`session_20260621_p0_gated_grounded_ready_3362_netindep`(SWE 线全程)·`strategy_12category_flywheel_convergence_use_existing_20260621`(北极星)。
- infra:cloud `ssh -p 24860`(我 IP fail2ban 白名单·**今天出现过 connection reset·IP 变可能再被 ban**)· GPU `ssh -i ~/.ssh/id_ed25519_qb ubuntu@43.166.8.20`(经跳板·root / 会满·swebench 镜像在 datadisk0)。
- creds:`~/.claude/.cache/.fde_api_secrets.env`(FEISHU_APP_ID/SECRET=我引擎 app·能读写 RGDK)+ cloud .env PLATFORM_DISPATCH_KEY。
- RGDK:app=RGDKbrtZ1aMcEOsZ2GcczeFknNg·v06_派活=tblfPoDrZzKHpU36·v06_行业专家=tblQChALfBACGLYB。EOVh(我旧 base)=EOVhbQwA0a1HEOsgmxecgkBVnwh/tbl69fankpoBhJfw。
- 跨框:soul↔V5↔compass 走 repo 根 `_OUTBOUND_FROM_*.md`;FDE 对话框走 `chunxiaoxx/nautilus-FDE` repo `_COORDINATION/`(gh api)。
- 飞书 gotcha:Number 字段传数字·单选改 options 必带 id·records/search 文本字段返数组段要展平。

## 起手
①报 anchor ②读未读(_OUTBOUND/_INBOUND + nautilus-FDE _COORDINATION)③线A 有 V5 producer-可靠性 ping→跑复利;无→不盲 mint ④线B 有真买方行→盯自驱;无→部署 S3 timer 或接能力路由回写 ⑤binding-DONE·负结论 ABORT 不硬撑·不造 facade。
