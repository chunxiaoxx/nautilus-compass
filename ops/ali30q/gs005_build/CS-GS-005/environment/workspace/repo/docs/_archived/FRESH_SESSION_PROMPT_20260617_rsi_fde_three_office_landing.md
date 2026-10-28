# /goal 提示词 · platform-soul · 2026-06-17(全力推进 RSI+FDE 落地 + FDE 对接 + 前台/后台/中台)

我是 platform-soul(nautilus-core 对话框 = 后台引擎)。

## Session-start 必读
- `FDE_BUSINESS_CHARTER.md`(业务 SSOT)
- memory:`session_20260615_rsi_flywheel_deterministic_verify_wired_first_turn`(飞轮全程)/ `gotcha_nginx_boot_dns_upstream_fails_whole_site_20260616`(服务器三根因+诊断铁律)/ `reference_two_fde_systems_convergence_map_20260615`(两套系统收敛)/ `feedback_close_one_real_loop_before_new_fronts_20260614`(防掰玉米)

## 🔴 唯一 P0 = 让 FDE 业务环真流一遍 + RSI 飞轮全自动,前台/后台/中台三层都落地可见

**三层定义(本 session 锚)**:
- **前台**(FDE 对话框 turf)= 客户/PM 面:飞书 RGDK base(v06_* 表)+ 文档站 fde.nautilus.social + webhook(8848·已 live)+ Playground。intake/派活/真人 review/交付。
- **后台**(我 platform turf)= 自动化引擎:dispatch substrate + verdict-bus + S1/S2/S3 runner + RSI 飞轮(bench timer)+ 部署 + 控制面看板。
- **中台**(集成层)= 连前后台:webhook→runner 桥(FDE webhook 调我 S2/S3 @ `/opt/ecc-shared/runner/platform_soul/`)+ RGDK 共享 base + bot-member 鉴权(我 bot 写 RGDK)+ verdict-bus 信号总线。

→ **胜利条件 = ① 一道真第1/2类任务从「派活→提交→QC→交付→结算」全程流一遍(前后中台都参与·可见)② RSI 飞轮 mint→produce→verify→settle 全自动转(不靠我手跑)。**

## A. FDE 业务环对接(前台↔中台↔后台·关键路径)
**卡 FDE 两件**(已发解锁 `nautilus-FDE/_COORDINATION/FROM_platform_soul_20260616_unblock_build_paihuo_table.md`·它 merge 了但还没回):
1. FDE 用 FDE app 在 RGDK 建 `v06_派活`(12 字段·我 schema + B.2 澄清)+ `v06_审计日志`(writer_source 字段)→ 发 table_id。
2. FDE 授我引擎 bot `ou_af25f91ccc5cd9e39d120615006df974` RGDK editor(`POST drive/v1/permissions/RGDKbrtZ1aMcEOsZ2GcczeFknNg/members?type=bitable` member_type=openid perm=edit·实测可行)。

**table_id + bot editor 到位后我做**(我 turf·立刻):
3. 反向写测:我 app 读/写 RGDK v06_派活 验证(我 app 已实测能读 RGDK 全部表)。
4. 部署 S2/S3 runner 到 `/opt/ecc-shared/runner/platform_soul/`(脚本在 repo `phase3/backend/runner/platform_soul/s2_auto_qc.py`+`s3_delivery_settlement.py`·薄包装调 TDD-green 的 `services/fde_qc_feedback_runner`/`fde_delivery`)+ 配 env(`FDE_BASE_TOKEN`=RGDK·`PAIHUO_TABLE_ID`=新 table_id·`FEISHU_APP_ID/SECRET`=我引擎 app)。部署法镜像 cloud `/home/ubuntu/soul-scorer/`(自包含目录)/`/home/ubuntu/fde-bench/`。
5. 跑 1 道真任务全程 S1→S2→S3(派活→QC→交付→结算)。目标判据 **≥5 道真任务流一遍**。

## B. RSI 飞轮全自动(后台·两件,坐标全验)
1. **mint poller**(我 turf·坐标已验):从飞书 base `EOVhbQwA0a1HEOsgmxecgkBVnwh` / 表 `tblvR6BCSBH4IG59`(燃料·10 行·字段 `附件文件` 含 3 附件 bench_eval/buggy/spec)→ 下载附件 inline 进 description → `POST /dispatch`(cloud 侧有 `PLATFORM_DISPATCH_KEY`)。复用 `services/fde_poller.py poll_and_dispatch`。鉴权=共享 app cli_aaa8e75d(secrets 里)。
   - 🔴 **gated**:auto-mint timer **别开**,直到 V5 加 code-fix produce(V5 自报消费者"不认 code-fix"→现在自动派 code-fix 题会被消费者抢去产垃圾)。先建好、手动可跑、timer 关。
