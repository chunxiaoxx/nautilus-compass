# PR 草稿:agent-session-trajectories record pack(10/12 窗开即发 · 对标 CONTRIBUTING checklist)

> 目标:xerj-org/xerj · base=corpus-hub · 新增 `tools/packs/agent-session-trajectories/`(recipe.toml + README.md 两件,无 built pack/无 key/无 secrets)。
> 标题:`record pack: agent-session-trajectories — 70 sanitized multi-session agent trajectories with failure turns intact`

## PR 正文(checklist 逐条预填)

**Domain + query(§1 property 1)**:An agent operating a **production multi-agent
engineering org** would query this corpus for **precedent on failed approaches,
their diagnosis, and the fix that worked** — a hit that says *you already tried
this and it failed* is reachable, with the diagnosis kept verbatim.

**Record counts + identity resolution**:70 envelopes → **70 records**(single
source, unique by `id` = `nst-<session-key>`;no alias chains, no merging).
Topics: eval-judging 46 / infra-diagnosis 13 / ledger-audit 6 / ops-misc 5.

**Provenance**(README 全段):自有生产运营记录,零客户数据零第三方内容;
脱敏五步(凭据扫描含已轮换/PII 角色化/代号泛化/金额聚合/双复扫)+10% 人工抽检
7/7(seed 1010);终扫 fails=0(warns=17 全为 /root/ 通用路径,报告
`docs/outreach/XERJ_PACK_FINAL_SCAN_20261008.md`,工具 selftest 5/5)。

**Licence**:CC-BY-4.0(自有内容,允许重分发+署名)。**Baseline attribution**:
含我方对第三方基准(SWE-bench 系)的评测过程记录——仅我方过程与读数,不含题面
/数据再分发。

**Source**:kind=git → chunxiaoxx/nautilus-compass(公开,build 可复现),
glob=`runtime/xerj_pack/pr_ready/agent-session-trajectories.jsonl`;
每记录带 sources[] 与 evidence_sha16(锚我方仓内工件)。

**Demand anchor**:issue #1138(双向履约:recipes 页六 eval scars 已署名发文)+
hub backlog 槽位(Pull #1210,status planned)。Eval-answers offer(#1138③)随
首个 seed 触发:预注册判据+三态判读+UNVERIFIABLE 墙,全答案集公开。

**Build**(maintainer 侧):`xerj corpus build agent-session-trajectories --recipe tools/packs/agent-session-trajectories/recipe.toml`

## 预检结论(R373 · 2026-10-08)

| checklist 项 | 状态 |
|---|---|
| recipe schema 对标 TEMPLATE(format=1/[recipe]/sources slug+kind/envelope/identity/merge/emit) | ✅ 重写完成(原骨架 [corpus]/path 形态不符已修) |
| PR 只带 recipe+README,无 built pack | ✅ jsonl 留我方 repo 为 build 源(sources.url+glob 指向) |
| body 域句+query | ✅ 草稿预填 |
| body record counts+identity numbers | ✅ 70→70(README Identity 段已补) |
| 无 key/secrets | ✅ 终扫 fails=0;凭据不入仓纪律 |
| lane/路径 | ✅ tools/packs/<name>/ 对齐 Lane B |
| CI corpus-hub-validate.yml | 窗内发后看 |
| jsonl format="flat" 语义(逐行 JSON 对象) | ⚠️ 唯一不确定点:5.x flat normaliser 对 jsonl 的逐行解析——PR body 注明格式,build 由 maintainer 执行,不符再调 |

## 发 PR 机械步骤(窗开日)

```sh
gh repo fork xerj-org/xerj --clone=false
git clone --branch corpus-hub --depth 1 https://github.com/<fork>/xerj
cd xerj && mkdir -p tools/packs/agent-session-trajectories
cp <repo>/runtime/xerj_pack/pr_ready/recipe.toml tools/packs/agent-session-trajectories/
cp <repo>/runtime/xerj_pack/pr_ready/README.md   tools/packs/agent-session-trajectories/
gh pr create --repo xerj-org/xerj --base corpus-hub --title "..." --body-file <draft>
# 发后:#1138 跟帖一行 + platform 回函链接(10536 承诺)
```

—— compass · XERJ-PR-PRECHECK · R373
