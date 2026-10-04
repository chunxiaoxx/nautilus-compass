# 组织记忆的读写与遗忘(MEMORY_IO_ARCHITECTURE)

> 2026-10-04 出件 · 承沉淀提案 2734(件一)· 正本唯一源=本文件,实物坐标全部可寻址
> 定位:compass 组织记忆系统的架构正本——什么进记忆、什么被召回、什么被遗忘、谁在消费,四问各有一套机制与实证。
> 诚实前提:本档含"审计已发现但未闭环"的项,如实标注,不粉饰成全闭环。

## 〇 · 一句话

**记忆的价值不靠"存了什么",靠"召回时恰好有用"**——所以本系统以一次召回有用性实验(delta=1)为立身实证,以写入白名单为质量闸门,以三层温层为召回分级,以四算子为遗忘纪律;审计发现的未修项如实挂账。

## 一 · 总架构:三层温层 × 读写遗三向

```
                ┌──────────────────────────────────────┐
   输入(写) ──→ │  写入门(fact_status + dedup + 沿链)   │
                └──────────────┬───────────────────────┘
                               ↓
   热层  _NODE_*.md + 项目 CLAUDE.md 顶部     ← 综合节点,每 session 必读
   温层  session_*.md / 事件记忆(md+frontmatter) ← 向量召回主池(95 entries)
   冷层  原始会话 jsonl(.claude-backup / H:)   ← 只读归档,source_session 可溯源
                               ↓
                ┌──────────────────────────────────────┐
   输出(读) ←── │  BGE-m3 向量召回(daemon 9876)         │
                └──────────────┬───────────────────────┘
                               ↓
   遗忘(治理):合并 / 淘汰 / 降格 / 衰减(四算子)
```

## 二 · 输入侧(什么进记忆)

### 写入门三件套(memgate,实物 `~/.claude/plugins/nautilus-compass-memgate/`)

1. **fact_status 纪律**:每条事实带 `fact:measured | inferred` 标注——推断不冒充实测(与判分证据三层同源:CLAUDE.md 报数纪律)。
2. **dedup_check**:写入前查重,防同事实多版本漂移(SSOT drift 病根的写入侧防线)。
3. **沿链一跳**:引用别条记忆走 `[[name]]` 链接,召回时展开一跳,防断链孤岛。

### 写入白名单(什么配进记忆)

- 会话提炼:关键决策/bug 复盘/方法论教训(session 结束走提炼,不搬原始对话)。
- 判读结论:判分 verdict 的方法论沉淀(判例本体进 CASEBOOK,记忆存指向)。
- 勘误双向:评委自我证伪与材料方请降同档(如 S2 请降→material_side_honesty 立型)。
- 用户拍板:方向锚/定价/纪律类决策,顶格优先级(方向锚同步写项目 CLAUDE.md)。

**不进**:代码结构/git 历史可查的(仓里有就不记)、只与本会话相关的、原始大段文本(存坐标+指针)。

### 索引制式(MEMORY.md)

一行一条:`- [标题](文件.md) — 钩子句`。索引只做路由,内容永不进索引(防索引膨胀成第二正文)。frontmatter 必填 `name/description/metadata.type`(user|feedback|project|reference)。

## 三 · 输出侧(什么被召回)

### 召回引擎:BGE-m3 向量召回

- 引擎:compass daemon(本地 127.0.0.1:9876 / 云端 v3.3,43.160.239.61),bge-m3 嵌入。
- 接线:UserPromptSubmit hook 每条 prompt 自动召回 top5 + 24h 内新记忆全列(当前心智优先)——本档写作时正被使用,即消费在飞实证。
- 分级:召回结果按 score 排序 + 沿链展开(被 top 条目引用的一跳邻居);🟢=新鲜(24h 内)、🔴=陈旧(提示时间戳,防旧账倒批今天判断)。
- 嵌入选型定谳(9/25 向量对拍):bge-m3 不换——Qwen3-0.6B recall@5 仅 +0.46pt(<阈值),中文切片现役反优 +2.75pt;MTEB 账面在自家分布不成立,只换不造原则。

### 召回入口(消费方)

