---
name: orgfuel-ORGG-623edcb23ad0961f-bfecb5905c
description: "判读档判例 2026-06-20-compass-serving-semantic-recall · Task 0: 核"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-623edcb23ad0961f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-20-compass-serving-semantic-recall · Task 0: 核实部署拓扑 + daemon 协议(动手前必做·不写码)
## Task 0: 核实部署拓扑 + daemon 协议(动手前必做·不写码)

**为什么**:serving 与 daemon 可能不同机(serving cloud / daemon T4·靠 `compass-t4-tunnel`),`DAEMON_HOST` 默认 `127.0.0.1:9876` 需确认在 serving 所在机能解析到 daemon。

**Steps:**
1. 核 serving 运行真身:`ssh <serving-box> "systemctl cat compass.service | grep -E 'ExecStart|WorkingDir'; cat /proc/\$(pgrep -f compass_http)/cwd -L 2>/dev/null; curl -s localhost:<port>/healthz"` → 记版本号 + CWD + 端口。
2. 核 daemon 真身:T4 `43.166.8.20` `compass-daemon.service`(6/20 瘦身后 PID·:9876)。确认从 serving box 能 `nc -z <DAEMON_HOST>`(隧道通)。
3. 读 daemon 现有 recall action 协议(`daemon.py` `_handle`/请求分发):确认 JSON 行协议 `{"action":...}` → `{"ok":...}`,记 socket 读写格式(换行分帧)。
4. 产出:在本 plan 末尾追加「拓扑实测」小节(serving box / daemon host /
