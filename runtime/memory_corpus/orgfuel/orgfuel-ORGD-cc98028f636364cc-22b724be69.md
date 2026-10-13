---
name: orgfuel-ORGD-cc98028f636364cc-22b724be69
description: "[## 判分工序预注册(2026-10-05 R183 落,用户拍板"双臂跑完自动判分出 Round 1 读数")] -"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-cc98028f636364cc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 判分工序预注册(2026-10-05 R183 落,用户拍板"双臂跑完自动判分出 Round 1 读数")] - **判分环境**:A100 现役机复用(2026-10-05 R184 用户纠偏"没找对数据盘"后实测:vdd4 数据盘 98G 仅用 8%=87G 余,判死结论作废)。部署=static docker 27.3.1 全落 /root/vdd4(dockerd --data-root=/root/vdd4/docker-root,系统盘满不落盘)+swebench 5.0.2 venv@/root/vdd4+HF 走 hf-mirror;评测分两批(非 django 先/django 后)防镜像超容,每批评完立即 rmi;与双臂运行机(Windows 本机)物理分离=非实现者隔离落地件。环境件全 [实测](docker info/hello-world 拉取/dataset 500 rows)。
- **判分命令**(官方口径,零改):`python -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path preds_arm_{a,b}.json --run_id l3r1_{a,b} --max_workers 4`——predictions 由 collect_predictions.py 生成(idx→instance_id 对齐断言,A 臂 patch 取 trajectory.final_patch,B 臂取 patch.diff,缺件如实记 _note)。
- **resolved 定义**:官方 report 的 resolved 列(FAIL_TO_PASS 全过 且 PASS_TO_PASS
