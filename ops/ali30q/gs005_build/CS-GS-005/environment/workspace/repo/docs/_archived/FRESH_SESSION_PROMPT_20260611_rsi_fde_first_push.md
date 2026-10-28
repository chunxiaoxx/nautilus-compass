# /goal — RSI+FDE 整链打通 · 人推第一棒(fresh session 提示词 · 2026-06-11 交接)

> 复制本文当 /goal 提示词贴进新会话。你 = platform-soul(nautilus-core 对话框)。
> **Session-start 必读**:`FDE_BUSINESS_CHARTER.md`(三类业务/甲方保密/红线/turf)+ 本文 + memory `fde_business_charter_ssot_must_read_20260609`。

## 北极星(不变)
RSI+FDE 外部客观闭环:**产 → 外部验收(买方 / benchmark pass@k / soul checklist)→ escapes 门 → grounding → 再产 → 下一次外部 ΔReward 度量**。fitness **永远外部**,绝不内部 NAU/自评;**不复活 `nautilus-soul.service`**(内部 codegen 自改 daemon = 已证伪的自指环;它≠FDE 判分引擎)。

## 当前状态(2026-06-11 · 三框 grounded 收敛 · 飞轮只差一棒)
判分链 + 消费链**全活**,唯一断点已精确定位:
- ✅ `soul-scorer`(judge·timer 每 2min)活 · ✅ v5 `fde-runner@kairos/@v7` + `V5_FDE_RATCHET=1` LIVE(consumer)· ✅ benchmark_verifier / fde_verdicts / soul-cycle-B(grounded-retrieval RSI cycle)/ fde_grounding 都在生产
- 🔴 **唯一断点 = `fde_dispatch` 队列 0 个 open 任务**(实测 `GET /api/platform/fde/tasks?status=open`=0;9 行全 settled;最新产出 6/10 ~16h 前)。
- 🔴 关键认知(本 session 推翻旧误判):agent 创建 produced 行**不需要 admin key**(`/claim` `/report` 对 agent 开放·实测 404 过鉴权);**只有录入 open 任务(`POST /dispatch`)需 admin key = 平台 turf**。"永远靠 Claude 单方推"的真相 = 平台没在录 open 任务,不是权限墙。
- 🔴 **第一推动人 = 人(用户)**:注入真外部买方需求,不让 AI 内生 demand(否则又一种自指)。

## 第一优先 = walking skeleton(先证整链转一圈,别先建漂亮入口)
**① 人推第一棒**:`POST /api/platform/fde/dispatch` 录 1 道真 T3 题。命令(用户持 key):
```bash
curl -X POST https://www.nautilus.social/api/platform/fde/dispatch \
  -H "Content-Type: application/json" -H "X-Platform-Key: <PLATFORM_DISPATCH_KEY>" \
  -d '{"task_uid":"compass_autolab_huffman_cuda_001","title":"AutoLab Huffman CUDA · T3 难倒(doubao pass@5=0.4)","description":"{\"level\":\"L3\",\"benchmark\":\"AutoLab\",\"eval_kind\":\"passk_rerun\",\"k\":5,\"target_model\":\"doubao-seed-2.0-pro\",\"pass_threshold\":0.6,\"eval_script\":\"/mnt/datadisk0/fde_t3_harness/huffman_eval.sh\",\"feishu_rid\":\"recvm9Rrt8U5bF\"}"}'
```
**② 盯一圈**:fde-runner 是否自动 claim+produce(doubao 重做)?soul-scorer 是否 2min 内 settle?→ 新 verdict + /demo 数据变新 = **整链端到端成立**。⚠️ 这步同时验证**最大未验证点:fde-runner 能否真自驱生产一个真任务**。若不动,排查 fde-runner(它瞄的端点/claim 逻辑)。
**③ RSI 半边泛化**:≥3 道独立 benchmark grounded-vs-裸 ΔReward(GPU·radix 已 +0.0734 escapes=True·soul-cycle-B 机制 ready)。
**④ 再建操作台**:飞书"任务下发"intake(平台 poller 持 key 读飞书表→/dispatch)+ 网页/飞书 = 原生 AI 组织操作台(人员组织 / 项目管理 / 咨询培训引导副驾驶)。**②证通前不建**。

## 关键事实 / gotcha
- **dispatch schema**:`POST /dispatch` 只持久化 `task_uid` / `title` / `description`(其余 body 丢弃)。富 spec(eval_kind/k/eval_script/...)**打包进 description JSON**,v5 consumer 必须解析 description 拿到。长期更干净 = 给 fde_dispatch 加 `spec` JSON 列 + 端点接收(迁移)。
- **12 题名册** = `_OUTBOUND_FROM_COMPASS_TO_PLATFORM_20260611_t3_open_task_roster_for_dispatch.md`(huffman/leven/ntt/icp/gb/regex/vliw/golf/aes/splay/bvh/zorder · eval_script + 飞书 rid 齐 · 难倒达标 9 道 + 合格 3 道)。
- **soul QC 裁定(已发 compass·`_OUTBOUND_FROM_PLATFORM_SOUL_TO_COMPASS_20260611_qc_*`)**:verdict 沿用 fde_verdicts 锁定列 + T3 字段挂 `artifacts.qc` · 第三类 harness pass@k 自判 authoritative + 薄 QC(脱敏/防作弊)· 一二类 soul-scorer 自动判 · 触发=compass ping。
- **admin key** = cloud `~/nautilus-mvp/phase3/backend/.env` 的 `PLATFORM_DISPATCH_KEY` · 鉴权头 `X-Platform-Key` · **别放进对话**。
- **demo 已修**(本 session·PR #136 分支 cp-pulse-provenance):Reveal 用 Portal 修(fixed 被 transform 困)· control-plane 限流 200→1200/hr · 死页 /live /feed 摘除 · 营销页删编造 · 三系统真代码图谱(平台3424/agent1298/compass42 核心)+ 力导向大图。memory:`gotcha_control_plane_ratelimit_vs_poll` + `gotcha_fixed_modal_trapped_by_ancestor_transform`。
- **cloud = fork**(分支 soul-audit-increment1)· 外科 scp 部署(scp dist→/tmp→sudo rsync /var/www/nautilus/current)· **别 pull**。
- 跨框 outbound 投 cloud `~/nautilus-soul-workspace/docs/`(compass scanner 扫这)· MCP 时断时用户转发。

## 收敛纪律(anchor #4 · 历史最痛 = 工作流永远扩展、不闭环)
binding-DONE + 冻结 scope。第一优先**只做 ①②**(walking skeleton)。操作台/飞书 app 愿景 = captured-but-deferred 到 ③④,**引擎证转前不建**。本 session 已极长就是反例 —— 别再 diverge。

## 跨框待办(已发 cloud · 用户可转发)
- **compass**:把产出接线进 `fde_dispatch`/`fde_verdicts`(别只写飞书)· schema=3字段+spec进description · 12 题名册当 v5 棘轮 open 燃料
- **v5**:produce 无需 key(claim/report 开放)· 持续供给队列 · spec 在 description 要解析 · 棘轮 ≥2 version×≥5 样本
- **用户**:第一推动人(录 open 任务)· ContactPage 邮箱已改 chunxiaoxx@gmail.com

关联 [[FDE_BUSINESS_CHARTER]] · [[session_20260610_soul_cycle_b_keystone_binding_done]] · [[session_20260609_grounding_platform_bridge_v1_binding_done]]
