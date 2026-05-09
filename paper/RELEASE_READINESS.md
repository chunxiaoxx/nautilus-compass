# compass v0.9.0-dev · Release Readiness

> ⚠️ **SUPERSEDED 2026-05-08** · this doc reflects the v0.9.0-dev cycle.
> Current release line: **v1.0.0-rc2** (CHANGELOG.md is authoritative).
> Kept as-is for historical context · do not retrofit version numbers.
>
> Status: 2026-05-05 · 90% READY · awaiting user GO/NO-GO for cloud deploy + npm publish
> Decision owner: @chunxiaoxx (user)

## Recommendation

**GO** for soft-release on GitHub (push code + tag · no announcement) · then **GO/HOLD** decision on cloud deploy + npm publish · separately:

```
Step 1 (zero-risk):  GitHub push + tag v0.9.0-dev    ← can do now
Step 2 (low-risk):   GitHub release (with notes · no broadcast)  ← can do now
Step 3 (medium):     Update compass.nautilus.social to v0.9 server  ← needs cloud ssh + uvicorn migration
Step 4 (medium):     npm publish @nautilus/compass-mcp  ← needs npmjs account login
Step 5 (high):       Cursor extension marketplace上架  ← needs Microsoft Publisher account
Step 6 (high):       Public announcement (HN · 知乎 · X)  ← BLOGPOST.md ready · timing 用户决
```

## Deliverables Inventory

### ✅ Code (3700+ LOC)

```
sdk/                              # Multi-agent ingest SDK + protocol adapters
  compass_client.py               # offline buffer · E2EE-ready
  attach_memory.py                # one-line Nautilus integration
  a2a_adapter.py                  # 4 capabilities · HTTP service
  mcp_adapter.md                  # MCP install spec
  README.md                       # 3-line integration

mcp_server.py                     # 7 tools · v0.9.0-dev
compass_http_v09.py               # FastAPI server · sqlite · JWT
session_writer.py                 # session 蒸馏 ¥0.05/session
drift_history.py                  # ASCII timeline
session_search.py                 # cross-project keyword
daemon_anchor_loader.py           # 3-layer (platform_base + domain + tenant)

npm/                              # @nautilus/compass-mcp Node wrapper
cursor-extension/                 # VS Code extension scaffold

tools/migrate_from_v5.py          # v5-memory 迁移工具

tests/test_compass_v09.py         # 7 集成测试
```

### ✅ Documentation (36+ MD/TeX files)

```
README.md                         # cross-agent + 8 fusion section · 56.6%
INSTALL.md                        # 3 install + 4 client config
CHANGELOG.md                      # v0.9 entry · highlights · added · changed · removed
CONTRIBUTING.md                   # v0.7.1 base + v0.9 增量
SECURITY.md                       # 90-day disclosure · threat model
CODE_OF_CONDUCT.md                # Contributor Covenant 2.1
LICENSE                           # MIT
LICENSE_DECISION.md               # MIT vs Apache 2.0 决定 tracker

.github/
  workflows/ci.yml                # 9 jobs (test · lint · v0.9 integration · MCP · npm · cursor)
  ISSUE_TEMPLATE/{bug,feature}.md
  PULL_REQUEST_TEMPLATE.md
  dependabot.yml                  # auto deps update
  CODEOWNERS                      # ownership 分类

paper/
  RESULTS_v0.8.md                 # 论文级 final 数据
  PLATFORM_FUSION.md              # 8 fusion points
  V09_USER_SCHEMA.md              # multi-user multi-region E2EE schema
  V09_API_SPEC.md                 # endpoint contract + FastAPI 实施
  V10_ROADMAP.md                  # 12-month 17-phase
  STAKE_DRIFT_COUPLING.md         # economic coupling spec
  REGION_SHARDING.md              # v1.0 多 region (合规)
  RELEASE_READINESS.md            # 本文件
  BLOGPOST.md                     # release announcement 1500 字
  GITHUB_RELEASE.md               # GitHub release notes 模板
  
  paper2_main.tex                 # paper 2 主入口 (pdflatex ready)
  paper2_refs.bib                 # 19 entries
  sections/paper2_*.tex           # 8 sections + 1 appendix
  figures/{pipeline,trajectory,fusion}_v08.tex  # 3 TikZ figures
  results/experiments_20260505.csv # 16 rows · 6 LLMs × per-type
```

### ✅ Testing

```
tests/test_compass_v09.py         # 7 integration tests
sdk/a2a_adapter.py selftest       # A2A protocol roundtrip
mcp_server smoke (CI job)         # 7 tools enumeration
npm wrapper selftest              # python detection + spawn
.github/workflows/ci.yml          # 9 jobs · multi-Python × multi-OS
```

### 🟡 Performance / accuracy claims (verifiable)

