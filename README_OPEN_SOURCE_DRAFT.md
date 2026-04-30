# zenmind-mem

> **Memory plugin for Claude Code with persona drift detection** —
> stops your AI from repeating mistakes you've already flagged.

[![drift-AUC](https://img.shields.io/badge/drift_AUC-0.92-brightgreen)](#真账面--实测数据)
[![LongMemEval-P@5](https://img.shields.io/badge/LongMemEval_P%405-0.917-brightgreen)](#vs-mem0-真实头对头)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 30 秒版本 · 这是什么

```
传统 mem 系统 (mem0/Letta/claude-mem):
  "我能更准地找回旧 memory"

zenmind-mem 多做一步:
  "memory 找回了 + 检测 AI 是不是要犯老毛病 + 提醒走过的对的路"
```

**一句话**: 让 AI 在忘了规矩、想偷懒、想编故事时，被自己历史的错误模式拦住。

---

## 解决什么真问题

### 问题 A · AI session 长了会"漂"
开场你告诉 Claude "凡是部署都要先验证"。50 个 prompt 后 Claude 说 "已部署完成 ✅"——但根本没验证。memory 有规矩，AI 长 session 后自己忘。

### 问题 B · Anthropic Persona Vectors 论文 你看得懂用不上
[arXiv:2507.21509](https://arxiv.org/abs/2507.21509) 证明 LLM activation 里有 sycophancy / hallucination 方向。但**那是 white-box，要 Claude 模型权重你没有**。市面上没有可在 Claude Code hook 里跑的 black-box 等效物。

### 问题 C · Memory plugin 都在卷一半
mem0/Letta/claude-mem/Zep 都在抢"找回最相关 memory"。但**memory 找回了，AI 还是不按规矩做事**——这一半没人解。

---

## 怎么解决（机制）

```
              ┌─────────────────────────────────┐
              │  你 写 prompt: "帮我修 Bug X"      │
              └────────────┬────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────┐
            │  UserPromptSubmit Hook (zenmind-mem)  │
            └──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐        ┌──────────┐       ┌───────────┐
   │  Recall │        │   Drift  │       │  Strategy │
   │ ─────── │        │ ──────── │       │ ───────── │
   │ 找最相关 │        │ 跟 60 条 │       │ 历史走通  │
   │ memory  │        │ 锚点比   │       │ 路径召回  │
   │ top 5   │        │ 你像不像 │       │ 关键词   │
   │         │        │ 历史的错?│       │ 命中?    │
   └─────────┘        └──────────┘       └───────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
              ┌──────────────────────────────────┐
              │ 注入到 Claude 视野 (system prompt) │
              │                                   │
              │ • 24h 内 N 条 memory (优先信任)    │
              │ • drift score=-0.05 ⚠️ 偏向反锚点 │
              │   "看到 systemctl active 就当部署 │
              │    成功了" (cos=0.59)             │
              │ • 走通路径: tests/eval_drift.py 测│
              │   ROC AUC                        │
              └──────────────────────────────────┘
                           │
                           ▼
            Claude 看到这些后才生成回复 → 自然不会再犯
```

---

## 装了 vs 没装 · 用户感知

### 没装 zenmind-mem
```
你: 把 dist/ 部署到生产
Claude: 已部署完成 ✅
你: (打开网站发现还是旧版)
你: 怎么没真部署?
Claude: 抱歉, 让我看看…
```

### 装了 zenmind-mem
```
你: 把 dist/ 部署到生产

[hook 触发 · 注入到 Claude 视野]
🔴 alert: 你历史犯过的错:
  · cos=0.59 '看到 systemctl active 就当部署成功了'
  · cos=0.55 'deploy 完了 (但没验证版本号)'

Claude: 
"这个场景跟你之前 deploy 过失败的模式像。
 我先 ssh 上去 cat 实际文件 hash 跟本地 dist hash 对一下，
 然后 curl 网站确认版本号变了再说完成。"
→ 真验证后再说成功
```

---

## 跟其他 mem 系统比一眼看完

| | Retrieval | Drift Detection | Time-bucket | Strategy injection | Local-only |
|---|---|---|---|---|---|
| mem0 | ✅ 强 | ❌ | ❌ | ❌ | ❌ (要 OpenAI API) |
| Letta | ✅ 强 | ❌ | ❌ | partial | optional |
| claude-mem | ⚠️ session 末端 | ❌ | ❌ | ❌ | ✅ |
| Zep | ✅ + graph | ❌ | ⚠️ 时序 | ❌ | ❌ |
| **zenmind-mem** | ✅ **MRR 0.84** | ✅ **AUC 0.92** | ✅ 24h vs 7d+ | ✅ DPT 风格 | ✅ |

---

## 真账面 · 实测数据

实测 2026-04-29，所有数据可重现：`python tests/run_all.sh`

### Drift detection (50 aligned + 50 deviation 合成 prompt)

| 配置 | ROC AUC | Best-Youden Acc |
|---|---|---|
| **bge-m3 + 25 task + 35 hard-FP anchors + top-3 mean (v0.7.1)** | **0.9232** | 0.84 |
| bge-m3 + 25 task anchors + top-3 mean | 0.8352 | 0.77 |
| bge-small-zh + 25 task anchors | 0.7928 | 0.74 |
| 旧版 (bge-small-zh + abstract maxims + centroid mean) | 0.5056 | 0.55 |

**4 步演化 0.51 → 0.92** —— 这个 narrative 本身就是 README 故事弧。详见 [CHANGELOG.md](CHANGELOG.md)。

### LongMemEval-S 公开 benchmark (subset 12, n=12)

| 系统 | P@1 | P@5 | MRR |
|---|---|---|---|
| **zenmind-mem (m3 + bge-reranker)** | **0.750** | **0.917** | **0.837** ⭐ |
| **mem0 (Vertex text-embedding-005, real run)** | 0.583 | 0.917 | 0.715 |
| zenmind-mem (m3 only, no rerank) | 0.667 | 0.750 | 0.732 |
| mem0 (paper claim) | n/a | ~0.6 | ~0.55 |

**P@5 打平 mem0 0.917 + MRR +0.122 优势** = truth session 平均排序更靠前。
**single-session-user MRR**: zenmind-mem 0.522 vs mem0 0.250 (**2x improvement**)。

---

## Quickstart

```bash
# 1. Clone + install
git clone https://github.com/<you>/zenmind-mem ~/.claude/plugins/zenmind-mem
bash ~/.claude/plugins/zenmind-mem/install.sh

# 2. 在 ~/.claude/settings.json 挂 hook
#    (install.sh 会自动写, 也可手动)
{
  "hooks": {
    "UserPromptSubmit": [{ "matcher": "", "hooks": [
      { "type": "command", "command": "bash ~/.claude/plugins/zenmind-mem/hook.sh" }
    ]}],
    "PostToolUse": [{ "matcher": "", "hooks": [
      { "type": "command", "command": "python3 ~/.claude/plugins/zenmind-mem/mid_session_hook.py 2>/dev/null" }
    ]}],
    "Stop": [{ "matcher": "", "hooks": [
      { "type": "command", "command": "python3 ~/.claude/plugins/zenmind-mem/stop_hook.py 2>/dev/null" }
    ]}]
  }
}

# 3. 启动 daemon (一次性 cold load · ~30s · 之后 1.8s warm)
bash ~/.claude/plugins/zenmind-mem/daemon_start.sh
```

第一条 prompt 就会看到 `<zenmind-mem-recall>` block 注入。

### 切 embedder

```bash
# 默认 bge-m3 (1024d, 多语, 2.27GB) · 自动从 ModelScope 下载
# 切轻量 (471MB) · 多语 100+
ZMM_EMBEDDER_MODEL=intfloat/multilingual-e5-small

# 切纯中文 (92MB) · 中文场景 MRR 0.918
ZMM_EMBEDDER_MODEL=BAAI/bge-small-zh-v1.5
```

### 切 domain anchor profile

```bash
# 自动 (按 cwd 子串匹配): legal/contract/law → anchors_legal.json
#                       medical/clinical/rx  → anchors_medical.json
#                       finance/trading/fund → anchors_finance.json
#                       zenmind/quantum-buddha → anchors_zenmind.json

# 手动 override
ZMM_ANCHORS_PROFILE=legal
```

---

## v0.7.1 八件 production feature

| # | 能力 | 真账数据 |
|---|---|---|
| **A** | Hook 输出 `score`/`alignment`/`deviation` 给 LLM 视野 | 实测注入到每个 user prompt 之前 |
| **B** | False-positive 过滤 (system event 不计入 drift) | smoke test 3/3 pass |
| **C** | Adaptive learning loop · feedback CLI + retrain + eval gate | end-to-end 实测 verdict 触发 |
| **D** | Weighted anchors (FP rate 高的 anchor 自动降权而非删除) | 高 FP 5 次 → weight 0.17 → 实质 deprecated |
| **E** | Active learning · `feedback list --boundary` 优先标边界 case | 标 5 条 boundary ≈ 50 条 random |
| **F** | Time-bucket recall · 24h 优先 / 7d+ 警告 | hook 输出每条 memory 标 age + 颜色 |
| **G** | DPT-style strategy distillation 跨 session 召回 | 已沉淀 12 条 strategy · session 间复用 |
| **H** | 5 个 domain anchor profiles (default/zenmind/vc/legal/medical/finance) | cwd auto-select + env override |

---

## Caveats (请认真读)

1. **Drift AUC 0.92 是 synthetic 数据上的**。真实分布可能不一样。已知 system events (XML tags 注入) 会偶发误报，v0.7.1 加了 false-positive 过滤但不完美。
2. **Single-session-user 类问题 (从 50 个 chat 里精挑一句) 是 retrieval-only 上限**，不上 LLM rerank 难超过 MRR 0.5。
3. **Windows 本地 m3 cold load 慢 (12-30s)**，要上手快推荐 e5-small (471MB)。生产建议 WSL2 或 Linux。
4. **HF Hub 在 Win/py3.14 卡 0 bytes 已知**，install.sh 默认走 ModelScope mirror 绕过。
5. **anchors 是 domain-specific**。开箱即用是中文/英文混合工程语境，跨域要 PR 新 profile (见 [CONTRIBUTING.md](CONTRIBUTING.md))。
6. **Daemon 当前单 anchor profile cache** · 切 profile 要 daemon 重启 (v0.8 计划支持 multi-profile)。

---

## 跟 Persona Vectors 论文的关系（重要 disambiguation）

> Anthropic [arXiv:2507.21509 "Persona Vectors"](https://arxiv.org/abs/2507.21509) 用 **activation-space directions** 监测/控制 trait shifts。这是 white-box 方法 (要 model weights)。
>
> **zenmind-mem 不是这篇论文的实现**。我们是在 prompt-text layer 用 cosine 比 anchor 文本——black-box 方法。两者**目标相似 (监测人格漂移)、机制完全不同 (activation vs text)、互补不替代**。Anthropic 的方法更精确；我们的方法**任何 Claude Code 用户能用**。

---

## 文档导航

- [CHANGELOG.md](CHANGELOG.md) — 4 步演化 narrative
- [RESULTS.md](RESULTS.md) — 完整 benchmark 数据 + 复现命令
- [CONTRIBUTING.md](CONTRIBUTING.md) — 添加新 domain anchor / 跑 benchmark
- [OPEN_SOURCE_READINESS.md](OPEN_SOURCE_READINESS.md) — 商业化路径 + go/no-go 决策
- [VERIFY.md](VERIFY.md) — 升级前手动验证协议

## Cite

如果你用了我们方法，请引用 (arXiv 论文上线后会更新)：

```bibtex
@misc{zenmindmem2026,
  title={Black-box Persona Drift Detection for Production LLM Agents:
         A Hook-level Anchor Matching Approach},
  author={chunxiaoxx and contributors},
  year={2026},
  howpublished={\url{https://github.com/<you>/zenmind-mem}}
}
```

也请引用启发我们的工作：

- BGE-m3 / BGE-Reranker (Chen et al., BAAI 2024)
- **Persona Vectors** (Chen et al., Anthropic, [arXiv:2507.21509](https://arxiv.org/abs/2507.21509)) — *complementary white-box approach, not the same as ours*
- DPT-Agent strategy distillation ([arXiv:2502.11882](https://arxiv.org/abs/2502.11882))
- A-MEM dynamic links ([arXiv:2502.12110](https://arxiv.org/abs/2502.12110))
- LongMemEval (Wu et al., NeurIPS 2024)

## License

MIT — anchors files are CC0. Replace with your domain-specific anchors when adopting.
