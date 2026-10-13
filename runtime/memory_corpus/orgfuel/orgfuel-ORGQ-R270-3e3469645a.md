---
name: orgfuel-ORGQ-R270-3e3469645a
description: "### R270 · 2026-10-06 深夜(A+B+C 启动:判据档冻结+管道基线出数;发车留交接) - **B+"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R270
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R270 · 2026-10-06 深夜(A+B+C 启动:判据档冻结+管道基线出数;发车留交接)
- **B+C 预注册判据档冻结**(docs/metering/PRECOR_JUDGE_ROBUST_20261006.md):B=量化漂移矩阵(1.7B champion×{bf16/fp16/int8/int4}×{greedy/T0.3}=8 配置×292 题,部署合格线=对 bf16 一致率≥99% 预注册);C=软维度双跑一致性(k=5×两轨,只产数不定门,ER v2 数值=实测-2pp 判据修订序另冻)。
- **A 管道建成+基线出数[实测]**:tools/corpus_pipeline.py(合并三 split+delta,qid 防泄漏去重,SFT 清单+manifest+双触发器);首跑=1453 唯一 qid(拦 18 跨源重复)/train 1162/7B 缺口 1838/基线 sha16=2a0a8f0c825292f4/manifest_corpus_pipeline.json 落盘。
- **A100 环境探明[实测]**:Qwen3-1.7B 基座在盘(/root/vdd4/modelscope/models/Qwen--Qwen3-1.7B)+磁盘 36G 余+RAM 47G;E1 复算栈在 vdd4/e1_recheck(generate 配方可复用)。
- **发车留交接(4h 护栏+质量纪律)**:发车前置=1.7B champion 推理管线复原(prompt 构造在 P2 训练机 js2.blockelite.cn:15124 的 bootstrap_and_train.sh,未入仓)——管线拼错=实验白跑+白烧 GPU,不硬上。交接件:①从 js2 拉取管线脚本入仓 ②按 PRECOR 档写 robust_exp 脚
