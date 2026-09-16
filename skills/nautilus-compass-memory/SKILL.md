---
name: nautilus-compass-memory
description: Local-first long-term memory for AI agents via MCP — zero LLM calls at write time, typed retrieval at read time. Use when session decisions and pitfalls should survive across days, when multiple agents or dialogs share facts on the same filesystem, or when you want drift detection so past mistakes don't repeat. Verified claims only — every published number ships as a byte-recomputable, ed25519-signed evidence pack.
---

# Nautilus Compass Memory

Open-source memory & reliability layer for AI agents (Modified MIT). Raw text is
embedded locally with BGE-m3 — **no extraction LLM at ingest, no graph, no data
leaving the machine**. All intelligence lives at read time (semantic + keyword
hybrid recall, drift scoring against real failure anchors).

Works with Claude Code / Claude Desktop · Cursor · Cline · Continue.dev · Zed ·
any MCP client. Local daemon or hosted gateway.

## 1 · When to use

Any of these:

- **Memory should outlive the session** — decisions, pitfalls, configs, and
  post-mortems from past sessions should come back when relevant, days later.
- **Multiple agents / dialogs share one filesystem** — several agents working on
  the same repo need a shared fact base, not four private notebooks.
- **The same mistake keeps repeating** — compass scores every prompt against an
  anchor set of real failure patterns (drift detection) before the agent acts.

Skip when: one-shot tasks with no memory dependency, or the user explicitly
opts out of prior context.

## 2 · How to connect (~3 minutes)

### Option A · Local daemon (recommended)

```bash
git clone --branch v3.2.0 --depth 1 \
  https://github.com/chunxiaoxx/nautilus-compass ~/.claude/plugins/nautilus-compass
# pinned to the audited commit — hard-fail if the tag ever moved:
[ "$(git -C ~/.claude/plugins/nautilus-compass rev-parse HEAD)" = "344290b0bb252c4a28305d351bb18a7f177718be" ] || \
  { echo "commit mismatch: audited code != cloned code — DO NOT run install scripts"; exit 1; }
bash ~/.claude/plugins/nautilus-compass/install.sh        # wires hooks for Claude Code
bash ~/.claude/plugins/nautilus-compass/daemon_start.sh   # start BGE-m3 daemon (once per boot)
```

Other MCP clients (Cursor / Cline / Continue.dev / Zed / Claude Desktop) —
auto-detect, backup, and patch their MCP config:

```bash
python ~/.claude/plugins/nautilus-compass/scripts/install_to_agent.py
```

What these scripts do, before you run them: download the local embedding
model, register hooks in `~/.claude/settings.json`, and patch each MCP
client's config — every file is backed up before writing; uninstall = remove
`~/.claude/plugins/nautilus-compass` and restore the backups.

Also on PyPI: `pip install nautilus-compass==3.2.0` (CLI + MCP server + A2A adapter).

### Option B · Hosted gateway (self-serve, no local model)

1. Sign up: <https://compass.nautilus.social/signup>
2. Create a scoped token in the web console
3. Point any MCP client at `https://compass.nautilus.social/mcp/`
   (Bearer token · streamable-http · per-user memory isolation)

> Data-egress note: the hosted gateway means memory content and recall
> queries are sent to compass.nautilus.social (per-user isolated). Use the
> local daemon (Option A) if data must not leave your machine.

### What you get

Core tools: `ingest_obs` · `recall` · `session_search` · `profile` ·
`drift_check` · `drift_history` · `feedback_log` (+10 advanced). Slash commands
in Claude Code: `/compass-recall` `/compass-verify` `/compass-drift`
`/compass-status` `/compass-search`.

> First recall after daemon idle can take up to ~90 s (model cold-load); the
> MCP client auto-retries once with an extended timeout.

## 3 · How to verify (don't trust us)

This project's differentiator: every claim it publishes is sealed as an
evidence pack — sha256 manifest, claims recomputable from payload bytes, an
ed25519-signed receipt. Verify with two commands, stdlib only, no third-party
deps:

