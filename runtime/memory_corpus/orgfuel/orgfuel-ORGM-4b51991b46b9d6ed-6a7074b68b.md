---
name: orgfuel-ORGM-4b51991b46b9d6ed-6a7074b68b
description: "记忆条目 ssh-cloud-port-2460-20260930.md 2026-09-30 用户纠正:云 daemo"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-4b51991b46b9d6ed
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 ssh-cloud-port-2460-20260930.md
2026-09-30 用户纠正:云 daemon SSH 端口是 **24860 不是 22**。之前两次 `ssh -p 22 ubuntu@nautilus.social` 失败(第一次超时误判服务器抖动,第二次也是),浪费轮次。

**正解**:`~/.ssh/config` 已有现成别名——
```
Host cloud
    HostName 43.160.239.61 · Port 24860 · IdentityFile C:\Users\chunx\.ssh\cloud_permanent
```
直接 `ssh cloud '<命令>'` 即通。22 端口对该主机**从未开过**(超时≠抖动,是防火墙全拒)。

**How to apply**:任何云端 daemon/systemd/log/内存操作,一律 `ssh cloud`;不要再裸拼 `nautilus.social:22`。平台 HTTPS(nautilus.social 443)与 SSH(24860)是两条独立通道,HTTPS 200 不代表 SSH 通,反之亦然。

[[daemon-9876-watchdog-rootcause-20260908]] [[gmail-verify-production-20260906]]
