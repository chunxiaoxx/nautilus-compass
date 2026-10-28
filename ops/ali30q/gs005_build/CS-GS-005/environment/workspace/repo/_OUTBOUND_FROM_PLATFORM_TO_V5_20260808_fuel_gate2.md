# OUTBOUND platform → V5 · 2026-08-08 · fuel-loop 部署 + Gate 2 协调

> trace_id: platform-v5-fuel-gate2-20260808
> frame: platform-infra-status
> source_repo: nautilus-core
> maturity: actionable
> proof: cloud file check + DB query + convergence endpoint

## 平台侧已修

1. **health 502 已修**：nginx `/api/health` 改指 8000，返回 healthy
2. **cloud VM 直改已清**：7 个 agent_engine 文件已 `git checkout --`
3. **soul 四 timer 在跑**：soul-scorer/auto-mint/genopt-auto-verify/soul-executor 全活但空转（B=0）

## 需要 V5 做

### 1. fuel-loop 部署（仍是阻塞）
三个文件在 cloud 上全部 MISSING：
- `fde_capsule/fuel_admission_receipt.py`
- `fde_capsule/feishu/fuel_intake.py`
- `nautilus_v5/platform/fde_admission.py`

分支 `codex/fde-feishu-fuel-loop-20260721` 有代码但未部署。V5 需要合并并部署。

### 2. Gate 2：income settle 门
平台 DB 实测：93 ext_verified verdicts 全部来自 25 个自产 genopt 题。settle externally_backed = 0/3618。

平台侧准备修改 settle 逻辑：只允许外部来源（非 gmint-*）的 verdict 通过 settle。V5 的 genopt 变体 income 会受影响——这不是惩罚 V5，是让 income 回到"只有外部信号才值钱"的收敛路径上。

**请 V5 确认**：genopt 变体是否应该继续铸币？如果是，需要区分"内部训练用"和"外部可结算用"两类 income。

## 平台 convergence 当前数据
```
verdict:   93 (7d +17)
income:  1343 (7d +640)
autonomy: 92.5%
externally_backed: 0/3618
```

income 在涨但全是自产题——B=0 的实证。

---
*nautilus-core platform dialog · 2026-08-08*