```bash
git clone --branch v3.2.0 --depth 1 https://github.com/chunxiaoxx/nautilus-compass && cd nautilus-compass
[ "$(git rev-parse HEAD)" = "344290b0bb252c4a28305d351bb18a7f177718be" ] || { echo "commit mismatch — abort"; exit 1; }
# 1. full recompute (every claim recomputes from bytes — your receipt, not ours)
python -m tools.verifypack verify runtime/verifypack/arma_summary/pack \
  --out /tmp/my_receipt.json
# 2. signature + digest check
python -m tools.verifypack check runtime/verifypack/arma_summary/pack \
  --receipt runtime/verifypack/arma_summary/pack/receipts/receipt.json \
  --pubkey f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be
```

Want your verdict under **your** key?

```bash
python -m tools.verifypack keygen --out-dir .verifypack --name you
```

Re-run `verify`, sign, and send the receipt — independent reproduction beats
self-report, and the [Reproducibility Wall](../../docs/REPRODUCIBILITY_WALL.md)
publishes contradicting numbers with the same prominence as favorable ones.

---

## 中文版

**Nautilus Compass Memory** — AI 智能体的本地优先长期记忆层(MCP 协议)。
写入时零 LLM 调用(纯本地 BGE-m3 向量,数据不出机器),读取时做语义+关键词
混合召回;另带漂移检测(对照真实失败模式锚点集打分,防止重复犯错)。

### 何时用

- 会话里的决策/踩坑/配置需要**跨天保留**,几天后还能被召回
- 多个智能体或多个对话框**共享同一文件系统事实**
- 想要**漂移检测**:同样的错误不再犯第二遍

### 如何接(约 3 分钟)

本地(推荐):

```bash
git clone --branch v3.2.0 --depth 1 \
  https://github.com/chunxiaoxx/nautilus-compass ~/.claude/plugins/nautilus-compass
# 钉住已审计 commit——tag 若被动过则硬失败:
[ "$(git -C ~/.claude/plugins/nautilus-compass rev-parse HEAD)" = "344290b0bb252c4a28305d351bb18a7f177718be" ] || \
  { echo "commit 不符:审查过的代码 != 克隆到的代码——勿跑安装脚本"; exit 1; }
bash ~/.claude/plugins/nautilus-compass/install.sh        # Claude Code 钩子
bash ~/.claude/plugins/nautilus-compass/daemon_start.sh   # 启动 BGE-m3 daemon(每次开机一次)
```

其他 MCP 客户端: `python ~/.claude/plugins/nautilus-compass/scripts/install_to_agent.py`
(自动检测 Cursor/Cline/Continue.dev/Zed/Claude Desktop,备份后写入其 MCP 配置)。
脚本会下载本地嵌入模型、注册 Claude Code 钩子、改动各客户端 MCP 配置——每处改动前
逐文件备份;卸载=删除插件目录+还原备份。

云托管自助: 注册 <https://compass.nautilus.social/signup> → 控制台建 scoped
token → MCP 端点 `https://compass.nautilus.social/mcp/`(Bearer · streamable-http)。
出域提示: 云托管=记忆内容与召回查询会发送到 compass.nautilus.social(用户级隔离);
数据不能出本机请用本地方式。

### 如何验(不信自报)

```bash
git clone --branch v3.2.0 --depth 1 https://github.com/chunxiaoxx/nautilus-compass && cd nautilus-compass
[ "$(git rev-parse HEAD)" = "344290b0bb252c4a28305d351bb18a7f177718be" ] || { echo "commit 不符,中止"; exit 1; }
# 1. 全量复算(每条声明从字节复算,产出你自己的回执)
python -m tools.verifypack verify runtime/verifypack/arma_summary/pack \
  --out /tmp/my_receipt.json
# 2. 签名+摘要校验
python -m tools.verifypack check runtime/verifypack/arma_summary/pack \
  --receipt runtime/verifypack/arma_summary/pack/receipts/receipt.json \
  --pubkey f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be
```

本项目对外公布的每个数字都随附 sha256 清单+字节级复算+ed25519 签名回执的
证据包;矛盾的复算结果同样上墙,不删不利条目。
