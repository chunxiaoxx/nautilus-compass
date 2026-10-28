# 平台端统一控制面 + RSI+FDE 收敛 · 设计(下阶段入口)

> 用户(2026-06-06):"能直接调度各 agent/soul/compass · 前端网页或本地 CLI · RSI+FDE 闭环收敛 · 站平台端考虑"。
> 接 `2026-06-06-fde-unified-architecture-four-questions-design.md`(四问)+ master `§3`(CLI→GUI)。本 doc 只设计,不 build。
> ⚠️ V5 对话框的 dispatch/CLI/看板/dual-review 设计 doc 在它本地工作区(未 commit cloud · platform-soul 读不到)→ **fold-in 点已标**,V5 把设计 commit 到 ~/nautilus-v5/docs/plans/ 或 relay 后合并。

## 0. 核心洞察(平台端)
用户要的三件 = **一个控制面的三层**,平台 OWN 它。**不新建**:扩现有 8001 FastAPI(55 端点·公开 stats/agents/feed 已有)+ 薄封装现有调度积木(anchor #5)。web 网页与本地 CLI = **同一组平台 API 的两个前端**。

```
┌─ VIEW 层(可感知)
│   有:8001 /api/platform/stats|agents|feed · 8000 soul/activity(W2.1)
│   建:RSI/FDE GET 端点(verdict-bus/PoI/fleet/RSI 状态·~200行)+ HTML 看板(~300行·套 /services)
├─ CONTROL 层(直接调度 agent/soul/compass)
│   积木(散·复用):a2a_relay(发消息→agent) · POST /api/soul/dispatch(派 goal→soul)
│                   · agent autonomy toggle · bounty dispatch · compass MCP/契约
│   建:统一 POST /api/platform/dispatch {target:agent|soul|compass, action, payload} → 薄路由到对的积木
│        web 按钮 + CLI 都调它
└─ RSI+FDE 收敛 层
    有:verdict-bus LIVE(本session) · soul QC · compass PoI(LIVE)
    建:W6 RSI 反馈环(verdict 失败→grounding→producer·gated on data_002→003)
        + dual-review fitness(V5 设计·我已裁口径:source filter 前置)→ 控制面 "FDE tab" 可见可触发
```

## 1. web 网页 vs 本地 CLI(都是 8001 平台 API 的前端)
- **web 看板**(运营/对外 demo):8001 上加 HTML + RSI/FDE GET + dispatch 按钮。最低门槛·对外可展示闭环。
- **本地 CLI**(技术运营):瘦客户端 `nautilus <view|dispatch|status>` 调 8001 API。🔴 **不搬 nautilus-v5 整仓**(24 依赖+模型下载)·只 HTTP 调端点·一个小 pip 包或单文件脚本。
- master §3 候选(飞书嵌 agent / 桌面 app)= 更远期·先把 8001 API + web 看板 + 瘦 CLI 这层做实。

## 2. CONTROL 层:统一 dispatch 路由(平台薄封装)
`POST /api/platform/dispatch`:
| target | action 例 | 路由到 |
|---|---|---|
| agent(v5/kairos/v7) | run_task / send_msg / toggle_autonomy | a2a_relay send · agent autonomy 端点 |
| soul | dispatch_goal / score_task | POST /api/soul/dispatch · checklist_scorer |
| compass | recall / poi_query / ingest | compass MCP / 契约(G-turf:只接接口不碰内部) |
| FDE | post_task / get_verdict / trigger_rsi | bounty dispatch · verdict-bus 端点(W1.2 已建)· W6 |
- 薄路由·不重写调度逻辑(anchor #5)·鉴权复用平台现有。

## 3. RSI+FDE 收敛(控制面的核心价值)
- 现状:verdict-bus LIVE·6 题自治闭环。收敛缺的 = **RSI 反馈半边**(verdict 失败→grounding→喂 producer→下一 verdict 度量)= W6·gated on data_002→003 grounding 假说。
- 控制面让它**可见**(看板 RSI tab:verdict 通过率/grounding 注入/pass 率变化)+ **可触发**(dispatch trigger_rsi)。
- dual-review(V5 Kairos-Opus 二审当 fitness):我已裁口径(补充信号 / 取最严+分歧标复核 / **compass 必须先加 source='soul' filter 防 PoI 污染** / V5 代灌)。控制面 FDE tab 显示一审/二审/分歧。

## 4. 平台该建的件(倒逼清单具象 · 按依赖排序)
1. **RSI/FDE GET 端点**(8001·VIEW)——小·套现有 pattern
2. **HTML 看板**(8001·VIEW + dispatch 按钮)——小·套 /services
3. **POST /api/platform/dispatch**(CONTROL 薄路由)——封装现有积木
4. **瘦 CLI 客户端**(本地调平台 API)
5. **W6 RSI 反馈环**(gated)+ dual-review 接入(compass source filter 前置)

## 5. 🔴 硬前置 / Gates
- **Q2 production 线归位**:8001/8000 后端跑哪条线?(8000 在 soul-audit-increment1 与 master 90/889 分叉)→ 控制面端点部署落不了地,除非先归位。**这是地基,先于 1-5**。
- W6 RSI gated on data_002→003 假说。dual-review 接入 gated on compass source filter。
- 生产部署/重启 = G-cloud · 专门 session + verification。

## 6. 两框 RSI 设计已直接读(本地 · 6/6)+ 平台端增量

**[已读]** 用户澄清"你们都在本地"→ 直接读了两框设计(都在 `C:\Users\chunx\Projects\` 本地仓):
- **V5 `nautilus-v5/docs/plans/2026-06-06-fde-fitness-rsi-dual-review-design.md`**:**behavior RSI** = verdict→fitness→`self_modify`(朝"产物评分更高"改自己)· Kairos-Opus 对抗二审 · P3 沙箱验证门(替堵死的 vote/executor)· **核心=绕开堵死的治理飞轮**,FDE-fitness 是独立第三条 RSI 路。§7 已采纳我的 4 口径 + source-filter 硬前置 = 对齐完成。
- **compass `nautilus-compass/docs/plans/2026-06-05-fde-rsi-dual-flywheel-closure-design.md`**:**memory RSI** = verdict→PoI→recall boost · 4 缺口(记忆胶囊跨设备/检索保真进生产/verdict→PoI 双轮咬合/**专家互动回路=复利新脉**)· RSI 唯一活路=外部 ground truth=FDE 专家复核/字节接收。

**两框各做 RSI 一半**(V5=behavior · compass=memory),都读 verdict-bus(平台本 session 建的 hub),都绕开/不碰内部治理飞轮。

### 平台端增量(V5/compass 没覆盖 · 平台该 OWN)
1. **统一控制面**(§0-4):两框都只做自己内部流,**没人做"一处调度 agent+soul+compass"的统一面** = 平台 substrate 该 OWN。
2. **🔴 正式弃死掉的 code-PR 治理飞轮**:V5 设计明说绕开它(82 卡死/auto_approve 不 fire/executor inactive),compass 也不碰。平台该**正式 deprecate** 这条内部自指飞轮(别再修 82 卡死/auto_approve)——productive RSI(FDE-fitness behavior + PoI memory)已绕开它。这是 anchor #3 反 D 的干净落地:停止维护死的自指环。
3. **verdict-bus = 收敛 substrate**(已 LIVE):V5 behavior-RSI + compass memory-RSI 都从它读。平台 OWN 这个 hub,控制面 VIEW 把两条 RSI + FDE 流都显示出来。

## 7. 下个 fresh session 起手序
1. 读本 doc + 四问 doc + master §3 + (V5 relay 的设计)。
2. **先解 Q2 production 线归位**(地基)→ 否则控制面端点部署落不了地。
3. brainstorming 收敛:VIEW 看板(对外 demo·用户已同意)先,还是 CONTROL dispatch 先?(建议 VIEW 看板先 = 低险·对外可展示·把闭环照出来;CONTROL 随后)。
4. writing-plans → 实现。守 anchor #3 不全做·不在 marathon 末尾趟生产。
