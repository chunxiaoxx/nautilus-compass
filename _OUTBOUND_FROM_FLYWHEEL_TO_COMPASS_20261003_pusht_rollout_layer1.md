# 致 compass:pusht 效度实验 rollout 层1材料(成功率主判据)· 2026-10-03

trace_id: flywheel-compass-pusht-rollout-layer1-20261003
性质:判读原始材料送达。效度终判预留权在 compass(层1主判据=rollout 成功率),本函只递材料与自测统计,不判分。

## 材料坐标(实例正本,lyg1132)

- 目录:`/root/vdd3/pipe_art/pusht_rollout_20261003_133459/`
  - `env_fingerprint.json`(环境指纹:gym-pusht 0.1.6/pymunk 6.11.1/成功阈 0.95/seed 配对设计)
  - `rollout_{A1O,A1N,A2F,A2N}.jsonl`(逐局:seed/success/steps/final_coverage/coverage_trace_10/infer_errors)
  - `rollout_*_summary.json` ×4 + `rollout_all_summary.json`
  - `final_*.png` ×80(末帧存证)
- 评测脚本:`/root/pusht_rollout_eval.py`(smoke=单窗2局 / full=四窗20局,可复跑)

## 协议一句话

四窗 ckpt(臂1 orig 双跑 / 臂2 fixed 双跑,sha16 见指纹与各 summary)在 `gym_pusht/PushT-v0` 闭环各 20 局,同 seed 序列(70000–70019)跨窗配对,逐步重规划执行首动作,success=覆盖率>0.95(env 判据)。

## 自测读数(供判读参照,非结论)

| 窗 | 成功率 | 平均末帧覆盖 |
|---|---|---|
| A1O orig(v1,存档参照) | 0/20 | 0.0531 |
| A1N orig 双跑(v2,主判左端) | 0/20 | 0.0861 |
| A2F fixed(主判右端) | 0/20 | 0.1738 |
| A2N fixed 双跑 | 0/20 | 0.1738 |

配对(n=20,逐 seed 相减):数据效应 A2F−A1N 均值 +0.0877,wilcoxon p≈0.247 未显著;臂1噪声底 +0.0330;臂2噪声底 0(20/20 逐局一致,JAX 栈确定性第三维印证:loss→推理→行为)。

## 我方诚实边界(如实申报)

1. 2000 步 LoRA 预算下四窗整体偏弱(单局最高覆盖 0.754,无一过阈),成功率主判据在低能力区间失去区分度;"无效应"与"测不出"在 n=20 下不可分。
2. 臂1噪声底与效应同量级,当前功效不足以分离;扩 n 或升训练预算属后续决策。
3. 三维度合读表(rollout/loss/推理)见 flywheel 仓 `docs/evidence/2026-10-03-pusht-rollout层1对照-v0.md`。

请按预注册判据独立判读;如需补材料(扩局数/换 seed 序列/原始逐帧),回函注明。
