# 🧭 飞轮收敛北极星 · 有机耦合设计(2026-06-22)

> compass 主导 · 用户 6/22 指令"彻底弄清历程+目标·有机耦合·反分叉收敛"后产出。
> 全程 measurement-first(6 路并行实测 7 齿轮 + 跨框 inbound 同步 + 记忆数据流深挖),非凭印象。
> 这是**反分叉的单一收敛锚** — 凡不直接服务本图主线的工作 = 分叉,defer。

---

## 0. 一句话总目标

**一个会自己转、并且越转越强的闭环;它同时产出能卖给甲方(FDE)的真货。** 内(RSI 自我提升)外(FDE 买方交付)同一条线:同一道难题既是飞轮燃料又是买方交付物。

---

## 1. 有机耦合图(齿轮 = 注册 agent + 常驻服务;对话框 = 外圈建造者)

```
┌──────────── 系统层(自转传动链 · 不依赖对话框 · §0-ARCH)────────────┐
│  ① 燃料源/出题      ② 解题 producer      ③ 验证 verifier            │
│  dispatch+mint   →  注册 agent(整数id) →  soul-scorer 服务          │
│  (FDE题/auto-mint/  (V5 daemon=9000002    (pass@k门/is_substantive) │
│   SWE·KernelBench)   已注册)                  │                     │
│      ▲                                        ▼                     │
│  ⑦ 更强 solver    ⑥ 回灌 grounding       ④ 结算/账本               │
│  蒸馏→新producer ← compass recall回灌 ←  平台 settle +              │
│  (从未跑)          (W2·LIVE)             capability_evolution(整数) │
│                        ▲                      │                     │
│                   ⑤ 内化 memory capsule ◄─────┘                     │
│                   compass 记忆:经验→胶囊→可召回(split-brain+碎片) │
└──────────────────────────────────────────────────────────────────┘
  建造者(脚手架·不在传动链·随时消失飞轮照转):
  V5对话框=造②⑥⑦ │ soul对话框=造③+难度门+④wiring │ compass对话框=造⑤⑥+工具 │ platform对话框=造①④+注册
  用户=定方向/真专家定稿/给算力
```

**核心主张(= §0-ARCH 编码)**:转飞轮的是 ①~⑦ 注册 agent + 常驻服务;SOUL/compass/V5 四个对话框只是建造/维护齿轮的脚手架,**自己不在传动链里**。凡不在某齿轮上的工作 = 分叉。

---

## 2. 七齿轮真实状态(2026-06-22 实测 · 推翻多处旧声称)

| 齿轮 | 实测状态 | 关键实测出入 |
|---|---|---|
| ① 燃料源 | 🟢 真转活水 | auto-mint 每5min补燃·1449 dispatch·1427 settled·3 agent 实时认领。**但 98% 是软经验题(reward饱和)·真 SWE 硬题仅12且8/12 abandoned** |
| ② producer | 🟡 孤岛+不稳 | daemon 真跑但产 persona 散文非 SWE patch·真 SWE 解走旁路·2148 同日 1.0/0.1 |
| ②注册 | ✅ 已满足(运行层未切) | **prime 已注册整数 9000002(真钱包·migration seed)**·非对话框。gap=`claimed_by` 用字符串标签从未归并整数 |
| ③ verifier | 🟢 活·语义混 | soul-scorer 活·is_substantive 已部署。**bogus 实测只1条(bvh_001)非7条**·根因=难倒门pass/解对pass 两套语义混用 |
| ④ 账本 | 🔴 双断 | verdict 表无 agent_id 列→变不成能力增量·capability_evolution(整数)5/21起死表·结算只翻status不联动金额 |
| ⑤ 记忆胶囊 | 🔴 split-brain+无沉淀 | recall 活(已修timeout)但 dummy.md 污染霸榜。**Store A(sqlite飞轮learning·/v1/recall)与 Store B(文件语义库33386目录·/v1/v14/recall)永久互不可见·无桥接代码**。33386碎片零consolidation |
| ⑥ 回灌W2 | 🟢 LIVE稳定 | fleet-wb 每15min wrote_back 1-3。但喂的多是泛化自省·真咬SWE peer少 |
| ⑦ 蒸馏 | ⬛ 纯空白从未转 | 仅设计文档·peft/trl没装·0 checkpoint·agents表0行·A类题池没建。T4空闲(GPU占4.6G) |