2. **V5 加 code-fix produce**(V5 turf·已同步 `_OUTBOUND_FROM_PLATFORM_SOUL_TO_V5_20260616_flywheel_prod_closed_codefix_produce_ask.md`):识别 `kind==code-fix-with-deterministic-verifier`→读 `starter_inline`→LLM 修代码→report `output.code`。加完→开 mint timer→飞轮全自动。

## ✅ 本 session 已 binding-DONE(别重验·别重建)
- RSI verify 侧:`services/fde_bench_poll.py`(15green)+`fde_bench_runner.py`(7green)+ **cloud `fde-bench.timer` 每2min 自驱**(端到端验证:produced code-fix→自动 verdict source=compass/bench_eval→settled·看板飞轮 10/10)。
- 生产 marketplace 完整 lifecycle 跑通(`scripts/flywheel_prod_turn.py`)。
- 看板:`https://nautilus.social/api/platform/rsi-fde/dashboard` 🔁RSI飞轮卡 live(10/10·已部署 platform_rsi_fde.py)。
- 服务器抢修:nginx boot-DNS 自愈(systemd 重试)+ SSH 真相(腾讯绑密钥关密码·非崩溃)+ **低噪站点看门狗**(`nautilus-site-watchdog.sh`·systemd timer·直发 @openclaw_cxchat_bot·含 compass→T4 隧道 9876/9877 监控)。
- compass cutover:bge-daemon 迁 T4·释放 ~3G(used 7.5→4.2G)·隧道纳入看门狗。
- FDE 给了我专用密钥 `ssh fde-cloud`(部署用)。

## 真数据/凭据/IDs
- 凭据:我引擎 app cli_aaa8e75d(`~/.claude/.cache/.fde_api_secrets.env` FEISHU_APP_ID/SECRET·百炼 BAILIAN_API_KEY=deepseek-v4-pro 当 code-fix produce·拉数 curl+PYTHONUTF8 避 GBK)。
- cloud:`ssh cloud`(43.160.239.61:**24860**·非22)。backend `/home/ubuntu/nautilus-mvp/phase3/backend/`(分叉·外科 scp 单文件·勿 git pull·改完 `sudo systemctl restart nautilus-backend`)。dispatch key 在该 .env。
- RSI 燃料:base `EOVhbQwA0a1HEOsgmxecgkBVnwh` / 表 `tblvR6BCSBH4IG59`(10 行·字段 `附件文件`)。
- FDE 业务:RGDK base `RGDKbrtZ1aMcEOsZ2GcczeFknNg`(v06_* 表·v06_派活待 FDE 建)·专家单价 `tblQChALfBACGLYB`。交付/结算 base `Dx2qb1fjhaJadSs0ZeMc0teVn49`。
- 端点:dispatch `POST nautilus.social/api/platform/fde/dispatch`(X-Platform-Key)·verdict `POST .../verdict`(免鉴权)·`GET .../tasks`·看板 `.../rsi-fde/dashboard`。
- ⚠️ 我机器→nautilus.social/GitHub 偶发 SSL 握手抖动(瞬时·重试或走 ssh cloud localhost 可靠)。

## 跨框协调(GitHub·发前先 fetch·别 thrash)
- FDE = `nautilus-FDE/_COORDINATION/`(本地 `C:\Users\chunx\Projects\_nautilus_fde_inspect`·可 push)。
- V5/compass = `nautilus-core` repo 根 `_OUTBOUND_FROM_PLATFORM_SOUL_TO_*` / `_OUTBOUND_FROM_{V5,COMPASS}_TO_PLATFORM_*`。compass MCP 已重连。
- 球位:FDE(建表+授 bot editor)·V5(code-fix produce)·都已同步。compass 燃料义务全交付(给了 base token)。
- 🔴 买方 pivot(compass 6/16):可解燃料题=**飞轮燃料非买方交付**;买方交付走"难倒 doubao 题"(compass kernelbench-stump 轨·见 `~/fde_t3_scratch/HANDOFF_buyer_third_class_deliverable_20260616.md`)。别把飞轮燃料当买方交付上报。

## 纪律
#1 agent-first(bot-member 落地)。#3 反 D:推真任务流通+全自动 > 埋代码/又一散页。#4 单一 forcing function=FDE 业务环真流一遍 + 飞轮全自动。#5 整合现有(soul-scorer/fde-bench 部署模式·fde_poller.py)别重造·先调研。#6 gotcha 先读·发协调前先 fetch·诚实(交付 provisional·第3类 verify 确定性门非 LLM judge)。
