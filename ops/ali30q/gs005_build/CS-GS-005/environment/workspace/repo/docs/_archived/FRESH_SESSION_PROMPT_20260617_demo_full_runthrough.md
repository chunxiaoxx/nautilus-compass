# /goal 提示词 · platform-soul · 2026-06-17 凌晨(明早给甲方 demo·全面跑通三台两环)

我是 platform-soul(nautilus-core 对话框 = 后台引擎)。**夜里全面完成 demo-prep,明早给甲方 demo「全面跑通」。**

## Session-start 必读
- `FDE_BUSINESS_CHARTER.md`(业务 SSOT)
- memory:`session_20260616_fde_runner_deployed_flywheel_validated_soulfix`(本轮 binding-DONE 全在此)/ `reference_two_fde_systems_convergence_map_20260615`(前台 nautilus-FDE↔后台我)/ `feedback_close_one_real_loop_before_new_fronts_20260614`(防掰玉米·demo 要真自转不要假数据)/ `gotcha_feishu_bot_as_base_member_crossapp_write_20260615`
- 🔴🔴 **保密红线**:demo 受众 = **甲方(保密大厂)**。任何 demo surface / 表 / 看板 / 话术 **绝不出现甲方名**。我方 = 伊洛科技。

## 🔴 唯一 P0 = 明早给甲方 demo 三台两环「全面跑通」
**Demo surfaces(甲方会看·每个都要有真数据、能打开、能自转)**:
1. **飞书多维表格**:RGDK `v06_派活`(`tblfPoDrZzKHpU36`)+ `v06_审计日志`(`tblqX49MQooUZjKH`)+ Dx2qb `交付表`(`tblFkmEKTk4LIWJM`)/`结算表`(`tblFL7y3DejBQUvm`)
2. **网页看板**:`https://nautilus.social/api/platform/rsi-fde/dashboard`(🔁RSI飞轮卡)
3. **平台 control 页面**:`https://nautilus.social/control`(ControlCenterPage)
4. **我们的飞书应用(内嵌 agent)**

**胜利条件(closeable)**:
1. 飞轮看板**自转**(settled 数自动涨·无需手 mint)
2. FDE 业务环 **≥5 道真任务**在飞书表可见(派活→QC→交付→结算·**结算应付真数字**非 None)
3. 每个 demo surface **亲自打开截图确认**能看(飞书表/网页看板/control 页/飞书应用)
4. **demo runbook** 写好(用户能照着演一遍)

## ✅ binding-DONE 本轮(别重验·别重做)
- S2/S3 runner 部署 FDE host `/opt/ecc-shared/runner/platform_soul/`(11文件自包含 + `assemble_tutorial.py` + `.env` 含 `FDE_TUTORIAL_ASSEMBLER`)·DRY_RUN s2/s3 远端 green。
- **RSI 飞轮端到端验证两次**:mint d2 → V5 agent `nautilus-prime-001` claim → `qwen3.7-max` produce(code_fix)→ `compass/bench_eval` reward=1.0 → settled。`scripts/mint_one_open.py`(单发留 open·cloud 上跑)。
- **soul 双判 code-fix 已修**(soul-scorer skip `kind==code-fix-with-deterministic-verifier`·commit 37a117f09·生产日志验 `skipped=[uid]`)。
- **line 路由已修**(业务线「2·教案」≠「2」→ `line_code()`·commit 5867cd113·17 TDD green)。
- **真教案任务全生命周期通**(`expert_line2_persona_drift_20260616`·派活→提交→QC 5/5→交付4段买方格式→结算·行=已交付·Dx2qb 有真数据·record `recvmIvql5PR6g`)。
- 反向写测(bot `ou_af25f91ccc5cd9e39d120615006df974` RGDK editor 验)·`scripts/seed_real_t2_task.py`(walking-skeleton 驱动)。

## 🌙 夜里要完成(按优先级·每件带验收)

### A. 飞轮 auto-mint timer(demo 最有冲击力=飞轮自转)
- 原 gate(等 V5 code-fix produce)**已满足**(本轮验证 V5 消费路径 reward=1.0)→ 可开。
- 建 auto-mint poller:维持 marketplace 有 1-2 道 open code-fix 题(从本地 `~/fde_t3_scratch/compass_bench/*/` 或燃料 base `EOVhbQwA0a1HEOsgmxecgkBVnwh`/`tblvR6BCSBH4IG59` 取·**fresh uid per mint 防 verdict-join 遮蔽**·去重)→ POST `/dispatch`(`PLATFORM_DISPATCH_KEY` 在 cloud .env)。
- **复用 `scripts/mint_one_open.py` + `services/fde_poller.py` 模式·别重造**。
- 部署 cloud systemd timer(**镜像 `fde-bench.timer`**:建 `/home/ubuntu/auto-mint/` 自包含 + run.sh + `.timer` 每 5min)。
- ⚠️ 限流:poller 维持 ≤2 open·燃料池耗尽即停·别无限 mint clutter。
- **验收**:看板飞轮 settled 数自动增长(open→claim→produce→bench_eval→settle 全自动)·无需手 mint。

### B. 应付金额真算 wire(结算 demo 显真数字)
- `services/fde_expert_rates.py` 已有 `parse_expert_rates`/`compute_payable`/`price_settlement`(8 TDD green)。
- wire 进 s3(`services/fde_delivery.py build_settlement_record` 或 `fde_delivery_runner`):读 RGDK `v06_行业专家`(`tblQChALfBACGLYB`).工时单价 × `v06_派活`.工时 → 应付金额。
- TDD → scp FDE host runner → 重跑 s3 那道教案 → 验 Dx2qb 结算表 应付金额 = 真数字(现 None/pending)。
- **验收**:结算表 应付金额 有真值。
- 注意:v06_行业专家 表若没「平台专家#1」的单价行,先补一行(或 seed 任务用已有专家名)。

