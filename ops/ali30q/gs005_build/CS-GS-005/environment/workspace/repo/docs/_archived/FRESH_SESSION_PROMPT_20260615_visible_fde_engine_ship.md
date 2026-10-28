# /goal 提示词 · platform-soul · 2026-06-15 晚 → 下个 session

我是 platform-soul(nautilus-core 对话框)。Session-start 必读:`FDE_BUSINESS_CHARTER.md` + memory `feedback_close_one_real_loop_before_new_fronts_20260614`(防掰玉米)+ `reference_two_fde_systems_convergence_map_20260615`(两套系统收敛+bot成员路线)+ `gotcha_feishu_bot_as_base_member_crossapp_write_20260615`。

## 🔴 唯一 P0 = 转动 RSI 飞轮一整圈(真闭环·平台 turf·燃料已到位)+ 把它做可见(整合现有散页·不再造新页)

**为什么是这个(用户 6/15 三连批评必须内化)**:
1. 我的产出"看不见摸不着·埋在会话里"(掰玉米的另一面)。
2. 我**建过很多页面,但分散/半途而废/没维护/没整合** → **不许再造第 5 个页面**;要把现有散页整合成一个维护的真数据面。
3. compass 已产真燃料(3 道第三类可解题·确定性 verifier·reward 1.0)但喂不进 marketplace → **RSI 飞轮饿着,桥接是平台 turf(我的活)**。

→ **胜利条件 = 一道真燃料题从 marketplace 经 consumer→produce→verify→settle→PoI 真转一圈,且这一圈在一个整合的真数据面上可见。** 实质(飞轮转)+ 可见(整合面),一体。

## A. 飞轮桥接(真闭环·平台 turf·先做)
compass 燃料在飞书经验表 `tblvR6BCSBH4IG59`(code-fix 题·确定性 bench_eval verifier·reward 1.0·行 c2c=`recvmyidEsTqJ0`/C3=`recvmy00Ec9i42`/c2d=`recvmD0KDV9oCF`)。compass `submit_platform_task` 写文件队列卡死(COMPASS_PLATFORM_QUEUE_URL 未设·3 题 error)。consumer 只 drain HTTP `localhost:8000/api/platform/fde`(现 0 open·饿)。喂料口 `POST /api/platform/fde/dispatch {task_uid,title,description}` 需 `X-Platform-Key`(admin·平台侧)。

**平台决策(我倾向 b·security 更好)**:
- **(b 推荐)平台侧 poller 从飞书 `tblvR6BCSBH4IG59` 拉题 → mint 进 marketplace(dispatch)**。admin key 留平台侧·复用 S1 poller 模式·走飞书 substrate(整合方向一致)。= 扩 S1 加"第3类燃料源"。
- (a)给 compass X-Platform-Key + 指 COMPASS_PLATFORM_QUEUE_URL 到 dispatch —— 把 admin key 交另一框·security 差·不推荐。
- 🔴 **必须确认 verify 链真跑**:dispatch→claim→produce→**verify(第3类=跑 compass bench_eval 确定性门·非 soul checklist)**→settle→PoI。否则 consumer 产出无 reward 信号、棘轮不转。第3类 verify ≠ 第1/2类 QC,要 wire bench_eval verifier。
- 实测验:mint 1 道 → 看 V5 consumer 是否 claim→produce → verify 出 reward → settle → PoI 累积。**这一圈真转 = P0 达成。**

## B. 可见面(整合现有散页·不造新·喂 A 的真数据)
🔴 **先 audit 现有页面再动**(用户:别再造分散页)。已知散落:
- `/control` ControlCenterPage(脉搏+LoopReplay+rerun·nautilus.social·登录后)。
- W-A 看板(verdict/agent/event)。`/demo` 系列(PR#136)。前端多版本(line/master/fork·别弄混·见 `frontend_version_map_dont_mix_20260606`)。
- 控制面聚合 API `GET /api/platform/control-plane`(8001 脊柱·LIVE)。
→ **整合成一个 canonical 维护面**(不是第 5 个):脉搏 + 飞轮活转(A 的 PoI/reward 流)+ 真交付物(S3 drift·Dx2qb)+ verdict 流。用真数据(IDs 见下)。判据:用户能打开看到飞轮真转 + 真数字 + 可交互·SendUserFile/可 host。别画空 drill-down(装饰=反D)。

## 真数据位置(拉了就有·别 mock)
- 凭据=我引擎 app `cli_aaa8e75d`(`~/.claude/.cache/.fde_api_secrets.env`)。
- 交付表 `Dx2qb1fjhaJadSs0ZeMc0teVn49`/`tblFkmEKTk4LIWJM`(1 行真交付 drift·provisional·BK1426字)。结算 同base/`tblFL7y3DejBQUvm`(score=1·token=0·应付pending)。
- 专家单价 RGDK `RGDKbrtZ1aMcEOsZ2GcczeFknNg`/`tblQChALfBACGLYB`(15行·5有单价400-600元/h)。
- compass 燃料 `tblvR6BCSBH4IG59`(3 道第3类·确定性verifier)。
- verdict-bus `GET https://nautilus.social/api/platform/fde/verdict/{task_uid}`。FDE 队列 `GET .../api/platform/fde/tasks`(现0 open)。

## 已 binding-DONE(别重验)
- S3 引擎(`services/fde_delivery.py` 10green·f0f73afba)+ 第一根线(`fde_expert_rates.py` 8green·d1292ec10)+ webhook 入口(`runner/platform_soul/s2_auto_qc.py`/`s3_delivery_settlement.py` 4green·8055779ed)。
- bot 跨app写实测可行(drive permission member_type=openid+bot open_id·我bot=`ou_af25f91ccc5cd9e39d120615006df974`)。第一份真交付物在 Dx2qb。

## 可独立落地(喂可见面)
- S3 runner wire 第一根线(应付真算)。S1 加 agent-produce 路由(仅第3类留open·第1/2类human·买方红线)——这条正好是 A 飞轮桥接要的。

## Gated/Blocked(别在里面打转)
- **FDE 部署链(FDE 的活)**:FDE 建 `v06_派活`+审计表发 table_id + 授我 bot RGDK editor + webhook scp/restart(等SSH恢复)。我 FINAL bot-member 已发 `nautilus-FDE/_COORDINATION/`(71b0991)待 FDE ack。**这是第1/2类 human 业务环·与 A 的第3类飞轮并行不互斥。**
- compass P1.2-P1.4(repoint/退役cloud)= 暂缓·不转发·等退役一次性切。

## 跨框协调(GitHub·别 thrash)
- FDE=`nautilus-FDE/_COORDINATION/`(同GH账号自动)。**发"取代"前先 fetch 对方最新**(上session反转4次=教训)。V5 poller=我S1(已回)。compass MCP 现 down·燃料桥接走本 P0。

## 纪律
- #3 反D:**飞轮真转 + 可见 > 埋起来的代码/又一个散页**。#4 反精分:单一 forcing function=飞轮一圈+可见·FDE部署并行不抢焦点。#5 不造轮子:整合现有页·别新建。#6 gotcha 已落 memory·先读。诚实:交付标 provisional·第3类 verify 用确定性门不是 LLM judge。
