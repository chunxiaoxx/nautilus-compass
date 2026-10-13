---
name: orgfuel-ORGM-b7a7ef20ae3beecb-dd6cd9a249
description: "记忆条目 daemon-v33-switch-20261001.md # 云 daemon v3.3 蓝绿切换成功(20"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-b7a7ef20ae3beecb
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 daemon-v33-switch-20261001.md
# 云 daemon v3.3 蓝绿切换成功(2026-10-01)

## 根因定谳(v3.2 为何云端不达标)

v3.2「刀 A numpy 化」只覆盖 **encode 出口**(新向量)+cosine 单向量临时转换——**存量 pkl 的 PyList 从未被整体转换**,warmup/惰性载入时原样驻留。实测坐实:cache 有 **999MB 单体 pkl**(c096d6883da3),PyList 载入膨胀 2-3x=2G 差额全部来源。本地合成压测 175MB 之所以测不出:压测数据是新造的(走 encode 出口=已 np),没模拟存量 pkl。

## v3.3 三修(runtime/cloud_daemon_v33_20261001.py)

1. `_npify_cache()`:warmup+惰性两个载入点整体转 np.float32;转换后下次 flush 落盘即 np,永久免转
2. 巨 pkl 跳过 warmup(>200MB → lazy);999MB 巨物治理另挂账(身份待查)
3. systemd unit ExecStart 改指 daemon_v33.py(bak 备份 .bak-v31)

读数:蓝 RSS 2507MB(vs v3.2 同配置 5326,降 2.8G);9876 切换后 systemd 管理。

## 云端部署五坑(9/30-10/1 实战)

1. systemctl 要 `sudo -n`(ssh 非交互 polkit 拒)
2. **9877 被 mcp_server.py 长期占用**(9/15 起)——蓝端口用 9878
3. **stop 挡不住拉回**:Restart=always+云端 watchdog 双机制会 star