### C. Demo 数据厚度(≥5 道真任务)
- seed 3-4 道更多真 walking-skeleton 任务(`scripts/seed_real_t2_task.py` 改 uid/内容·用**真实平台一手 dev 经验**·标 provisional)→ 跑 S2/S3 → 飞书表 + Dx2qb 有 ≥5 道。
- 第1类(出题)也可掺 1-2 道展示双线(出题=checklist LLM judge·需 LLM key·教案=line2 确定性)。
- 🔴 内容真实(平台/各 agent 真实开发经验)·标 provisional·**别编造**。

### D. Demo 可视化核实(每个 surface 亲自浏览器打开看 + 截图)
- 用 MCP `browser_navigate` + `browser_take_screenshot`(host.docker.internal 若需)。
- 飞书表(需登录·可能截 API 读回的结构化数据代替)/ 网页看板 `rsi-fde/dashboard` / `/control` 页 / 飞书应用。
- 修任何渲染坏的:前端 canonical=master·build→部署 `/var/www/nautilus/current`(先备份 `current_backup_$(date)`)。
- **验收**:每个 surface 截图确认能看·发给用户 SendUserFile。

### E. Demo runbook(现场一键演)
- 写 `docs/DEMO_RUNBOOK_20260617.md`:每个 surface URL/表 + 一句话讲解 + 演示顺序 + 若 FDE 自动化没配则现场跑 runner 的命令。
- **验收**:用户能照着跑一遍。

## 依赖他方(非我 turf·已转发·别等·有兜底)
- **FDE** 配 RGDK feishu 自动化(中台 auto-trigger)→ 配好 = FDE 环全自动;**没配则 demo 现场跑 runner**(同命令·`ssh fde-cloud 'cd /opt/ecc-shared/runner/platform_soul && python3 s2_auto_qc.py'`)。
- **V5** 棘轮(已验证消费路径·棘轮是后续增强·**不卡 demo**)。

## 凭据/IDs/gotchas(全)
- 我引擎 app `cli_aaa8e75d`(`~/.claude/.cache/.fde_api_secrets.env`:FEISHU_APP_ID/SECRET·BAILIAN_API_KEY=deepseek-v4-pro·拉数 `PYTHONUTF8=1`)。
- cloud=`ssh cloud`(43.160.239.61:**24860**)·backend `/home/ubuntu/nautilus-mvp/phase3/backend/.env`(`PLATFORM_DISPATCH_KEY`·`DATABASE_URL`)·**分叉·外科 scp 单文件·勿 git pull·改完 `sudo systemctl restart nautilus-backend`**。
- FDE host=`ssh fde-cloud`(VM-0-8-ubuntu)·runner `/opt/ecc-shared/runner/platform_soul/`·webhook 8848(`webhook.service`+`webhook-2`)。
- RGDK base `RGDKbrtZ1aMcEOsZ2GcczeFknNg`(v06_派活 `tblfPoDrZzKHpU36`·审计 `tblqX49MQooUZjKH`·行业专家 `tblQChALfBACGLYB`)。
- Dx2qb base `Dx2qb1fjhaJadSs0ZeMc0teVn49`(交付 `tblFkmEKTk4LIWJM`·结算 `tblFL7y3DejBQUvm`)。
- 燃料 base `EOVhbQwA0a1HEOsgmxecgkBVnwh`/`tblvR6BCSBH4IG59`(10行·只 L3)·本地燃料 `~/fde_t3_scratch/compass_bench/*/`(c2/c2b/c2c/c2d/c2e/c3/d1/d2/f1/f2)。
- 端点:dispatch `POST nautilus.social/api/platform/fde/dispatch`(`X-Platform-Key`)·verdict `POST .../verdict`(免鉴权)·`GET .../tasks`·看板 `.../rsi-fde/dashboard`。
- cloud timers:`fde-bench.timer`(每2min·bench_eval 自驱 verify)·`soul-scorer.timer`(每2min·教案/出题 QC)·`fde-assignment.timer`。自包含目录 `/home/ubuntu/{soul-scorer,fde-bench}/`(run.sh exec python3·timer 每 fire 起新进程·改 services 外科 scp 单文件即生效)。
- 🔴 gotchas:① **bash `/tmp` ≠ Windows-python `/tmp`**(写文件用 bash echo 或统一路径)② **assemble_tutorial.py 必须随 runner 部署**(line2 QC 依赖·6/16 实证漏带→教案 QC 全 failed)③ 飞书单选改 options 必带 id 否则清空既有值 ④ 我机器→nautilus.social/GitHub 偶发 SSL 抖动·走 `ssh cloud` localhost 可靠 ⑤ verdict-join 防遮蔽:每版 fresh uid。

## git 状态
master 本地有本轮提交**未 push**(dc29a008a runner / 37a117f09 soul-fix / 5867cd113 line_code / cfcf2badd V5coord / +compass coord)·**部署走 scp 非 git**·新 session 继续提交 master 不 push(R4)·若要 V5/compass 走 GitHub 通道读 outbound 才 push。

## 纪律
#1 agent-first · #3 反 D(**真流通+全自动 > 埋代码·demo 要真自转不要假数据**)· #4 单一 forcing function=demo 全面跑通 · #5 整合现有(mint_one_open/fde_poller/fde_expert_rates/部署模式)别重造 · #6 gotcha 先读·诚实(交付 provisional·demo 别 overclaim·飞轮是真自转)· 🔴 保密:甲方 demo 任何 surface 绝不提甲方名。