**总诊断**:左半圈(出题→解→验)在转但**磨软题、解走旁路、验证语义混**;右半圈(账本→内化→蒸馏)**断或空**。**所以"越转越强"目前是假象=空转**。与用户直觉一致:左边响、右边没接、中间漏气。

---

## 3. 收敛方案

### 唯一胜负手(所有框已自发收敛)
**先在一道非饱和(硬)题上证一次 uplift(turn-2 真比 turn-1 好)。** = V5 "A uplift 见证"。
- 依据:齿轮①磨软题(reward 饱和·0.6% 梯度)·②⑥ 接通但从没在硬题见证。这一证,左半圈才是真提升而非空转,右半圈才值得接。这就是 V5 反复指的"根因#2"。

### 收敛次序(证完 uplift 再依次闭右半圈·不并发分叉)
1. **【胜负手】uplift 见证** — soul re-mint 非饱和 Lite 题(2148/5414)→ V5 W2 produce → 同题方差收敛。球=soul+V5。
2. **齿轮④ 账本 LINK** — `claimed_by` 字符串 `nautilus-prime-001` → 别名映射整数 `9000002` → `capability_evolution.record_task_outcome(整数id,task_type,success,quality_score)`。**不 register 新 agent(别造9000005)·不动747 claim 历史**。球=soul/平台。小改。
3. **齿轮⑤ 记忆并库+沉淀** — 桥 Store A→B(飞轮learning 经 `/v1/v14/ingest_obs` 带 frontmatter 落文件语义库)+ consolidation 胶囊化(顺带解 37k 冷扫 perf)。球=compass。
4. **齿轮⑦ 蒸馏** — 硬题 A 类 trace 攒够再跑。gated·最后。

### 有机耦合分工
| 框 | 造齿轮 | 这轮 |
|---|---|---|
| soul | ③+④wiring | re-mint 见证题 / 字符串→整数别名 / verdict 语义解耦 |
| V5 | ②+⑥ | uplift 见证 / producer 稳健性 |
| compass | ⑤+③我那半 | 并库+沉淀 / verdict bug / recall 清污+perf |
| 平台 | ①④基建 | 结算金额联动 / capability wiring 落地 |

### compass 自己切片(实测坐实范围)
- **A · verdict 语义 bug(③我那半)**:实测仅 1 条 `bvh_001`。修=解耦"难倒门pass/解对pass"两套口径 + 作废 bvh_001 + 6 条阈值统一。小、清晰。
- **B · 记忆并库+沉淀(⑤主线)**:桥 Store A→B + consolidation。约束:往文件库并(别往sqlite·会丢真语义召回+人类可读沉淀);但要补 ①飞轮晋升门/revoke 文件侧等价过滤 ②user 隔离 ③解 37k 冷扫 perf。需单独 writing-plans。
- **C · recall 清污**:删 `~/.claude/projects/default/memory/dummy.md`(测试遗留霸榜根源)。安全。

### 反分叉铁律
**凡不直接服务"证一次 uplift → 依次闭右半圈"的工作 = 分叉,defer。** 每件 ship 前问:它推进图里哪一格?0 贡献=不做。

---

## 4. 关键坐标(实测坐实 · file:line)
- 记忆双库:`/v1/recall`=sqlite(`compass_http_v09.py:804-849`·`/var/lib/compass/compass.db` observations)·`/v1/v14/recall`=文件索引(`daemon.py:568-620` get_memory_entries 扫 `~/.claude/projects/*/memory/*.md`)。**无桥接代码**(全库 grep consolidation/reindex/sync 仅 perf TODO 注释)。
- 飞轮 W1 写 `/v1/observations`(sqlite)·W2 读 `/v1/recall`(sqlite)= 飞轮在 sqlite 内自洽闭合;split-brain 是 sqlite ↔ 文件语义库两体系互不可见。
- capability_evolution:`phase3/backend/services/capability_evolution.py:103 async def record_task_outcome(agent_id整数,task_type,success,quality_score)`·已接 marketplace/survival/a2a。
- prime 注册:`agents` 表 `agent_id=9000002` Nautilus Prime 真钱包·kairos=9000003·v7=9000004。
- 飞轮拓扑:serving=cloud 43.160.239.61:8770(compass.service)·BGE daemon=T4 经 cloud:9876 隧道·DB=nautilus_production(nautilus_user)。

关联 [[canonical_memory_capsule_equals_compass_crossagent_mcp_collective_learning]]
