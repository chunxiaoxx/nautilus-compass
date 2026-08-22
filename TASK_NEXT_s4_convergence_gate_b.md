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

---

## ✅ 执行结果(2026-08-22 · 本 session 完成)

### 任务 1 · S4 收敛:完成
- `codex/compass-dogfood-mvp` 合入主线(59dad03,零冲突),393 测试绿。
- tag **v2.4.0** 已推(7/2 v2.3.1 之后首个)。
- worktree 65→55(直清 10 个 detached 碎片;dogfood-mvp 合并后清,分支保留作 PR 安全网)。
- 附带修复:安装冒烟测试环境前提显式化(115b746)。

### 任务 2 · Gate B 解封:机制实证完成,Gold 未达成(诚实 Repair)
- **Live 全链路首次真跑通**:真实 glm-5.3 provider + 独立语义 oracle + append-only journal + 事件哈希。
- 排障链(全部实锤):Cloudflare 拒 urllib UA(403/1010)→ 修 UA 头(66266dd 已推);代理无 glm-5.2[1m] 权限且映射到 glm-5.3 → suite 钉真实 identity;30s CLI 超时 → 改直连;防重放门(duplicate_attempt)与空目录门均正确拦截。
- **4 次真实尝试 0 Gold**:
  - source 2/4 过(oracle 要求 "bool" 先于 "int" 且含 "before" 的措辞序,模型自由散文常不满足——语义对但措辞序不符);
  - control 一次语义正确但写成 lambda(隐含约定:谓词须以 `value` 为变量,prompt 未明说);
  - 1 次 provider_output_invalid。
- **判:机制 ✅(fail-closed 全程无假 Gold),suite 契约标定 ❌**——fixture 是为完全合规 provider 设计的,真 LLM 接不住隐含约定。
- 运行档案:outputs/gate_b_live_*/gate_b_glm53_try*(report.json+artifacts+receipt 俱全)。

### 下一步(待批)
1. suite 标定修正:prompt 显式写明"answer 须为以 value 为变量的谓词表达式"+source 措辞契约 → 预期 Gold 概率大增(这是把隐含约定变显式,非放宽 oracle)。
2. 用 ledger 真燃料(compass_exp_c2e)构造真经验 suite 跑 Gate B。
