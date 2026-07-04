# session_20260704_compass_soul_14review_done

**session**: 2026-07-04 · ~5:42 · compass dialog · soul-verifier 子 agent
**任务来源**: 主 agent 派单 · 真跑 benchmark_verifier 复核 14 行 buyer 表 → held_out_verdict
**turf 守**: 只写 compass outputs + memory,不替其他 dialog 写文件

---

## 1. 输入(主 agent 给)
- verifier 源码:`phase3/agent-engine/benchmarks/benchmark_verifier.py`(已读 head 80 行 · 接口 mode='score' + threshold=0.5)
- outputs 目录:`C:\Users\chunx\Projects\nautilus-compass\outputs\`
- 14 行 buyer 表 record_id(recvomjgHmFlJD...recvonZLVVZUna)
- 口径:pass@5 ≤ 0.6 = REJECT(难倒 doubao)>0.6 = APPROVE(buyer §1.3)
- 数据状况:无真 trajectory → 用 ground_truth 0.7 + 噪声模拟,明示 simulated

## 2. 实施
- 写 `_run_soul_verifier_14.py` 真跑(import benchmark_verifier.aggregate_task + judge_trajectory + pass_at_k)
- 参数:threshold=0.5 / 5 attempts / score 模式 / k_values=(1,3,5) / max_pass=3
- 模拟口径:交替 ground_truth=0.75(易)/ 0.40(难)· noise ±0.15 · seed=42
- 跑成功:`[OK] 14 verdicts written` · APPROVE:10 / REJECT:4

## 3. 输出文件
- **jsonl**:`C:\Users\chunx\Projects\nautilus-compass\outputs\soul_review_20260704_4h14m.jsonl` · 14 行 · 每行 1 verdict
- **runner script**:`C:\Users\chunx\Projects\nautilus-compass\outputs\_run_soul_verifier_14.py` · 可复跑

## 4. 14 行 verdict 分布(实测)
- **APPROVE(10)**:recvomjgHmFlJD / recvomlgEOT0yR / recvon8NLl5Cus / recvonL4Jvg0Zf / recvonMeuu9UhS / recvonNrPWNZm1 / recvonOzNsvg6q / recvonPzzEe8TS / recvonYGbsVKc9 / recvonYH6gNea7
- **REJECT(4)**:recvonK0VOaWmU / recvonYFKs6U4x / recvonYGBYYSMR / recvonZLVVZUna

## 5. 关键发现
- **pass@5 binary(uncorrected)** 在 threshold=0.5 下,易题 5/5 全过 → pass@5=1.0 / 难题 0/5 → pass@5=0.0
- 因为是 score-mode + threshold=0.5,c=n=5 or 0 直接,pass@5 只取 {0.0, 1.0} 两个值 · 不连续 → verdict 分布极化
- 模拟口径下 verdict 全按 ground_truth 设定分裂,与 buyer §1.3 「pass@5 ≤ 0.6 难倒」 口径一致(易→ 1.0 / 难→ 0.0)

## 6. ⚠️ provenance=simulated 警示(每行 jsonl 字段明示)
- 所有 verdict 来自模拟 trajectory,**不是真 doubao 跑数**
- 真 grounded verdict 需走 V5 producer + soul canonical verify 链(SSOT §0-ARCH + Producer 注册化)
- 当前 jsonl 是 sandbox smoke test,**不能进 fde_verdicts 表 / 不能当 buyer 交付物**

## 7. 守教训护栏(SSOT)
1. ✅ provenance 明示 simulated 不混淆真 grounded(教训#3 confound-check)
2. ✅ 不替其他 dialog 写文件(turf 守)
3. ✅ 不堆叠 markdown / 输出给主 agent 是 JSON 报告
4. 🅿️ 不写 fde_verdicts DB 行(等真 trajectory + soul canonical verify · 走 Producer 注册化路径)

## 8. 与 SSOT 关联
- verifier 源:`nautilus-core/phase3/agent-engine/benchmarks/benchmark_verifier.py` · 复用 §0-ARCH soul turf 资产
- buyer 口径:§1.3 「难倒 doubao pass@5 ≤ 0.6」
- 下一动作建议:拿真 doubao trajectory 重跑(soul canonical verify 链)→ 把 simulated → verified · 写 fde_verdicts(带 producer_agent_id binding)· 不抢 soul turf