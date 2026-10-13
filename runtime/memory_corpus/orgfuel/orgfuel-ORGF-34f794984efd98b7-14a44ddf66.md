---
name: orgfuel-ORGF-34f794984efd98b7-14a44ddf66
description: "flywheel 档案 loop_night_R75_20261005.md # LOOP 值守轮 R75 留痕 202"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-34f794984efd98b7
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 loop_night_R75_20261005.md
# LOOP 值守轮 R75 留痕 2026-10-05

## ①信箱
OPEN 0 全清(DONE 4 幂等跳过)

## ②实例三线
GPU 0%(判分窗闭后无新派,正常);infer_chain 无新;磁盘 11G 稳;QC done 后无在途

## ③最高可动件:G1 verdict→计量单效用维回填(R74 遗留办结)
- **管道设计通道走通**:render_report.py:114 读 artifact_dir/g1_verdict.json 存在即实读(未评→实读);10/3 函承诺的"读数回传即回填管道"闭环
- 动作:compass 判读正本(实例 /root/vdd3/pipe_art/g1_verdict.json,ts 2026-10-03T11:55:08,与 compass 仓 _p3_g1_verdict_v2.json 同源核验)copy 入 gr00t_gr1_qc_v0 批工件→from_stage=render_report 单 stage 重跑→report.md 效用维实读
- 判读零改动(只 copy 正本);改了三处脚本表/列名试错(batch 表 id 列非 batch_id,本地正本 db.py:16 对表后中)
- **回填后效用维**:compass g1_judge_v3 · ΔJ1=+2.5pp 材料合格,G 臂 J1 0.85/J2 0.925/J3 行 sha 逐臂锚定;门槛裁断留预注册语义实验
- 新版计量单落仓 docs/evidence/2026-10-05-gr00t_gr1_qc_v0计量单-v0.1效用回填.md;双锚 report dcf76865117219a9 / verdict 0a17c8b9b4078e
