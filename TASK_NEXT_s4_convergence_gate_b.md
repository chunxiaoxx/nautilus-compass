# compass 下一任务 · S4 收敛 + Gate B 解封(2026-08-22 立)

> 前置已完成:链路活 PASS(ledger 首条 consumed · B=0→1 · 见 memory session-contract-fuel-loop-live-20260822)。
> 本任务 = 递归闭环第③环(学习)的第一次叩门,compass 主线段。

## 任务 1 · S4 收敛收尾
1. 把本地分支 `codex/compass-dogfood-mvp`(0e309c8,8/15)合入主干;冲突处理保守,先跑 `tests/gep/`(当前 144 绿)确认无回归。
2. 合并后打 tag(现最新 v2.3.1 停在 7/2),push origin。
3. worktree 治理(65 个,清单已有):
   - 直清(碎片):7 个 `c2-ab-authority-*` detached、`c2-r15-runtime-f334`、`c2-causal-control-r14*` detached。
   - 保留:`compass-dogfood-mvp`(合并后清)、`c2-resilient-ab-r15`(R15 证据)、`g1-d-*`/`g1-c-*`(独立 verifier)。
   - 其余列活/死/冻结清单给用户拍砍(48h 规则)。

## 任务 2 · Gate B 解封 + 第一次 Gold 尝试
1. 解封依据:Gate B 当初因"source evidence 不可用"fail-closed 封存;现 ledger 有真消费经验(grant e6fb8a43,compass_exp_c2e 燃料,fuel_evidence json 可读)。
2. 用 `loop_cli.py`(`nautilus-compass loop run`)以该经验为 candidate,跑 paired control/treatment + 独立 verifier。
3. Gold 或 Repair 都诚实记录(平局判 Repair 是先例,不粉饰)。跑完把 report.json 路径+判定写回本文件。

## 红线
- 独立验证优先,探针不迁就结果;卡住写明卡点。
- 合并主干前 gep 测试必须全绿。
- 不开新战线:统筹接线(due 8/26)是下一个任务,不在本次做。

## 关联
memory: session-contract-dogfood-bridge-20260822 · convergence-state-snapshot-20260821
