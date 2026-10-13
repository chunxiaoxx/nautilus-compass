---
name: orgfuel-ORGQ-R184-b640c410fd
description: "### R184 · 2026-10-05 15:5x-16:0x(用户纠偏:判分环境复用 A100 数据盘——管道全链"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R184
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R184 · 2026-10-05 15:5x-16:0x(用户纠偏:判分环境复用 A100 数据盘——管道全链就绪)
- **用户纠偏"没找对数据盘"**:此前只 df 系统盘(196G 100% 满)判死=探针盲区;全量 df 复测 **vdd4 数据盘 98G 仅用 8%(87G 余)+vdd3 余 63G**——租机方案作废,复用 A100 ¥0
- **判分环境落成(全 [实测])**:static docker 27.3.1 全落 /root/vdd4(dockerd --data-root=vdd4/docker-root,系统盘满零触碰;三坑:userland-proxy-path 显式指定/containerd 须 PATH 带入/SSH banner 限流退避 120s)→docker info+hello-world 拉取过;swebench 5.0.2 venv@/root/vdd4(pip 走 tuna);HF Verified 500 rows 经 hf-mirror 拉通;eval_runner.py 上传(分批 rest→django 防镜像超容+批后 rmi+report 回显,COMPILE-OK)
- **判分触发序(跑完自动)**:双臂进程退出+30 题产物齐→collect_predictions.py(collector session_id 过滤)→sftp preds→nohup eval_runner 双臂→report 合并→抽查 6 题/臂→Round 1 读数回传
- 双臂进度 [实测]:A 5/30(~5min/题,预计 ~18:10 完);B task_5(~9min/题,预计 ~19:30 完,B 为瓶颈)
- M1:+0(判分读数供给前置件全就绪)
