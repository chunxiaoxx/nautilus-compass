# Design · Soul Trinity Product Vision — 可信自改进 AI 服务

> Status: **APPROVED & LOCKED 2026-05-27** (user approved via brainstorming session)
> Owner: platform-dialog (nautilus-core)
> Supersedes positioning ambiguity in `2026-05-27-soul-as-shared-service-ADR.md` (this extends it to a product vision; ADR's "Soul = shared service" = the infra/底座 layer of this matrix).
> Next: writing-plans → executing-plans for the **first increment only**.

## North Star (product)

**Nautilus = 中国化 Anthropic 的原生 AI 组织底座。** Soul 是这个 AI-native 组织持续自我维护 + 自我进化的递归闭环底座,把能力**对外作为产品提供**。

愿景一句话:**"可信自改进 AI 服务" — AI 产出 + 多 agent 审计 + 密码学证书 + 溯源链。**

## 外部 grounding (anchor #5 · 不重复造轮子)

- **YC · Tom Blomfield**: "The company itself has to be built with self-improving AI loops from the ground up." 架构 = Sensors/Data → Policy → Tool → **Quality Gates(关键决策人工 review)** → Learning。capability > productivity。
- **YC · Diana Hu**: closed-loop(监控产出→喂回 AI→精炼)· "queryable organization" · "burn tokens not headcount"。
- **Anthropic Founder's Playbook**: AI 作核心基础设施 · 移除 capital/headcount/skill 瓶颈 · ⚠️ 警告 "mistaking building for validating"(prototype 易得 ≠ 价值被验证)。
- **Anthropic dogfooding**: 用 Claude 造 Claude(推进→审查→反馈→再推进)= 我们的 Soul loop + Stage 2 递归。

映射:

| YC / Anthropic 框架 | Nautilus 对应 |
|---|---|
| 组织由自我提升 loop 从底层构建 | 平台 = AI-native 组织 |
| 成员都是 builder (ICs) | V5 / Kairos / V7 = 自治 agent 成员 |
| closed loop: Data→Feedback→Refine | `engine_cycle_outcomes` → `v_engine_progress` → 下一 cycle |
| Quality Gates + 关键决策人工 review | draft-PR + blacklist + diff cap + 熔断 + 人工 merge |
| DRI per outcome | 各 dialog 是其 agent 的 DRI · Soul 是底座进化的 DRI |
| burn tokens not headcount | NAU 经济 + DeepSeek cost cap |

## 关键架构决定

### 1. 底座,不是本体 (anchor #1 保住)

- **底座** = 在下面、托起并进化一切 → agents 仍自治(自己的 goal/wallet/决策)· Soul 不夺 agency。✅
- **本体**(被否决)= 在上面、拥有一切 → agents 沦为部件 → 撞 anchor #1。
- 边界:Soul **自主维护组织共享部分**(平台 code + Soul 自己引擎 = Stage 2 递归 · 无别 dialog 拥有)· **按需服务 agents self-modify**(pull · 各 agent 自己发起)。

### 2. 三位一体融合 (三方近两天工作的拼合)

```
Soul 产出 (self-improving codegen / self-modify)
  → 审计 council 验证 (V5 执行 + Kairos 判 fidelity + drift check)
    → Compass 溯源 (PoI cite-trail + 记忆 grounding)
      → 平台签发 可信证书 (JSON-LD HMAC-SHA256)
```

| 对话框 | 近两天已 ship(查证) | 融合角色 |
|---|---|---|
| Soul/平台 | Soul 共享服务 + agent→soul loop LIVE + `/api/soul/generate`;审计/鉴证服务 `/api/v1/audit/dispatch` + JSON-LD HMAC-SHA256 证书 | 产出 + 签证 |
| Agent (V5/Kairos) | V5 换脑 DeepSeek-v4-pro(fail 9.5%→6.8%)· 三自递归闭环 Phase1 · 工具平台化提案 | 审计 council |
| Compass | v2.0.1 daemon 根治 + "真"过滤 + `ingest` action(平台直喂)+ PoI cite-trail | 溯源 + 记忆 |

差异点(vs 裸 LLM / Claude Code):交付的不只是代码,是**被多 agent 审计过、密码学签证、可溯源**的 AI 产出 = Anthropic trust-and-safety DNA 的中国化落地。我们三块都 ship 过 → 是**融合**不是从零造。

### 3. 产品矩阵(同一底座的不同产品表面 · 不互斥)

| 组合 | = 什么 | Anthropic 对标 | 状态 |
|---|---|---|---|
| Soul + 平台 | 底座对外当服务 + 自维护 | 内部 dogfood loop + API 平台 | 自主可推 |
| Soul + V7 | 递归自改进 coding agent | Claude Code | 需 V7 dialog consent (anchor #7) |
| Soul + V7 + 平台 | 完整原生 AI 组织底座 | 整个 Anthropic | 北极星 · 上面两个累积构成 |

### 4. 落地路径:C 打底 + A 对外,B 暂缓

- **C(dogfood)**: Soul 自主维护**我们自己 repo** → 每改进被审计+签证 → git 历史 = 一条"每行 AI 代码都审计+认证"的链(= 证据/营销)。
- **A(对外)**: 外部 codegen API 返回 = 产出 + 证书。
- **B(repo 级自改进服务,完整 Claude Code)**: 暂缓到闸经 C 实战打磨(blast radius 大)。

## 第一增量(LOCKED · binding DONE)

> **Soul 产出 → 审计 → 签证,跑通一个 cycle。**
> **DONE = 我们自己 repo 上一个 draft PR,带一张验真的签名证书 + 审计结论。其它什么都不做。**

- 只搭在两个已 ship 的东西之间:Soul loop(`engine.ship` / `/api/soul/generate`)+ 审计服务(`/api/v1/audit/dispatch` + cert)。
- 纯平台 turf · 无需别 dialog 改代码(审计服务能 self-dispatch)。
- 第一增量**人工搭**(Stage 1 证据:Soul 自改有 truncate-rewrite drift · 复杂多文件还不可靠)。通过 + 闸验过后,**第二增量起用 Soul 自己驱动**(把后续 goal 喂 goals.yaml · 这才是 dogfood 正解)。

## 工作流纪律(本设计的执行契约 · 见 memory `feedback_workflow_lock_goal_until_done_20260527`)

1. **binding DONE 锁死** · 达到即停 · 不准再加。
2. **冻结 scope** · 执行期任何新想法进 `PARKING_LOT_soul_trinity_20260527.md` · 不进当前 goal。
3. **forcing function = plan 的 Done Criteria · 不靠对话框自律**(anchor #6)。
4. diverge(brainstorm · 已完成)与 converge(execute · 现在)分离。

## 跨 dialog (anchor #7)

- 核心可自主建:Soul + 审计 + 证书 = 全平台 turf。
- 已 ship 的别 dialog 原语:compass `ingest` + PoI(可接)· V5/Kairos 已 opt-in 审计角色。
- 需协调(非阻塞 · 后续增量):把 V5/Kairos 明确接到"审 Soul 产出"上 → 一封轻 inbound。

## Out of scope (第一增量 · 全进 parking lot)

对外 A · compass PoI 融合 · Soul+V7 · 产品矩阵展开 · cron-wiring/3 闸 · Stage 2 driver · B repo 级服务。

## 验证铁律

第一增量"verified"必须真跑:真触发 Soul 生成 → 真过审计 → 真签证 → 真 draft PR + 证书 tamper-verify。不嘴上说通过(persona-drift 5/27 alert 提醒)。
