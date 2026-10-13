---
name: orgfuel-ORGH-60af0faa3dd92083-fb04270f8c
description: "工具决策记录 e1_j2_batch_judge_ood_7b.py E1·J2 OOD 盲判批处理·7B 升级版(Qw"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-60af0faa3dd92083
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 e1_j2_batch_judge_ood_7b.py
E1·J2 OOD 盲判批处理·7B 升级版(Qwen2.5-VL-7B bf16 · 判官升级程序·验收③补跑)。

升级纪律:判据/PROMPT/解析与 3B OOD 版(e1_j2_batch_judge_3b.py)逐字零改动
(判据不因模型升级而变——只许更严);改动仅四处:模型路径(直接 /root/sysmodels 7B,
去掉 modelscope 探测)、输出文件名(_7b 后缀防覆盖)、CSV 输出名(goldpack_ood_J2_7b.csv)、
版本署名(compass-AI-7B)。

判读协议照《判官须知》:五组作答(完成度/执行质量/置信/正问/反问),直觉式
短判断,看不清→无法判断+低置信;独立作答。断点续跑(逐题落 jsonl,重跑跳过)。
材料: /root/runtime/e1_judge_pack/judge_pack/(blind_data.js + frames/)
产出: /root/runtime/e1_judge_pack/ood_j2_answers_7b.jsonl + goldpack_ood_J2_7b.csv
