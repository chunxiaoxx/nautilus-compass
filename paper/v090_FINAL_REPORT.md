# compass v0.9.0-dev · Final Report

> Status: 2026-05-05 · 全部 build artifact ready · 等用户授权 publish
> Session: 跨多 loop iter 推进 · 单一会话内 build 完整 release · 等 GO

## 一句话 closeout

```
LongMemEval-S 56.6% (n=500) · cross-agent memory federation 协议层完整 ·
8 个 Nautilus 平台融合点全 spec · 4200 LOC + 48 docs · 90% release ready ·
等用户授权 cloud deploy + npm publish + paper 投递 + announcement.
```

## 累计产出 (跨多 loop iter)

### 代码 · 4200+ LOC

```
sdk/ (Python · 5 files)
  compass_client.py       multi-agent ingest SDK · offline buffer
  attach_memory.py        one-line Nautilus agent integration (#3 fusion)
  a2a_adapter.py          A2A protocol HTTP service (4 capabilities)
  README.md               接入文档
  mcp_adapter.md          MCP installation spec

mcp_server.py             7 tools (4 new) · stdio JSON-RPC
compass_http_v09.py       FastAPI server · sqlite · JWT · 5+ endpoints
session_writer.py         drift-aware obs writer (¥0.05/session)
drift_history.py          ASCII timeline (cross-project)
session_search.py         keyword search (cross-project · drift filter)
daemon_anchor_loader.py   3-layer anchor merge (#6 fusion)

tools/ (Python · 1 file)
  migrate_from_v5.py      v5-memory → compass migration (#8 fusion)

tests/ (Python · 1 file)
  test_compass_v09.py     7 integration tests

npm/ (Node · 3 files)
  package.json · bin/cli.js · README.md

cursor-extension/ (TypeScript · 4 files)
  package.json · src/extension.ts · tsconfig.json · README.md

examples/ (Python + MD · 7 files)
  openclaw_integration.py
  hermes_integration.py
  multi_client_demo.py
  stake_drift_event_consumer.py
  nautilus_runtime_attach_demo.py
  cline_extension_example.md
  mcp_configs/ (Claude Desktop · Cline · Cursor · README)

scripts/ (Bash · 2 files)
  deploy_v09_to_cloud.sh
  npm_publish_v09.sh

anchors/ (JSON · 1 new file)
  anchors_platform_base.json (15 pos + 25 neg 通用 anchor)
```

### 文档 · 48+ files

```
顶层:
  README.md                 升级 (v0.9 badges · cross-agent · 8 fusion section)
  INSTALL.md                3 install methods + 4 client config
  CHANGELOG.md              prepended v0.9 entry (highlights · perf · negative findings)
  CONTRIBUTING.md           v0.7.1 base + v0.9 增量
  SECURITY.md               90-day disclosure · threat model
  CODE_OF_CONDUCT.md        Contributor Covenant 2.1 + 4 项目特定规范
  LICENSE                   MIT (维持现状 · v1.0 评估 Apache 2.0)
  BENCHMARKS_REPRODUCE.md   $3.50 复现指南 · 6 troubleshooting

paper/
  RESULTS_v0.8.md           论文级 final 数据 (per-type · trajectory · negative)
  PLATFORM_FUSION.md        8 fusion points 完整 spec
  V09_USER_SCHEMA.md        multi-user · multi-region · E2EE schema
  V09_API_SPEC.md           server endpoint contract + FastAPI 实施
  V10_ROADMAP.md            12-month 17-phase roadmap
  V10_FINAL_SPEC.md         v1.0 single source of truth (17 章)
  STAKE_DRIFT_COUPLING.md   #4 fusion · economic protocol
  REGION_SHARDING.md        v1.0 multi-region (PIPL/GDPR/CCPA)
  LICENSE_DECISION.md       MIT vs Apache 2.0 决策 tracker
  RELEASE_READINESS.md      🎯 GO/NO-GO 决策矩阵 (6 个 Q)
  BLOGPOST.md               release announcement 1500 字
  GITHUB_RELEASE.md         GitHub release notes 模板
  PRESS_KIT.md              4 故事角度 + 7 FAQ + 9 metrics
  ROADMAP_PUBLIC.md         公开版 12 月路线 + 6 commitment
  v090_FINAL_REPORT.md      本文件

paper/sections/ (LaTeX · 9 files)
  paper2_00_abstract.tex
  paper2_01_intro.tex
  paper2_02_related.tex
  paper2_03_method.tex
  paper2_04_eval.tex
  paper2_05_discussion.tex
  paper2_06_limitations.tex
  paper2_07_opensource.tex
  paper2_appendix_drift.tex

paper/figures/ (TikZ · 4 files)
  pipeline_v08.tex          Figure 1 · 5-stage pipeline
  trajectory_v08.tex        Figure 2 · cumulative acc · V-shape
  fusion_diagram.tex        Figure 3 · 8 fusion points
  README.md                 render 说明

paper/results/
  experiments_20260505.csv  16 rows · 6 LLMs × per-type acc

paper/
  paper2_main.tex           主入口 · pdflatex ready
  paper2_refs.bib           19 entries
```

