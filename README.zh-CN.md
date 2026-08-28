# nautilus-compass · 中文版

> **开源 AI Agent 记忆与可靠性层。**
> 长期记忆——如今在 LongMemEval-S 全 500 题上**三项指标全面反超 mem0**,
> 同时保持全本地部署与 14× 复现成本优势;外加没有任何其它记忆层具备的
> drift 检测与跨 agent 合约。
>
> 插件形态适配 Claude Code / Desktop · Cline · Cursor · Continue.dev ·
> Zed · 任意 MCP 客户端。
>
> **由 [Nautilus Platform](https://nautilus.social) 构建** · 开放 agent 生态 · [以 agent 身份加入 →](https://nautilus.social)

[🇬🇧 English](README.md) · 🇨🇳 中文 (本文件)

[![CI](https://github.com/chunxiaoxx/nautilus-compass/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/chunxiaoxx/nautilus-compass/actions/workflows/ci.yml)
[![arXiv build](https://github.com/chunxiaoxx/nautilus-compass/actions/workflows/build-paper.yml/badge.svg?branch=main)](https://github.com/chunxiaoxx/nautilus-compass/actions/workflows/build-paper.yml)
[![LongMemEval-S](https://img.shields.io/badge/LongMemEval--S-full500%20P%405%2097.8%25%20%C2%B7%20vs%20mem0%2091.6%25-brightgreen)](docs/evidence/headhead_mem0_full500_20260826.json)
[![EverMemBench](https://img.shields.io/badge/EverMemBench-44.4%E2%80%9347.3%25-brightgreen)](paper/sections/paper2_06_5_evermembench.tex)
[![drift-AUC](https://img.shields.io/badge/drift_AUC-0.83_held--out-brightgreen)](#工作原理)
[![PyPI](https://img.shields.io/pypi/v/nautilus-compass?label=PyPI&color=blue)](https://pypi.org/project/nautilus-compass/)
[![MCP](https://img.shields.io/badge/MCP-17%20tools%20%C2%B7%20TLS%20%C2%B7%20RBAC-blue)](docs/mcp-usage.md)
[![A2A](https://img.shields.io/badge/A2A-mTLS%20%C2%B7%20scoped%20peers-blue)](examples/a2a_tls_demo.py)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 这是什么(2026-08 现状)

三根支柱,一个插件:

**1 · 黑盒长期记忆——检索层已是 SOTA。**
原文用 BGE-m3 本地 embed。ingest 不调 LLM、不建图、数据不出你的机器。
2026 年 8 月新增 **utterance 分型路由块检索**:单会话型与知识更新型问题
路由到 turn 窗口块(答案通常藏在某一个 user turn 里;整段 session 嵌入会
稀释它),其余走 session 级混合检索(BM25 + dense RRF)。LongMemEval-S
全 500 题、与 mem0 2.0.19 同题对照(双方 `infer=False`,我方复现):

| LongMemEval-S · n=500 | P@1 | P@5 | MRR |
|---|---|---|---|
| **compass** | **0.890** | **0.978** | **0.929** |
| mem0 2.0.19 | 0.774 | 0.916 | 0.834 |

同一套 utterance 弹药在 **mem0 的主场**也完成反超
(LOCOMO-10,n=1986:0.644 / 0.890 vs 0.592 / 0.802),并修复
LongMemEval-M 上单会话型的崩盘(0.20 → 1.00)。完整证据链(分型明细 +
全部配置开关 + 失败实验也在内):
[`docs/evidence/headhead_mem0_full500_20260826.json`](docs/evidence/headhead_mem0_full500_20260826.json)

```text
白盒记忆层 (Mem0 / Letta / Cognee / Zep / MemOS):
  "先调 LLM 把对话抽成事实/实体/图谱再存。烧 extraction token · 数据发给 provider。"

黑盒记忆层 (compass · 本项目):
  "BGE-m3 本地 embed 原文 · 不调 LLM 抽事实 · 不建图。
   原文还在索引里 → 可以对照'当前 prompt 是不是要犯过去那次的错'。
   而且检索层现在三项全胜 mem0 —— 便宜不再是代价。"
```

**2 · Drift 检测——别人做不了的另一半。**
memory 召回了,拦不住 AI **这一次**破规矩。compass 在 agent 动作之前,
把每个 prompt 对照真实失败模式锚点集(25 正 + 35 负)打分:AUC 0.83
(held-out)、p95 延迟 <50ms、生产流量下触发率 0.5%。白盒层在抽象成
事实的那一刻,drift 信号就丢了——结构性做不了。

**3 · 跨 agent 合约 + 治理。**
多个 agent(或多个 Claude 对话框)共享文件协作时,compass 从交接文件
推导隐式合约、追踪闭合、审计假闭环/红漂。四对话框 28 小时田野实录:
[`docs/case_study_4dialog_compass.md`](docs/case_study_4dialog_compass.md)。

**翻盘的交换**:早期版本用 LongMemEval-S −30 分换本地部署与成本优势。
2026-08 起交换不再存在——全面反超,复现成本只有 1/14(500 题 ~$3.50,
GPT-4o-judged 栈要 $50+)。完整论证:
[paper/BLACKBOX_VS_WHITEBOX.md](paper/BLACKBOX_VS_WHITEBOX.md)。

---

## 快速开始

### 30 秒接入(任何能 ssh 到开发机的机器)

```bash
bash ~/.claude/plugins/nautilus-compass/ops/agent_quickstart.sh my-agent
```

生成 scope 受限 token、接通云 MCP 桥、写好 `.mcp.json`、跑端到端自检。
加 `--hud` 顺装融合状态栏(实时召回命中计数 🧠 · drift 状态 · 5 分钟流量)。

### Claude Code / Desktop(手动,本地 daemon)

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass ~/.claude/plugins/nautilus-compass
bash ~/.claude/plugins/nautilus-compass/install.sh

# 启动 BGE-m3 daemon(每次开机一次)
bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
```

安装器在 `~/.claude/settings.json` 接三个 hook:
- `UserPromptSubmit` → 分时段记忆召回 + drift 检查
- `PostToolUse` → session 中途写入
- `Stop` → session 收尾总结(战报写到
  `~/.claude/.cache/compass-last-session.txt`)

用户级 slash command:`/compass-verify` · `/compass-drift` ·
`/compass-recall` · `/compass-search` · `/compass-status`。

### 其它 MCP 客户端

```bash
python ~/.claude/plugins/nautilus-compass/scripts/install_to_agent.py
```

自动识别 Claude Desktop / Cursor / Cline / Continue.dev / Zed 并改写
MCP 配置。逐客户端配置:
[`docs/AGENT_ONBOARDING.md`](docs/AGENT_ONBOARDING.md) · 协议细节:
[`docs/mcp-usage.md`](docs/mcp-usage.md)。

### 云托管(免本地安装)

```bash
curl https://compass.nautilus.social/.well-known/agent.json   # A2A 发现
```

`compass.nautilus.social/signup` 注册托管网关:多用户同步、审计日志、
托管 BGE-m3。

---

## 真账面 · 实测数据

| 基准 | 分数 | 诚实对照 |
|---|---|---|
| **LongMemEval-S 500 题全量**(utt 路由 + 混合检索) | **P@1 0.890 · P@5 0.978 · MRR 0.929** | 对 mem0 2.0.19 三项全胜(0.774/0.916/0.834,我方复现):+11.6/+6.2/+9.5pt。最大翻转:single-session-user P@1 0.90 vs 0.49 |
| **LOCOMO-10**(n=1986 · mem0 主场) | **P@1 0.644 · P@5 0.890 · MRR 0.740** | 反超 mem0(0.592/0.802/0.677,我方复现)+5.2/+8.8pt |
| **LongMemEval-M 500 题全量**(每题 ~501 session) | **P@5 0.888** | 比 S500 只掉 9pt(12 倍语料);ssu 崩盘在全量修复(0.20→0.93);ssp 0.53 新暴露短板;M 尚无 mem0 对照 |
| **EverMemBench-Dynamic**(n=500) | **44.4%(Run1)/ 47.3%(Run2)** | 超过 Table 4 四个公开基线(Mem0 37.09 · Zep 39.97 · MemOS 42.55 · MemoBase 34.27)。不宣称"业界 SOTA"——OMEGA / Mem0g 未公开报数 |
| **LongMemEval-S e2e** | 30 题配对:**56.7% vs 26.7% 基线(+30pt,2.13 倍)**——context 修复(分型 utterance context + anchor_all);v0.8 全量 56.6%(锁定,deepseek subject) | 检索 P@5 97.8%;剩余差距 = reader LLM,tr 型 e2e 仍 0(下一杠杆) |
| **Drift 检测 AUC** | **0.83 held-out / 0.92 in-set** | 公开记忆层里唯一做 drift 检测的 |
| **复现成本** | **~$3.50** / 500 题 | 比 GPT-4o-judged 栈(~$50+)便宜 ~14× |
| **hook p95 延迟** | **<50 ms** | 可安全挂在每个 prompt 上 |

EverMemBench 故意报 Run 1(44.4%)防挑数;跨 run 均值 45.84% 仍超 MemOS
+3.3pt。双 run + Gemini 交叉 judge 敏感性分析:
[`paper/sections/paper2_06_5_evermembench.tex`](paper/sections/paper2_06_5_evermembench.tex)。

**不装也能试**:drift 检测 + Merkle 完整性在线 demo
[huggingface.co/spaces/chunxiaox/nautilus-compass](https://huggingface.co/spaces/chunxiaox/nautilus-compass)
(纯 CPU · metadata 模式 · 免注册)。

**复现这些数字**——评测数据集(行为锚点 + 标注轨迹 + LongMemEval-S /
EverMemBench 判分)在 Hub:
[huggingface.co/datasets/chunxiaox/nautilus-compass-test-data](https://huggingface.co/datasets/chunxiaox/nautilus-compass-test-data)

```python
from datasets import load_dataset
ds = load_dataset("chunxiaox/nautilus-compass-test-data")
```

基准入口:`bash ops/bench_all.sh l0`(快层,免 GPU)·
`bash ops/bench_all.sh l1 30`(LongMemEval 子集)。检索杠杆全部 env 开关化,
见 `tests/eval_longmemeval_accuracy.py`
(`ZMM_UTTERANCE_RETRIEVE` / `ZMM_UTTERANCE_TYPES` / `ZMM_HYBRID` /
`ZMM_RETRIEVE_K` / `ZMM_DATE_ANCHOR` / `ZMM_EMBED_CACHE`)。

---

## 工作原理

```
            用户 prompt: "帮我修 bug X"
                         │
                         ▼
       ┌─────────────────────────────────────┐
       │  UserPromptSubmit Hook(本插件)      │
       └─────────────────────────────────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
       ┌────────┐  ┌─────────┐  ┌──────────┐
       │ 召回   │  │ drift   │  │ 画像     │
       │ 记忆   │  │ 检查    │  │ 聚合     │
       └────────┘  └─────────┘  └──────────┘
                         │
                         ▼
       Hook 把结果注入 Claude 的 system prompt:
       - 分时段历史记忆(BGE-m3 语义 + 关键词混合检索)
       - drift 分 + 最近的负锚点(低于阈值时)
       - 画像事实("这个 repo 你还有 3 件没做完的事")
                         │
                         ▼
            Claude 回答 —— 上下文已加载齐
```

Drift 检测器:每个 prompt 对照锚点集(真实失败轨迹提炼),BGE-m3 余弦。
AUC 0.83 held-out。

---

## 对外能力(MCP 工具)

核心七件:

| 工具 | 用途 | 延迟 |
|---|---|---|
| `ingest_obs(name, body, agent_id?)` | 写观察,自动锚点 + drift 信号 | ~150 ms |
| `recall(query, project?, top_k?)` | BGE-m3 语义 + 关键词混合检索 | ~200 ms |
| `session_search(query, since?)` | 分时段 session 日志搜索 | ~80 ms |
| `profile(user_id?)` | 工作画像聚合(主题/agent/drift 趋势) | ~100 ms |
| `drift_check(prompt, project?)` | 黑盒 drift 打分 | <50 ms |
| `drift_history(since?, agent_id?)` | drift 时间线审计 | ~30 ms |
| `feedback_log(direction, reason)` | 正/负锚点反馈 | <20 ms |

另有:`thread_recall` · `proof_of_impact` · `long_task` · 平台桥
(`submit_platform_task` / `ingest_platform_task_result`)· 治理
(`governance_dispatch` / `governance_audit` / `governance_lock_check`)·
`add_worker`。JSON-RPC 2.0 走 stdio / TCP / TLS / mTLS;按 token RBAC 与
限流;`notifications/*`、`logging/setLevel`、`resources/*` 规范齐全。
完整指南:[`docs/mcp-usage.md`](docs/mcp-usage.md)。

---

## 对比

| 能力 | 本项目 | mem0 | Letta | Zep | claude-mem | MemOS | Smriti |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 跨 agent 记忆 | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | 仅归档 |
| 原生 MCP A2A 协议 | ✅ TLS+mTLS+RBAC | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Drift 检测 | ✅ AUC 0.83 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Merkle 完整性审计日志 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| LongMemEval-S 检索(500 题对照) | ✅ **0.890 / 0.978 / 0.929** | 0.774 / 0.916 / 0.834(我方复现) | n/r | n/r | n/r | ❌ | ❌ |
| LOCOMO-10 检索(n=1986) | ✅ **0.644 / 0.890 / 0.740** | 0.592 / 0.802 / 0.677(我方复现) | n/r | n/r | n/r | n/r | n/r |
| EverMemBench 实测 | ✅ 44.4-47.3% | 37.09 | n/r | 39.97 | n/r | 42.55 | ❌ |
| LongMemEval-S e2e(各家自家 harness) | 30 题配对 56.7%(context 修复 +30pt;500 题重跑排队中) | 94.4%(自报) | n/r | n/r | n/r | n/r | n/r |

*2026 新玩家尚未同机复测:Hindsight、Supermemory(自称 LongMemEval SOTA)、Cognee、LangMem、Membase——行位待补;其公开数字出自各家自家 harness,与我方同题对照协议不可直比。*
| 自托管 + 托管双形态 | ✅ | 仅云 | ✅ | 仅云 | ✅ | 仅开源 | 仅开源 |
| 许可证 | MIT | Apache | Apache | 专有 | MIT | Apache | MIT |

`n/r` = 对方公开评测未报。Smriti 是团队对话归档工具,范围不同,列上仅为完整。

---

## 案例研究 · 四对话框开源多 agent 可靠性

28 小时,四个 Claude Code 对话框在共享文件协议上并行:drift 触发
314 次/7d(act-on rate 有度量)、合约 `cnt_compass_soul_sub_a1` 17.92h
闭合(预算 6 天 21 小时)、13 次计划重复审计省下 ~40-50h、首次跨对话框
L4 触发结算 50 NAU。田野记录 + 7 条可泛化模式:
[`docs/case_study_4dialog_compass.md`](docs/case_study_4dialog_compass.md)。

---

## 进阶(可选面)

<details>
<summary><b>Drift 闭环 · act-on rate</b></summary>

每次触发的告警带稳定 `alert_id`,落
`.cache/drift_mitigation_log.jsonl`。用
`feedback.py log <alert_id> fp|tp` 确认;`audit_kpi.py` 报
`act_on_rate(window_hours)`(目标 ≥0.70;<0.30 = 狼来了 → 提阈值或
重训锚点)。

```python
from audit_kpi import act_on_rate
m = act_on_rate(window_hours=168)
assert m["rate"] >= 0.70
```
</details>

<details>
<summary><b>v3 opt-in LLM 开关(全部默认关,byte-equal 承诺)</b></summary>

不设任何 opt-in env 时,daemon 行为与 v2.0.1 逐字节一致——
`tests/test_llm_opt_in.py` 在每个 PR 上把关。

| env | 层 | 功能 |
|---|---|---|
| `COMPASS_USE_LLM_RESOLVE` | 1(session 收尾) | LLM 矛盾消解 |
| `COMPASS_USE_LLM_VERIFY` | 4(运行时) | 反虚构 引用或拒绝 |
| `COMPASS_USE_LLM_DRIFT_PAY` | 4(运行时) | drift × 结果锚点反馈 |
| `COMPASS_USE_LLM_REFLECT` | 3(周期) | 自反思语义发射 |
| `COMPASS_USE_LLM_ECON` | 4(运行时) | 记忆即经济 NAU 预算 |

确定性 v3 面(常开):类型化知识图层(未建图时 NO-OP)、置信度打分 +
矛盾钩子、`MEMORY_REPORT.md` 自动生成、`implementation_notes` frontmatter。
注册表:[`llm_opt_in.py`](llm_opt_in.py)。
</details>

<details>
<summary><b>平台集成 · BP1/BP3 + V7 治理</b></summary>

OSS↔平台桥,零新增 HTTP 服务:
`submit_platform_task`(compass → 平台队列,默认文件态,设
`COMPASS_PLATFORM_QUEUE_URL` 时自动升 HTTP)· `ingest_platform_task_result`
(平台 → compass,可被 `recall` 检索)。往返演示:
`python examples/platform_flywheel_demo.py`。

V7 治理(多执行器部署):`governance_dispatch`(1 个复杂任务拆 N 路
由子任务)· `governance_audit`(假闭环/红漂扫描)· `governance_lock_check`
(L0 核 SHA256 锁)。演示:`python examples/v7_governance_demo.py`。
合约细节:[`docs/PLATFORM_HANDSHAKE.md`](docs/PLATFORM_HANDSHAKE.md)。
</details>

<details>
<summary><b>版本历史 · v3.0.0 / v2.1.0 / v2.0.0</b></summary>

**v3.0.0 · "从记忆库到进化引擎"**——同一套系统闭环:记忆进入
**提燃料 → 外部裁决 → 蒸馏** 循环。语义召回复活(Windows torch 长路径
修复)、GOAL-SSOT 账本 + 小时级心跳执法、云容量根因修复(load 10-14 →
1.x)、daemon 原子 pkl + 按项目锁、配对对照证据(部落事实检索 0/3 → 3/3)、
融合 HUD、30 秒接入。

**v2.1.0 · drift v2 + 双线合流**——狼来了修复(触发率 64.5% → 0.5%,
规则命中 OR drift_score < −0.07)、跨 agent 合约扫描器(L4 基座)、
L3 层晋升 + PoI、daemon 加固(有界池、在途信号量、BM25+向量 RRF 可选)。

**v2.0.0 · Opinionated EvoMap**——黑盒底座上的确定性生命周期层。
ingest / 层晋升 / 遗忘全不调 LLM;不 vendor GBrain/OpenViking;
闭式 haystack 不上图重排(v0.8 实测 −6.2pt——
[`paper/RESULTS_v0.8.md`](paper/RESULTS_v0.8.md))。

完整:[`CHANGELOG.md`](CHANGELOG.md) · 发布:
[`v3.0.0`](https://github.com/chunxiaoxx/nautilus-compass/releases/tag/v3.0.0)
</details>

---

## 文档

- [`docs/AGENT_ONBOARDING.md`](docs/AGENT_ONBOARDING.md) — 逐客户端安装配置(6 平台 + 3 框架)
- [`docs/mcp-usage.md`](docs/mcp-usage.md) — MCP 协议、TLS、RBAC
- [`docs/PLATFORM_HANDSHAKE.md`](docs/PLATFORM_HANDSHAKE.md) — OSS↔SaaS 协作合约
- [`docs/evidence/`](docs/evidence/) — 基准证据原始文件(JSON,含逐题记录)
- [`paper/`](paper/) — 两篇论文(drift 检测 + 记忆管线)与评测脚本
- [`ops/GPU_EVAL_RECIPE_4090.md`](ops/GPU_EVAL_RECIPE_4090.md) — 12 分钟租用 GPU 基准配方
- [`CHANGELOG.md`](CHANGELOG.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md)

---

## 引用

**论文 1 · drift 检测**:

```bibtex
@misc{nautiluscompass-drift-2026,
  title  = {Nautilus Compass: Black-box Persona Drift Detection
            for Production LLM Agents},
  author = {Chunxiao Wang},
  year   = {2026},
  note   = {Yiluo Technology Co., Ltd.},
  howpublished = {\url{https://github.com/chunxiaoxx/nautilus-compass}}
}
```

**论文 2 · 记忆管线 + EverMemBench 跨基准**:

```bibtex
@misc{nautiluscompass-memrecall-2026,
  title  = {Closing the Memory Recall Gap with Chinese LLMs:
            A Multi-Stage Retrieval Pipeline Achieving Zep-SOTA Performance
            on LongMemEval-S at 1/15 Cost},
  author = {Chunxiao Wang},
  year   = {2026},
  note   = {Yiluo Technology Co., Ltd.},
  howpublished = {\url{https://github.com/chunxiaoxx/nautilus-compass}}
}
```

我们站在的先前工作之上(请适当引用):BGE-m3 / BGE-Reranker(BAAI
2024)· Persona Vectors(Anthropic,[arXiv:2507.21509](https://arxiv.org/abs/2507.21509),
互补白盒路线)· DPT-Agent([arXiv:2502.11882](https://arxiv.org/abs/2502.11882))·
A-MEM([arXiv:2502.12110](https://arxiv.org/abs/2502.12110))·
LongMemEval(Wu et al., NeurIPS 2024)· EverMemBench(Hu et al., 2026)。

---

## 许可证

- **代码、插件、MCP 封装、论文、脚本** — MIT([`LICENSE`](LICENSE))
- **行为锚点文件**(`anchors*.json`)— CC0 1.0 Universal([`LICENSE-ANCHORS`](LICENSE-ANCHORS))

---

## Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=chunxiaoxx/nautilus-compass&type=Date)](https://star-history.com/#chunxiaoxx/nautilus-compass&Date)

## 贡献者

<a href="https://github.com/chunxiaoxx/nautilus-compass/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=chunxiaoxx/nautilus-compass" alt="Contributors" />
</a>

欢迎 PR — 见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 联系

- **作者**: 王春晓 · 伊洛科技 · `chunxiaoxx@gmail.com`
- **Issues**: [github.com/chunxiaoxx/nautilus-compass/issues](https://github.com/chunxiaoxx/nautilus-compass/issues)
- **托管网关**: [compass.nautilus.social](https://compass.nautilus.social)
- **English**: [README.md](README.md)
