# V5 Memory Plugin · v1.0

> 来自 nautilus-v5 + 禅心 AI 的记忆栈 · 解 claude-mem 不实时校准的真痛点。
> Claude Code UserPromptSubmit + Stop hook · 0 LLM cost · BGE 真语义召回 < 2s。

## 解的真问题

claude-mem 是 dump-and-load · 跨 session 传事实 · 但:
- ❌ 不区分 memory 时间戳 → 用旧 memory 倒批新心智
- ❌ 不存判断框架 → 只存事实
- ❌ 不实时 active recall → SessionStart 注入一次后不再更新
- ❌ 旧 memory 不 deprecate → 新事实出现也不影响

V5 栈 5 层对应解:
| claude-mem 缺 | V5 plugin 模块 |
|---|---|
| 不区分时间戳 | **metadata mode** · age 分组 (24h/7d/older) |
| 不实时 recall | **BGE daemon** · UserPromptSubmit hook · 真语义召回 1.8s |
| 不监控判断飘移 | **Persona drift** · 25+25 锚点 cosine |
| 不存判断框架 | **Strategy Store** · 关键词命中 → 注入推理路径 |
| 不 deprecate 旧 | **A-MEM links** · cosine cross-detect supersede |
| 不自动总结 | **Stop hook** · session 结束自动扩 strategy ev |

## 6 个核心模块

```
~/.claude/plugins/zenmind-mem/
├── recall.py            # main · UserPromptSubmit hook · 双轨 (hook 0.5s / BGE 1.8s)
├── daemon.py            # BGE keep loaded · TCP 9876 · IPC
├── stop_hook.py         # Stop hook · session 结束自动蒸馏
├── strategy_store.py    # Strategy 推理路径库
├── links_finder.py      # A-MEM cross-cosine 关系发现
├── anchors.json         # Persona 25+25 锚点 (用户编辑)
│
├── install.sh           # 一键装 (BGE + daemon + links)
├── install_bge.sh       # 仅装 BGE
├── daemon_start.sh      # 启动 daemon
├── daemon_stop.sh       # 停 daemon
├── hook.sh              # UserPromptSubmit entry
│
├── selftest.py          # 自测 (5 项)
├── deeptest.py          # 深度边界测 (19 项)
└── README.md            # 本文档
```

## 安装

```bash
bash ~/.claude/plugins/zenmind-mem/install.sh
```

3 步 · 装 BGE (一次性 ~400MB) · 启动 daemon · 算 A-MEM links · settings.json hook 已配。

## 用法 (3 路径)

### 路径 1 · Hook 自动 (每个 prompt · 0.5s)

UserPromptSubmit hook 自动跑 · 每个 prompt 看到:
```
<zenmind-mem-recall plugin=zenmind-mem v0.5>
Project memory: <proj> · 72 entries
⚠️ 时间戳 = 关键 · 用户心智在迭代 · 不要用 7d+ 旧 memory 倒批今天判断

[Strategy 蒸馏 · 你历史走通的路径 · 1 条命中]
  · 用户问 V5 治理/飞轮时 (conf=0.80)
    · 先 git log --since=昨天 看 commit 时间密度
    · ssh cloud 看真数据
    · 对照 4-14 宪法三 Yes
    · 承认旧 memory 是历史 · 不倒批今天判断

🟢 当前心智 (≤24h): N · 优先信任
🟡 近期 (1-7d): N · 可参考
🔴 历史 (>7d · 别当现状): N
```

### 路径 2 · BGE daemon (Claude 主动调 · 1.8s)

```bash
python3 ~/.claude/plugins/zenmind-mem/recall.py --bge --query "<问题>"
```

输出:
- Persona drift score + 反锚点 alert (如命中)
- BGE 召回 top 5 memory + cosine score + age
- 24h 内 fresh memory 即便低 cosine 也提示 (心智优先)

### 路径 3 · CLI 工具

```bash
# Strategy 管理
python3 strategy_store.py list             # 列所有
python3 strategy_store.py lookup "<query>" # 测命中
python3 strategy_store.py stats            # 统计

# A-MEM 重算
python3 links_finder.py                    # cross-cosine 全扫

# Daemon
bash daemon_start.sh                       # 启 (BGE cold ~30s)
bash daemon_stop.sh                        # 停
python3 daemon.py ping                     # 健康检查
```

## 路线图

| 版本 | 能力 | 状态 |
|---|---|---|
| v0.1 | metadata + age 分组 | ✅ |
| v0.2 | stdin 拿 prompt + BGE 召回 + cache | ✅ |
| v0.3 | Persona drift + 反锚点 alert | ✅ |
| v0.3.5 | daemon mode · BGE keep loaded · 41s → 1.8s | ✅ |
| v0.4 | Strategy Store (关键词命中) | ✅ |
| v0.5 | A-MEM cross-cosine supersede 检测 | ✅ |
| v0.6 | Stop hook 自动 strategy 蒸馏 | ✅ |
| **v1.0** | install.sh + 全文档 + 准备开源 | ✅ **当前** |

## 性能实测

| 操作 | 时间 | 备注 |
|---|---|---|
| Hook (metadata + strategy) | 0.5s | 每个 prompt 自动 · 不阻塞 |
| BGE daemon warm 召回 | **1.8s** | Claude 手动调 · 23x 加速 vs inline |
| BGE inline cold | 41s | daemon 不可用 fallback |
| BGE inline 第一次 cold | 120s | 73 file 全 embed |
| A-MEM links 算 (72 file) | 1.5s | 利用 daemon embedding cache |
| Stop hook 自动蒸馏 | 0.3s | 0 BGE 0 LLM · 关键词重叠 |

## 测试覆盖

- `selftest.py` · 8 项基础 · 全 PASS
- `deeptest.py` · 19 项边界 · 全 PASS (包括 cache mtime / 跨项目 / emoji / 字段名兼容)

## 商业化

蓝图 NAUTILUS_V5_ARCHITECTURE_FINAL.md 4-14 宪法第 3 条 "AI 员工" 衍生品:
- claude-mem 是简单 markdown 备忘
- V5 plugin 是认知层 (vector + drift + strategy + dynamic link)
- 卖给开发者: ¥499/月 (跟禅心 AI / 创投日报同档)

## 关闭

```bash
bash daemon_stop.sh
# settings.json 删除 UserPromptSubmit + Stop hook 即可
```