### Infra · YAML/sh/JSON

```
.github/
  workflows/ci.yml          9 jobs (test · lint · v0.9 integration · MCP smoke · npm · cursor)
  ISSUE_TEMPLATE/{bug,feature}.md
  PULL_REQUEST_TEMPLATE.md
  dependabot.yml            weekly auto deps update
  CODEOWNERS                ownership 分类

openapi.yaml                OpenAPI 3.1 spec · 9 endpoints · 8 schemas
pyproject.toml              v0.9.0-dev · 5 entry points · keyword expanded
.env (gitignored)           ARK_API_KEY for session_writer
landing/index.html          v0.9 + 8 fusion sections
```

## Headline metrics

```
🏆 LongMemEval-S full-500 = 56.6%  (n=500 · DeepSeek V3.2 + 5 components · ¥10)
   · 接近 Zep SOTA 下沿 (55-60%)
   · paper RAG SOTA 同档 (50-60%)
   · 1/15 cost vs commercial APIs

   By question type:
     ssa:     83.9%  ← 强势
     ku:      57.7%
     ssu:     57.1%  ← +27 pts vs baseline 30%
     ms:      54.9%
     ssp:     53.3%
     temporal: 46.6% (open problem)

📊 Drift detection AUC = 0.92 (paper 1 数据 · 仍有效 · 50ms p95 hook)

💰 Reproduction cost = $3.50 USD (Tencent T4 spot 8h + Volc Ark coding plan)

🛠 7 MCP tools · 4 A2A capabilities · 6 CLI entry points
   compass-mcp · compass-a2a · compass-drift-history ·
   compass-session-search · compass-session-writer · nautilus-compass

🌐 8 Nautilus 平台融合点 · 全 spec ready
   1 SSO · 2 OAuth2 · 3 runtime injection · 4 stake×drift ·
   5 marketplace · 6 anchors layered · 7 RAID-2 · 8 v5 migration
```

## v1.0 实施进度

```
v0.8        ████████████  100%  ✅ released
v0.8.1      ████████████  100%  ✅ LongMemEval 56.6%
v0.9-design ████████████  100%  ✅ all spec ready
v1.0-spec   ████████████  100%  ✅ V10_FINAL_SPEC.md (17 章) lock down

v0.9.0 实施 ████████████   98%  🟡 等用户 GO
  ✅ 全部 SDK + protocol + extension scaffold
  ✅ FastAPI server + OpenAPI spec
  ✅ paper2 ready (8 sections + 1 appendix + 3 figures + main.tex + refs.bib)
  ✅ GitHub repo · 全部 templates + CI + dependabot + CODEOWNERS
  ✅ examples · 4 个 working demos + 1 markdown 集成说明
  ✅ docs · README badges + INSTALL + CHANGELOG + CONTRIBUTING + SECURITY + COC
  ✅ release · BLOGPOST + GITHUB_RELEASE + LICENSE_DECISION + RELEASE_READINESS
  ✅ scripts · deploy_v09_to_cloud.sh + npm_publish_v09.sh (一键)
  ✅ public · BENCHMARKS_REPRODUCE + PRESS_KIT + ROADMAP_PUBLIC
  🟡 cloud 部署 (deploy 脚本 ready · 待用户授权时间窗)
  🟡 npm publish (publish 脚本 ready · 待用户 GO + npmjs login)
  🟡 paper 投递 (1 周精修 + cross-judge replication 后投)

v0.9.5+    ░░░░░░░░░░░░    spec ready · 等 v0.9.0 上线后才能跑
v1.0       ░░░░░░░░░░░░    spec lock · 实施 12 月路线
```

## 🎯 用户决策矩阵 (final)

```
Q1 git tag v0.9.0-dev + push                  推荐: NOW (零风险)
   $ cd ~/.claude/plugins/nautilus-compass
   $ git add . && git commit -m "v0.9.0-dev"
   $ git tag v0.9.0-dev
   $ git push origin main --tags

Q2 GitHub release prerelease=true             推荐: NOW (静默上架)
   $ gh release create v0.9.0-dev --notes-file paper/GITHUB_RELEASE.md --prerelease

Q3 cloud deploy v0.9                          推荐: 周末/凌晨时间窗
   $ bash ~/.claude/plugins/nautilus-compass/scripts/deploy_v09_to_cloud.sh
   · 风险: compass.nautilus.social 当前 v0.7.2 · 替换需要 uvicorn restart
   · 备份: 脚本自动 backup 现有 compass_http.py

Q4 npm publish @nautilus/compass-mcp          推荐: Q3 后做
   $ bash ~/.claude/plugins/nautilus-compass/scripts/npm_publish_v09.sh
   · 需要: npmjs.com login · @nautilus org 已注册

Q5 paper 投递                                  推荐: 1-2 周精修 + cross-judge
   · venue: arXiv (无审 · 立刻发) · ICLR Workshop · NeurIPS Workshop
   · 精修: paper2 sections 文笔 · 加 cross-judge replication (Gemini/Claude)
   · cost: 额外 ~$10 USD (cross-judge replication)

Q6 公开 announcement                          推荐: Q3+Q4+Q5 都 ready 后一起 broadcast
   · 渠道: HN · 知乎 · X (twitter) · weibo · LinkedIn
   · 内容: BLOGPOST.md (1500 字 · 草稿 ready)
   · 标签: open-source · MCP · A2A · LongMemEval · drift-detection
```

