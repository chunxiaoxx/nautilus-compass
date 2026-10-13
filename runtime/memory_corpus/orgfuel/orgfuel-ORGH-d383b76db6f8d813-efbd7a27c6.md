---
name: orgfuel-ORGH-d383b76db6f8d813-efbd7a27c6
description: "工具决策记录 e1_main_j2_batch_judge_7b.py E1·J2 主包盲判批处理·7B 升级版(Qwe"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-d383b76db6f8d813
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 e1_main_j2_batch_judge_7b.py
E1·J2 主包盲判批处理·7B 升级版(Qwen2.5-VL-7B bf16 · 判官升级程序首跑)。

升级纪律:判据/PROMPT/解析与 3B v4 定版逐字零改动(判据不因模型升级而变——只许更严);
改动仅三处:模型路径(/root/sysmodels 7B)、输出文件名(_7b 后缀防覆盖 3B 断点)、版本注记。

判读协议照《判官须知》:五组作答(完成度/执行质量/置信/正问/反问),直觉式
短判断,看不清→无法判断+低置信;独立作答。断点续跑(逐题落 jsonl,重跑跳过)。
输出 viewer 兼容 CSV(goldpack_J2.csv)。
材料: /root/runtime/e1_judge_pack/judge_pack/(blind_data.js + frames/)
产出: /root/runtime/e1_judge_pack/j2_answers.jsonl + goldpack_J2.csv
