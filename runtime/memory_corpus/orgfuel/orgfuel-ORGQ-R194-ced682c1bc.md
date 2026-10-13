---
name: orgfuel-ORGQ-R194-ced682c1bc
description: "### R194 · 2026-10-05 19:0x(推进轮:dockerhub 直连拉镜像卡死→daocloud m"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R194
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R194 · 2026-10-05 19:0x(推进轮:dockerhub 直连拉镜像卡死→daocloud mirror 修复,评测正式健康)
- **诊断链 [实测]**:A 臂评测 20min 0 容器 0 完成(磁盘+5.8G=layer 在拉但极慢,dockerhub 直连国内不通畅)→决定配 mirror 重启;首杀不净(旧 containerd 残留→新 dockerd "timeout waiting for containerd"半死)→**restart_eval.sh 脚本化**:杀净(dockerd/containerd/shim 两轮 pkill+9)→带 --registry-mirror https://docker.m.daocloud.io 重启→**验证循环(docker info OK 才继续,修上轮"daemon 未就绪即重跑评测秒退"时序错)**→评测重跑
- **修复后健康 [实测]**:DOCKER-READY+mirror 生效;首个实例 **pylint-4661 1 ran successfully, 0 failed**(镜像 2.82GB 拉+测试跑通,~4min/题);rest 批 15 题预计 ~1h,后接 django 批
- **B 臂 [实测]**:task_27 完成(28 目录剩 2 题在跑);B 模式稳定:几乎全 LimitsExceeded@50(patch 时有时无)
- M1:+0(判分链推进)