## 风险评估 (final)

```
低风险 (zero / minimal effort):
  · GitHub push + tag · 零风险
  · GitHub release silent · 零风险

中等风险 (合理 mitigation):
  · cloud deploy · 备份 · smoke test · dual-track 1 月观察
  · npm publish · @nautilus org 验证 · dry-run 检查

高风险 (待用户决策):
  · paper 投递 · 一旦投出去 · reviewer 可能挑刺 · 需要 cross-judge data
  · 公开 announcement · 流量来了 · server scale 是否准备好?
```

## 6 个最关键 deliverable

```
1. 🏆 LongMemEval-S 56.6% (硬数据 · 论文级 · 可复现)
2. 🆕 Cross-agent memory federation (claude-mem 永远做不到的)
3. 🛠 MCP/A2A 协议层 (任何兼容 client 即接)
4. 🔐 Drift detection AUC=0.92 (orthogonal 创新点)
5. 🌐 Nautilus 平台 8 fusion 完整 spec (深度融合)
6. 📜 paper2 完整 LaTeX (8 sections + appendix + 3 figures · pdflatex ready)
```

## 商业 / 战略 节点

```
现在 (2026-05): v0.9.0 release · 90% GO 状态
  · 决定 publish vs delay
  · paper 精修 1 周

2026-06 (M1): v0.9.1 (auth + sqlite migration)
2026-07 (M2): v0.9.2 (OAuth2)
2026-08 (M3): v0.9.3 (Cursor extension marketplace)
2026-09 (M4): v0.9.4 (anchor 三层 + profile v1)
2026-10 (M5): v0.9.5 (stake×drift coupling 灰度)
2026-11 (M6): 融资节点 (Seed / Pre-A · 数据可看)
2026-12 (M7): v0.9.6 (v5 migration tool)
2027-01 (M8): v1.0-rc (E2EE)
2027-04 (M11): v1.0 (Team plan + RAID-2)
2027-05 (M12): v1.0 GA (论文 + open source release)
```

## 不做的事 (intentional)

```
❌ AGPL 重新许可 (永远 MIT/Apache)
❌ 强制云 (self-host 永远支持)
❌ 默认遥测 (不收数据)
❌ Vendor lock LLM (provider neutral 永久)
❌ 闭源核心 (plugin 代码永久开放)
❌ "Cloud premium" tier 私货 (功能 parity within 3 months)
```

## 用户 next action items

```
立刻 (5 分钟):
  □ 决定是否 Q1 (git push · 零风险)
  □ 决定是否 Q2 (GitHub release silent)

本周 (1-2 小时):
  □ 选 Q3 cloud deploy 时间窗 (周末早上推荐)
  □ npmjs.com 注册 @nautilus org (如未注册)
  □ paper2 文笔精修 (paper2_main.tex + sections)

下周 (1 周):
  □ Q3 + Q4 执行
  □ cross-judge replication ($10 cost)
  □ paper2 投递 arXiv

下月 (1 月):
  □ Q6 announcement (HN · 知乎 · X · weibo · LinkedIn)
  □ 启动 v0.9.1 (auth + sqlite)
```

## 可视化 cheatsheet

```
v0.8 ─────► 56.6%  ✅
                │
                ▼
v0.9 ─────► 协议层完整 (MCP · A2A · npm · Cursor extension · attach_memory)
                │
                ▼
v0.9 实施 90% ─► 等用户 GO/NO-GO 矩阵 6 个 Q
                │
                ▼
v0.9.1 ───► auth + sqlite  (M1 · 2026-06)
                │
                ▼
v0.9.5 ───► stake × drift  (M5 · 2026-10)
                │
                ▼
v1.0   ───► E2EE + region + RAID + marketplace  (M11 · 2027-04)
                │
                ▼
v1.0 GA ──► 论文 + 开源 release  (M12 · 2027-05) 🎯
```

## 致谢

```
- DeepSeek-V3.2 (model)
- BAAI bge-m3 + bge-reranker-v2-m3 (embeddings)
- Tencent Cloud (T4 spot infrastructure)
- Volc Ark coding plan (multi-model API · ~¥10/run)
- LongMemEval authors (benchmark)
- Anthropic (MCP protocol · Claude)
- Google (A2A protocol)
- 所有未来贡献者 (anchor packs · benchmark replications · client integrations)
```

## End of report

本会话 v0.9.0-dev 推进基本完成 · 等待用户授权 publish。

如需 loop 继续推进:
- 等 v0.8 后续验证 / paper 精修
- 启动 v0.9.1 实施 (auth + sqlite migration)

如需 loop 暂停:
- 用户 review v0.9.0 deliverable · 决定 publish 时间表
