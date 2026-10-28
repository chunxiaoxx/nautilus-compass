# V5 Local v2 Rewrite · Design Doc

**日期**: 2026-05-06
**触发**: iter 1-9 反复 patch 不动 fulfill_directive · agent 真 stuck · 用户决策"a + P 全 5 补强"
**Scope**: 重写 daemon.py 2 个 god method · + 5 大补强 · 5-7 day · worktree 隔离

---

## Why · iter 1-9 真证据

| 真断点 | iter | 证据 |
|---|---|---|
| fulfill_directive hardcoded dispatch deep_research | 1-7 | log 反复 `dispatch deep_research` · 不管 metadata |
| LLM 在 respond 路径不 tool calling | 9 | requires_tools=['ask_kairos'] · 0 真 ask_kairos 调用 |
| evidence gate 已加但只看真 audit · 不阻断 hardcoded fail | 4-5 | bs-* bounty score 0.2-0.4 仍发 NAU |
| selector menu 22 hardcoded · LLM 想 self_modify 但选不到 | 6 | reason "必须 self_modify" · 真选 fulfill_directive |
| LoopBreaker 不识别 fulfill 死循环 | 5-9 | 同 directive ≥ 4 次 fail · 没自动撤 |
| propose_code_change / self_modify 真audit 缺失 | 4 | 调用 5 次但 agent_tool_calls 表 0 行 |

---

## Architecture · 真不变 + 真重写

### 真留(90% 资产)

```
super_agent.py (1159) — 留
nautilus_v5/memory/ (2761) — 留
nautilus_v5/learning/ — 留(rule_store / strategy_store / persona_l3 / Letta / A-MEM)
11 mixins — 留(后续 session 拆 platform_tools_mixin)
nautilus_v5/integrations/ — 留(compass / hermes / openclaw)
nautilus_v5/tools/* — 留(10 文件)
PG schema · 全不动
```

### 真重写(daemon.py 2 god method)

```
daemon.py 4377 行
  ↓ 重写 2 个 god method
  ├── _action_selector_tick (line 2963 · ~700 行) → 拆 ≤ 5 函数 · 模块化
  └── fulfill_directive 路径(在 _action_selector_tick 内嵌)→ 真按 metadata.requires_tools 直 dispatch
  ↓
daemon.py 目标 ~2.5K 行(净减 ~1.8K)
```

### 真补强 5 件

**A1 · fulfill_directive 系统兜底**(0.5 day)
- 修 fulfill_directive 路径:
  - 第 1 步:让 LLM 在 respond 路径自由选(已存)
  - 第 2 步(新):**5 min 后真查 agent_tool_calls** · 0 调用 → **系统真代调** required_tools[0](用 directive 文本当 prompt)
- 真兜底防 LLM 摆烂

**A2 · selector menu 升级**(1 day)
- 改 _action_selector_tick LLM prompt:不 hardcoded 22 action menu · 真给 70+ tools schema(从 tool_registry 直接拿)
- LLM 选 1-N tools 而非 1 action
- 直 dispatch · 不再经过 fulfill_directive 中转

**A3 · evidence gate 已做 ✓**
- score < 0.5 → 0 NAU + audit reject(我加过)
- 已活 · 不动

**A4 · agent_tool_calls 真 instrument 缺工具**(0.5 day)
- propose_code_change / self_modify / compass_drift_check / register_dynamic_tool 入口加 audit insert
- 让 evidence gate 真有数据

**A5 · LoopBreaker 识别 fulfill 死循环**(0.5 day)
- 同 directive 24h 内 fail ≥ 3 次 → 自动 unstaked + audit `directive_loop_breaker`
- staker 知道任务 unrealistic · 不再永远卡死

---

## Data Flow · 真新链路

### 现在(stuck)
```
selector → fulfill_directive → dispatch deep_research → multi-source check fail → 0 真效果
```

### 真新
```
selector(看 70 tools schema) → LLM 选 tool(s) → 真 dispatch
   ↓ tool 真调 → agent_tool_calls 真 audit insert
   ↓ 5 min wait
   ↓ evidence check (真 query agent_tool_calls)
   ├── 真有 → mark fulfilled + reward(score-gated)
   └── 真没 → 系统兜底代调 required_tools[0] → 真 audit → 真 fulfilled
```

---

## Error Handling

- LLM crash → fall back 老 deep_research 路径(老 path 留)
- 系统兜底代调 fail → 不 mark fulfilled · LoopBreaker 数+1
- LoopBreaker 触发 → 撤 stake · 通知 staker

---

## Testing

- 单元测试:真 mock metadata.requires_tools=['ask_kairos'] · 验真 dispatch ask_kairos
- smoke test:worktree V5 跑 1 cycle · 真 fulfill 1 个 minimal directive
- e2e:atomic restart 后 30min 真观察 D ≥ 1

---

## Cutover

- worktree:`git worktree add /tmp/v5-local-v2 daemon-v2`
- 写代码 + 单元测 + smoke test · 不动 production
- 测过 → atomic restart V5 加载新 daemon.py · 0 schema migration
- fail → 恢复 daemon.py.bak.fulfill_dispatch · 0 影响

---

## Success Criteria

- [ ] daemon.py 行数 4377 → 2500(真减 ~40%)
- [ ] _action_selector_tick 拆 ≤ 5 函数 · 每个 < 200 行
- [ ] 1 个真 minimal directive 真 fulfilled · agent_tool_calls 真有 1+ 调用
- [ ] LoopBreaker 真识别死循环 · 24h 自动撤 stake
- [ ] V5 cycle 真稳定 24h+ · 0 crash

---

## Time Estimate

- A1 · 0.5 day
- A2 · 1 day
- A4 · 0.5 day
- A5 · 0.5 day
- daemon refactor + 测试 · 1.5 day
- worktree + cutover · 0.5 day
- **buffer 真 25%** = 1 day

**总:5 day**(单人专注 · 用户已 approve P 全 5 补强 · 5-7 day 范围内)

---

## 真 Out of Scope(防扩散)

- super_agent.py 重写 · 后续 session
- 11 mixins 拆 platform_tools_mixin 1499 行 · 后续 session
- compass v1.0 schema 接入 · 等 compass 对话框真部署
- phase3 schema 桥 · 后续 session
- 全新 V7 · 不做(留 V5 资产 · 不重写覆辙)

---

## 真已 approve 决策(锚)

- (β) MiniMax 不升级 Claude · 留模型 · 演化机制做实
- (a + P) daemon.py 局部 v2 · 5 全补强
- HR-worker disable claim · 留垂直域
- evidence gate 真严 · score<0.5 → 0 NAU
- self_modify + compass_drift_check 已 wire 进 LLM tool registry