```
LongMemEval-S full-500: 56.6%
  · per-question log:    .cache/longmemeval_acc_m3_rerank_full_1777975609.jsonl
  · summary:             .cache/longmemeval_acc_m3_rerank_full_1777975609_summary.json
  · 都在 T4 服务器 (43.173.164.32) · 用户可下载验证

Drift AUC: 0.92 (paper 1 数据 · v0.7.0 测的 · 仍有效)
  · 校准数据:            .cache/drift_calibration_*.jsonl
  · 测试集:              tests/eval_drift.py 复现
```

### 🟡 Deploy / publish (待用户授权)

```
□ git tag v0.9.0-dev + push (no risk · 反正只在 GitHub)
□ GitHub release create (paper/GITHUB_RELEASE.md 已 ready)
□ ssh cloud + replace compass_http.py → compass_http_v09.py + uvicorn restart
   (中等风险 · 影响 compass.nautilus.social · 用户在用)
□ npm publish @nautilus/compass-mcp (需 npmjs login + 2FA)
□ vsce publish nautilus.compass-cursor (需 Azure DevOps + Publisher 注册)
□ paper2 投递 (arXiv · ICLR workshop · 等用户决定 venue)
```

## Pre-flight checks (run before any push)

```bash
# 1. 测试通过
python tests/test_compass_v09.py

# 2. selftest pass
python sdk/a2a_adapter.py selftest
node npm/bin/cli.js --selftest

# 3. lint
ruff check .

# 4. CHANGELOG 同步
grep -q "0.9.0-dev" CHANGELOG.md

# 5. 关键文件存在
test -f LICENSE && test -f README.md && test -f SECURITY.md && test -f CODE_OF_CONDUCT.md
```

## Risk register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| compass.nautilus.social 部署破坏 v0.7.2 客户 | 低 | 高 | 双轨期 · v0.7.2 endpoint 保留 · 1 月观察 |
| npm publish 名字被抢 | 低 | 中 | @nautilus/ scope · 需先注册 organization |
| paper2 数据被 reviewer 质疑 | 中 | 中 | per-question log + summary.json 公开 · 可独立 verify |
| MCP protocol 大改 | 低 | 高 | 我们抽象层 · transport 替换不破坏 tools API |
| Anthropic 自己出 cross-agent memory | 中 | 中 | 协议优先 + 跨平台 (我们不绑 Claude · OpenAI/Cursor 都接) |
| Volc Ark coding plan 调价 | 中 | 中 | 我们 LLM 是 swappable · OpenAI/Anthropic-compatible |

## Decision matrix (给用户)

### Q1: 是否 GitHub push v0.9.0-dev?
- 推荐: **YES** · 零风险 · 反正只是 git tag
- 用户操作: `git tag v0.9.0-dev && git push --tags`

### Q2: 是否 GitHub release create?
- 推荐: **YES** · 但 hidden (不 announce 不 broadcast · 等 cloud + npm OK 再公开)
- 用户操作: 用 `gh release create v0.9.0-dev --notes-file paper/GITHUB_RELEASE.md --prerelease`

### Q3: 是否 cloud server v0.9 部署?
- 推荐: **HOLD** · 等用户在合适时间窗口 (周末? 凌晨?) 切换
- 风险: compass.nautilus.social 当前 v0.7.2 · 替换 needs uvicorn restart
- 用户操作: ssh cloud + 备份 + 部署 + smoke test

### Q4: 是否 npm publish?
- 推荐: **YES (after Q3)** · 因为 wrapper 要 server endpoint 才有用
- 用户操作: `npm login && npm publish` (在 npm/ 目录)

### Q5: 是否 paper 投递?
- 推荐: **HOLD** · 数据虽然 ready 但 paper 文本需要更精修 (我们写得快 · 没自审)
- 时间: 1 周精修 + 跑 cross-judge replication (Gemini/Claude 各跑一次 · 加 confirmation)

### Q6: 是否公开 announcement?
- 推荐: **HOLD** · 等 Q3 + Q4 + paper 投递都 ready 后一起 broadcast
- 时间: 估计 2026-05-XX (用户决)

## Final: GO checklist

```
□ User approves Q1 (push tag)
□ User approves Q2 (GitHub release · prerelease=true)
□ User approves Q3 (cloud deploy time window)
  □ ssh cloud + backup compass_http.py
  □ deploy compass_http_v09.py
  □ uvicorn restart with new server
  □ smoke test: curl https://compass.nautilus.social/healthz
  □ run examples/multi_client_demo.py against production
□ User approves Q4 (npm publish)
  □ npm login (chunxiaoxx)
  □ cd npm && npm publish
  □ verify: npx -y @nautilus/compass-mcp --selftest
□ User decides Q5 (paper 投递时间)
□ User decides Q6 (announcement 时间)
```

## Final summary

```
  90% READY · code complete · docs complete · tests pass · benchmark pass
   8% pending: cloud deploy + npm publish (user authorization)
   2% TBD:     paper venue + announcement timing
```

**Recommend**: tag + GitHub release (silent) NOW · cloud + npm + announcement at user's chosen window.
