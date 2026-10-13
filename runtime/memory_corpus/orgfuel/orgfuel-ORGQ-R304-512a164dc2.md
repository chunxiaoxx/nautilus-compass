---
name: orgfuel-ORGQ-R304-512a164dc2
description: "### R304 · 2026-10-07 深夜(GPU 嵌入切换完成✅——daemon 过载根治,全链实测闭环) - "
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R304
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R304 · 2026-10-07 深夜(GPU 嵌入切换完成✅——daemon 过载根治,全链实测闭环)
- **切换全链落地**:①A100 ed25519 密钥→cloud authorized_keys 授权②反向隧道守护(A100 tunnel_daemon.sh:nohup while 循环,断线 30s 重连,ServerAlive 10s×3 快检测)③隧道端口 19987(首用 19986 被僵死 sshd 占住→整体换口,坑:ssh -R 半死不退出时 bind 冲突)④daemon v3.3.5 补丁(_BGEWrapper.encode 走 COMPASS_EMBED_PROXY,失败回退本地;超时 8s 快回退)⑤systemd drop-in 指向 19987⑥重启。
- **判定[实测]**:fails 110→110 零新增(GPU 代理承接全部嵌入);**overload 199858→199858 零新增**(60s 窗,此前 +60~1000/10min);**CPU 100%→10.5%**(嵌入计算全卸载 A100);ping 正常。两天过载问题根治。
- 运维注记:隧道守护不抗 A100 重启(reboot 后需重跑 tunnel_daemon.sh);cloud 旧 19986 僵死监听会自然消亡;embed_server.py 与隧道均已 nohup 常驻。