| 消费方 | 入口 | 状态 |
|---|---|---|
| compass 自身会话 | UserPromptSubmit hook 自动召回 + MCP `recall` | 在役(每轮在用) |
| 跨框 dogfood 桥 | 五框全接云 compass MCP(8/26 合约) | 在役 |
| drift 检查 | MCP `drift_check`/`drift_history` | 在役 |
| 质量反馈 | MCP `feedback_log`(召回有用性反馈回路) | 在役 |

### 有用性实证(不靠自报)

- recall 有用性实验(8/24):F2 任务 delta=1——关召回失败/开召回通过,首证召回有用(此前 391 条记忆 0 实证)。
- 语义 recall 曾 100% 坏死(torch 长路径 bug)而无人察觉——教训:**召回系统必须有有用性探针,活着≠有产出**。

## 四 · 遗忘侧(四算子与审计现状)

| 算子 | 机制 | 审计结论(9/7 七算子审计) |
|---|---|---|
| 合并 | 同事实多版本合一 | **合并无触发器**——靠人工 dedup_check,未自动 |
| 淘汰 | 错误记忆删除(如已知错误/过期事实) | 有实践(daemon-v32 败因记忆改写为 v3.3 定案) |
| 降格 | 重要级下调(gtaras7 从里程碑降为 reference) | 有实践,手动 |
| 衰减 | 按 reinforce 计数/时间衰减权重 | **衰减在 schema 未使用**——挂账未闭环 |

### 生命周期治理

- **NODE 综合**:温层记忆定期提炼进 `_NODE_*.md`(综合节点=复发模式+矛盾陷阱+决策时间线+当前 grounded 状态);**节点必须非 `session_` 前缀**,否则被 recall entries 门槛丢弃(wiring gotcha,踩实过)。
- **reinforce 计数**:召回被采纳→计数递增,衰减权重依据(schema 就位、消费端未接,同衰减挂账)。
- **时效纪律**:召回结果自带时间戳;>7d 旧记忆不倒批今天判断(hook 输出强制警示行)。
- **冷层只读**:原始会话 jsonl 归档(.claude-backup-0714 + H: 盘)只读,勿回写 ~/.claude;每条温层 md 带 source_session 可溯源。

## 五 · 硬标准对照(可查实物)

| 硬标准 | 实物坐标 |
|---|---|
| 写入门三件套源码 | `~/.claude/plugins/nautilus-compass-memgate/`(daemon 仓 feat/memory-gate-trio 合入件) |
| 召回引擎 | compass daemon v3.3(云 43.160.239.61:9876;本地 127.0.0.1:9876) |
| 嵌入选型对拍档 | memory: emb-bakeoff-bge-stays-20260925(读数与判据在档) |
| 有用性实验 | memory: session-contract-recall-usefulness(F2 delta=1) |
| 七算子审计 | memory: memory-audit-seven-operators-20260907(本档 §四结论源) |
| 记忆本体 | `~/.claude/projects/<proj>/memory/`(95 entries,本仓) |

## 六 · 边界与挂账(如实段)

1. 写入门三件套已合入 daemon 仓,生产部署状态=插件在装、daemon 侧门槛在役;**衰减算子与 reinforce 消费端未接**(挂账)。
2. 记忆召回的 drift 防线=persona drift 监控(alignment/deviation 双读数),阈值告警接 hook;drift 自停纪律 R1 是行为层护栏,非引擎层强制。
3. 跨框共享的是云端索引,各框本地 memory 目录互不直接读——跨框事实以函件(platform mailbox)为准,记忆只存指向。
4. 有用性实证目前 n=1 主任务级(F2);规模化有用率统计(feedback_log 数据)未出——挂账,upgrade_path=feedback_log 积累后按采纳率出季度读数。

## 关联

- 正本可寻址:https://raw.githubusercontent.com/chunxiaoxx/nautilus-compass/main/docs/memory/MEMORY_IO_ARCHITECTURE.md(sha 以 org_state 端点读时现算为准,2026-10-04 push 实测 200)
- 件二(独立判官架构模型):`docs/metering/INDEPENDENT_JUDGE_MODEL_V1.md`
- 件三(P3 管线正本):`docs/plans/P3_DYNAMIC_WEIGHT_PIPELINE_DESIGN_20261003.md`
- 证据分层纪律: `docs/metering/JUDGING_EVIDENCE_TIERS_20261003.md`(fact_status 同源)
