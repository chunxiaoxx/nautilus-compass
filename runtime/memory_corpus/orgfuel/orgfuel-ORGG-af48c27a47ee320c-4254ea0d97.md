---
name: orgfuel-ORGG-af48c27a47ee320c-4254ea0d97
description: "判读档判例 2026-06-20-compass-serving-semantic-recall · Task 5: 协"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-af48c27a47ee320c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-20-compass-serving-semantic-recall · Task 5: 协调部署 + 真证据验证
## Task 5: 协调部署 + 真证据验证

**前提**:Task 0 拓扑已核实。部署 = daemon(加 score action)+ serving(recall 改)双端,**重启会让 recall 短暂离线**(影响所有框)→ 协调窗口(参考 6/20 daemon 瘦身部署:ping soul/V5·MCP 桥 v1.8 自动重连兜底)。

**Steps:**
1. 备份 box 双端文件(`.bak.<date>`)。
2. scp daemon.py → daemon box(同版本核对·**先归一化 CRLF 再 diff 防假分叉**·6/20 踩过)→ restart `compass-daemon.service`。
3. scp compass_http_v09.py → serving box → restart serving service。
4. **验证(真证据·非 systemctl-active)**:
   - daemon:发 `score` 请求 socket 实测返 scores。
   - serving:curl `/v1/recall?cross_agent=true&q=...` 返 `ranker:bge-m3` + 合理排序。
   - 回归:普通 recall/drift 仍正常;nvidia-smi daemon 显存未暴涨。
   - 端到端:Task 4 的 A 写→B 语义召回 在生产/staging 复现。
5. 收尾 memory:登记部署态 + box-vs-repo 对账(systemd/代码)+ ranker 切换实证。

---
