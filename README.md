# zenmind-mem · v0.5 (Private · Pre-release)

> **Memory plugin for Claude Code** · Persona drift detection + DPT strategy + A-MEM dynamic links
>
> Based on [zenmind.chat](https://zenmind.chat) SoulCore architecture + Nautilus V5 governance battle-tested in production.

> ⚠️ **PRIVATE** · 内部使用 · 商业化前不开源

[中文](#中文) | [English](#english)

---

## English

### Why this plugin

`claude-mem` dumps session summaries to markdown. But it cannot:
- ❌ Distinguish memory **timestamps** → using 13-day-old memory to overrule today's mindset
- ❌ Store **judgment frameworks** → only static facts
- ❌ **Active recall** in real time → SessionStart loads once, never updates
- ❌ **Deprecate** stale memory → all old memos kept forever

**zenmind-mem** is the cognition layer above `claude-mem`:
- ✅ Age-grouped: `🟢 ≤24h trust · 🟡 1-7d ref · 🔴 >7d don't overrule`
- ✅ **Persona Vectors L3** (Anthropic arXiv 2507.21509): 25 anchors + 25 anti-anchors · drift detection
- ✅ **DPT-Agent Strategy Store** (arXiv 2502.11882): keyword-triggered path injection
- ✅ **A-MEM dynamic links** (arXiv 2502.12110): cross-cosine supersede detection
- ✅ **Ebbinghaus decay**: 30-day-unused strategies fade
- ✅ **TCP daemon**: BGE keeps loaded · 1.8s warm · usable across Claude Code + cloud agents

### Quick install (private)

```bash
gh repo clone chunxiaoxx/zenmind-mem ~/.claude/plugins/zenmind-mem
bash ~/.claude/plugins/zenmind-mem/install.sh
```

### Two-track design

| Track | Latency | Trigger |
|---|---|---|
| **Hook (metadata)** | 0.5s | every UserPromptSubmit · automatic |
| **CLI BGE daemon** | 1.8s warm / 110s first cold | Claude self-invokes |

```bash
python3 ~/.claude/plugins/zenmind-mem/recall.py --bge --query "<question>"
```

### Sample output

```
[Persona drift · 25+25 anchors · BGE · daemon]
  score=-0.012 · ⚠️ towards anti-anchor
  🔴 alert: '用 12d old memory 倒批今天判断' (cos=0.83)

🎯 Recall top 5:
  🟢 score=0.87 · [3h old]   audit_2026_04_27.md
  🟡 score=0.71 · [5d old]   flywheel_abcde.md  ↳ superseded by session_04_27.md
  🔴 score=0.65 · [13d old]  feedback_focus_on_products.md
```

### Roadmap (private)

- v0.5 · current · all 6 modules working
- v1.0 · install.sh polish + CHANGELOG
- v1.2 · cross-project memory recall
- v1.5 · self-reflection (PostToolUse drift)
- v2.0 · multi-user SaaS · ¥499/mo
- **公开发布**: 商业化路径明确后再决定 (TBD)

### Sister projects

- [zenmind.chat](https://zenmind.chat) · AI spiritual companion (1487+ users)
- [Nautilus V5](https://github.com/chunxiaoxx/nautilus-v5) · live super-agent platform
- All same SoulCore architecture by [@chunxiaoxx](https://github.com/chunxiaoxx)

---

## 中文

### 解的真问题

`claude-mem` 是 markdown 备忘录 · 但解不了:
- ❌ 不区分时间戳 → 用 13 天前的 memory 倒批今天判断
- ❌ 不存判断框架 → 只存事实
- ❌ 不实时召回 → SessionStart 注入后不再更新
- ❌ 不 deprecate 旧 → 所有 memory 永存

**zenmind-mem** 是 `claude-mem` 之上的认知层:
- ✅ 时间分组 `🟢 ≤24h 优先信任 · 🟡 1-7d · 🔴 >7d 别当现状`
- ✅ **Persona Vectors L3**: 25+25 锚点 cosine 漂移检测 · 反锚点 alert
- ✅ **DPT-Agent Strategy**: 关键词触发"当 X 时 → 做 Y"
- ✅ **A-MEM 动态链接**: 自动 supersede 检测
- ✅ **Ebbinghaus decay**: 30 天未用自动衰减
- ✅ **TCP daemon**: BGE 常驻 · warm 1.8s

### 双轨

| 路径 | 延迟 | 触发 |
|---|---|---|
| Hook | 0.5s | 每 prompt 自动 |
| BGE daemon | 1.8s warm | Claude 主动 |

### 安装 (私有)

```bash
gh repo clone chunxiaoxx/zenmind-mem ~/.claude/plugins/zenmind-mem
bash ~/.claude/plugins/zenmind-mem/install.sh
```

### 路线图 (私有 · 商业化前)

- v0.5 · 当前 · 6 模块全跑通
- v1.0 · install.sh 完善
- v1.2 · 跨项目召回
- v1.5 · PostToolUse drift 自反思
- v2.0 · 多用户 SaaS · ¥499/月
- **公开发布**: 商业化路径明确后再定 (TBD)

### 姐妹项目

- [zenmind.chat](https://zenmind.chat) · AI 精神伴侣 (1487+ 用户)
- [Nautilus V5](https://github.com/chunxiaoxx/nautilus-v5)
- 同源 SoulCore 架构 by [@chunxiaoxx](https://github.com/chunxiaoxx)

---

**License**: 私有 · 不开源 · © 2026 chunxiaoxx
