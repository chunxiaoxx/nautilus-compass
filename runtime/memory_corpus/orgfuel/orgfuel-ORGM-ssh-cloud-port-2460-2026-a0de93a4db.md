---
name: orgfuel-ORGM-ssh-cloud-port-2460-2026-a0de93a4db
description: "--- name: ssh-cloud-port-24860-20260930 description: "云服务器 S"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-ssh-cloud-port-2460-2026
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: ssh-cloud-port-24860-20260930
description: "云服务器 SSH 正确姿势——端口 24860 非 22,~/.ssh/config 有 Host cloud 别名(43.160.239.61+cloud_permanent 密钥),直连 `ssh cloud`"
metadata: 
  node_type: memory
  type: reference
  originSessionId: e01698b5-ca0c-4d79-8423-11cb0e107d82
  modified: 2026-09-30T03:29:48.432Z
fact_status: inferred
---

2026-09-30 用户纠正:云 daemon SSH 端口是 **24860 不是 22**。之前两次 `ssh -p 22 ubuntu@nautilus.social` 失败(第一次超时误判服务器抖动,第二次也是),浪费轮次。

**正解**:`~/.ssh/config` 已有现成别名——
```
Host cloud
    HostName 43.160.239.61 · Port 24860 · IdentityFile C:\Users\chunx\.ssh\cloud_permanent
```
直接 `ssh cloud '<命令>'` 即通。22 端口对该主机**从未开过**(超时≠抖动,是防火墙全拒)。

**How to apply**:任何云端 daemon/systemd/log/内存操作,一律 `ssh cloud`;不要再裸拼 `nautilus.social:22`。平台 HTTPS(nautilus.social 443)与 SSH(24860)是两条独立通道,HTTPS 200 不
