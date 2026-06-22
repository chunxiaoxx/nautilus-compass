# verdict 口径:难倒门 pass vs 解对 pass(2026-06-22)

> 起因:`fde_verdicts` source=compass 的 autolab 行把两套互不相同的 `overall_pass` 语义混用同一字段(齿轮③语义混)。本备忘钉死区分,供未来 ingest 分流。当前 14 行实测后只订正了 bvh_001(唯一不一致),其余 6 条 pass 各有正当语义、不动。

## 两套语义(同一 overall_pass 字段被混用)
1. **难倒门 pass(stump-gate · buyer 验收口径)**:`passk_threshold_met=true`(pass@5 ≤ 0.6,对 doubao 足够难)→ 作为**买方难倒题交付物**合格。score(=passk_reproduced,solver 良率)在此口径下**越低越好**(越难倒)。note 标 "难倒门 pass@5<..."。
   - 例:`levenshtein_001`(0.2)/`regex_engine_001`(0.4)/`stack_machine_golf_001`(0.4)= 合法难倒门 pass。
2. **解对 pass(solver-correctness · RSI/ratchet 口径)**:`score`(passk_reproduced)= solver 良率,**越高越好**;solver 解对(score 高)→ pass。
   - 例:`hash_join_001`(1.0)/`fft_rust_001`(1.0)/`aes128_ctr_001`(0.8)= 合法解对 pass(thr_met=false 仅表示对 doubao 不够难,非 solver 失败)。

## 唯一不一致(已订正)
- `compass_autolab_bvh_001`:score=0/passk_reproduced=0/thr_met=true/note="batch1"/原 pass=t。与同签名的 `ntt_cuda_001`、`gaussian_blur_001`(同为 0/0/true,均 f)矛盾——漏标。
- **订正(2026-06-22)**:`UPDATE ... overall_pass=false WHERE task_uid='compass_autolab_bvh_001' AND score=0`。backup `/tmp/compass_verdicts_backup_20260622.tsv`(14 行)。订正后 source=compass = 6t/8f,score=0 AND pass=t 的行 = 0。

## 未来 ingest 守卫(soul turf·compass 不重造写入器)
compass 对 fde_verdicts **只读**(GRANT SELECT TO compass_sub),那 14 行是手工 ingest。未来 verdict ingest 应:
1. 带 `verdict_kind ∈ {stump_gate, solver_correctness}` 显式标口径,**不再用单一 overall_pass 兼表两义**。
2. solver_correctness 路径:**score=0 强制 overall_pass=false**(bvh 类不再发生)。
3. 闲聊/占位 output:复用 soul 已部署的 `is_substantive_output` 守卫(`services/fde_scorer_poll.py`)→ 不送判不写 verdict。

→ outbound 已发 soul(`_OUTBOUND_FROM_COMPASS_TO_PLATFORM_SOUL_20260622_verdict_semantics_stump_vs_correctness.md`)。

关联 `docs/plans/2026-06-22-flywheel-convergence-design.md`(齿轮③)。
