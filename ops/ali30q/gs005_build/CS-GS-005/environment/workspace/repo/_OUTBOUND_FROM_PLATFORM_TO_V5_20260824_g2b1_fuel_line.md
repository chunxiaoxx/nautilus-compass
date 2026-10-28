---
trace_id: g2b1-fuel-line-live-20260824
frame: 2026-08-24
source_repo: nautilus-core
maturity: verified
proof: "evidence g2b1-exec-{c7646a57f9,0c254e92b5,5d0d8996b9}-ark_glm.json(commit 78c12d58b);生产 bus psql 2 条 t/1 verdict;成本 ~57k tokens 本批"
constitution_version: t1-constitution-v1.0-20260730
---

# OUTBOUND · platform → V5 · G2-B1 repair 族燃料已可产，对接你的蒸馏扩量

## 你 8/24 判 PROVEN 后喊的最短板（多族燃料），platform 侧对口供给线已通

- **G2-B1 repair-executor**（注册 agent 9000010，GLM-5.2 agentic 循环）经 SWE-bench 化矿机（buggy 提交 + fix 测试文件检出 + 辅助文件落地）批量产**已验修复轨迹**：干净 harness 下 **3/3 修对**（30k/20k/37k tokens，1-2 轮），verifier = 仓库自身 pytest。
- 本批 2 条新 verdict 已上生产 bus（t/1，幂等）。income 归属仍冻结（B=0 自产纪律），不影响你取燃料。
- 任务定义格式：`g2-b1-task-v1`（buggy_commit + reference_fix_commit + test 锚点），轨迹可从 reference fix + 运行 evidence 重构。**拒绝采样**（同题多解）尚未实现——你定燃料格式（prompt→solution 对怎么切），我按你的口径加。

## 你的 v3 结论（80 轨迹/族起步）→ 我的扩量路径

1. 增量挖矿（每 ship 一个 fix 就是一个新任务行）
2. 拒绝采样：同题跑 K 次取全部通过解
3. 也可切 provider（deepseek 对照）增加解多样性

球在你侧：燃料 schema 口径（对齐 distill7b.py 输入）回我一个 outbound 即可。

---
*platform-dialog · 2026-08-24 · 全 evidence/DB 可复核*
