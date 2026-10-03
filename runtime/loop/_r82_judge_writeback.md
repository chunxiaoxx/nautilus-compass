# [writeback:judge_writeback] pusht 首案+G1 判读索引(org_state v1 verdicts 落库)

judge: compass · cases: G1(三批)+pusht_first_case(四臂) · verdict 正本: A100 /root/vdd3/pipe_art/{g1_verdict,pusht_4win_verdict,pusht_pair_verdict,pusht_rollout_verdict}.json + compass 仓 runtime/loop/_r73_n100/rollout_n100_verdict.json(schema v2 迁移件已存档)

## 判读索引行

| case | 判据版本 | state | 核心读数 | 边界(claims.boundary) |
|---|---|---|---|---|
| G1 双臂差分 | criteria_J 帧级(v1) | VERDICT(valid) | ΔJ1=+2.5pp/ΔJ2=0,双链一致性(dir 40/40 同,ratio≤0.07) | 材料判读;"注入不传导"仍为 inferred |
| pusht 帧级配对 | v1 冻结 | PARTIAL | Wilcoxon p=0.00986,delta 中位+0.0627 | 归因级=抽样混杂已隔离;非效度终判 |
| pusht rollout n=100 | **v2-final**(用户裁+T1/T2 审定) | PARTIAL | 成功率 0/100 地板(冻结语义);coverage 配对 Wilcoxon p=0.00181 显著(meanΔ+0.081) | 修复方向显著有效(帧级+任务级双级);**达标性未证实**(FULL≥0.95 零触及);止损线生效不追加 |

## 附注

- 判据演进链留痕:v1 冻结→用户裁 v2(#2568)→compass 技术审定 T1/T2(#2574)→v2-final 冻结(#2610)
- 噪声底三级证据链:A2F/A2N 权重 70/70 leaf bit 同→帧级推理字节同→rollout 逐局 100/100 同
- 判读产物 schema:verdict_schema_v2(compass 仓 docs/protocol/),peer_case_spec 字段已预留与 flywheel case_spec 互引(会签函 2648 在途)

compass · 判分机构(judge_writeback 索引,org_state v1 协议首落)
