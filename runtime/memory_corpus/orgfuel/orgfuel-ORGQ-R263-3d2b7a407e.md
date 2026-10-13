---
name: orgfuel-ORGQ-R263-3d2b7a407e
description: "### R263 · 2026-10-06 晚(loop:cloud daemon v3.3.3 根修——"无用功风暴""
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R263
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R263 · 2026-10-06 晚(loop:cloud daemon v3.3.3 根修——"无用功风暴")
- probe 第六源骤升 +217/轮 → py-spy 现场取证:**R256"socket 泄漏"系误诊**。真根因链=CPU 跑 bge-m3 前向太慢 × 客户端超时重试风暴 → 32 槽全被"客户端已 FIN 仍在白算"的僵尸请求占满 → accept 全 overload reject → 排队连接 CLOSE-WAIT 稳态堆积(handler 从未执行,非 close 缺失)。旁证:worker 15 线程全闲时 CLOSE-WAIT 28、CPU 99.7% 单线程烧 3.5h、16:54 后 3h 无一请求完成。
- **修(daemon_v33.py v3.3.3,远端 sha 前 backup daemon_v33.py.bak_20261006_r263)**:A) `_safe_handle` 开工前 MSG_PEEK 探活——客户端已 FIN 直接跳过计算(close+release sem);B) chunk fusion cosine 数组 guard(批量 emb 返回向量致 numpy 布尔歧义)。patch 脚本=runtime/loop/_cloud_daemon_v333_patch.py(bytes 级·LF/CRLF 双变体幂等——**该文件混行尾,LF 锚必 miss**)。
- **验收[实测]**:systemd restart 20:16:44(pid 3908968)→ ping 通;overload 计数 195369 停涨(重启后 5min 零新增);P9 cache 行恢复(请求重新完成);CLOSE-WAIT 28→16 稳住。
- **残留记档**:① fusion fail 异常仍
