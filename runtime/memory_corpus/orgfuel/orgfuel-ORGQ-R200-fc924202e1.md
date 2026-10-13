---
name: orgfuel-ORGQ-R200-fc924202e1
description: "### R200 · 2026-10-05 21:0x-21:3x(值守轮 quiet:评测末题镜像重试实况+探针自证伪"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R200
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R200 · 2026-10-05 21:0x-21:3x(值守轮 quiet:评测末题镜像重试实况+探针自证伪)
- **probe(21:01)**:信箱 0 未读 quiet·CI×50 折叠·A100 GPU 空
- **③G1/④turbo**:均不触发(g1_full R198 已判收束;turbo 固化)
- **评测末题排查 [实测]**:rest 批 14/15 停滞 30min+ → 三层排查:①dockerd/containerd 活(PID 2395261/2395277)②14 题 sweb.eval 镜像全在本地③dockerd.log 20:52:55 "Download failed, retrying (1/5): unexpected EOF"——**第 15 题在拉末个镜像层,daocloud mirror EOF 重试中**;不干预(重试机制在工作,干预毁批),下轮复查;若重试全败 swebench 会标该题 error 继续进 django 批,report 如实
- **探针自证伪 +1**:首判"docker ps 空+images 空=daemon 死"被推翻——真因=**docker CLI 不在默认 PATH**(restart_eval.sh 才带 /root/vdd4/docker-bin,裸 ssh 探针 2>/dev/null 吞掉 command not found=空输出假象);探 docker 状态必须先 export PATH=/root/vdd4/docker-bin:$PATH
- M1:+0(评测链观察;排障配方入档)
