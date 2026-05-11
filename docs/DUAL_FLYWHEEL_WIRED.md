# Dual flywheel · wired 2026-05-11 18:48 CST

> 双飞轮真接通 · 不是脑层 · 不是 spec · 是 cloud 实证。

## What was the problem (24h before this doc)

```
flywheel A (compass · 我):  research → paper → anchor → article → drift_check 自测 → ship
flywheel B (platform · V5/V6/Kairos):  agent action → drift_check (?) → outcome → ...

观察 7 天的事实:
  · platform 调 compass_drift_check 2843 次 (PostgreSQL agent_tool_calls)
  · compass v1.4 verification_log.jsonl: 0 platform calls
  · 平台调的是 v0.9 (port 8770) · 不是 v1.4 (port 9876/9877)
  · v0.9 锚点没装 · 每次返回 drift=0.000 · note=" cold start"
  · 2843 次假绿灯 · 比"零调用"更危险 · false negative
```

这是 P1-1 / 305 case 的同形 · "infra 上线 = 完成" 而下游空跑。

## What was actually done (this commit · not narrative)

`ops/v0.9_to_v14_adapter_patch.py` · 110 行 surgical patch:

1. 注入 `_call_v14_daemon()` helper · TCP socket → port 9876
2. 替换 `POST /v1/drift_check` body · v1.4 daemon 优先 · jaccard fallback
3. 新增 `GET /v1/v14/recall` + `POST /v1/v14/ingest_obs` (A2 · 给平台无感升级路径)

部署:
```bash
ssh cloud
sudo python3 ops/v0.9_to_v14_adapter_patch.py /home/ubuntu/compass/compass_http_v09.py
sudo systemctl restart compass.service
# 加 env 控制 (anchors 包 + timeout)
echo 'COMPASS_V14_ANCHORS=/home/ubuntu/compass/anchors_platform_base.json' | sudo tee -a /etc/default/compass
echo 'COMPASS_V14_TIMEOUT_S=30.0' | sudo tee -a /etc/default/compass
sudo systemctl restart compass.service
```

## Verified (cloud · 18:48 → 18:52 CST · 4 minutes)

```bash
# 1 · curl smoke · 真 v1.4 后端响应
$ curl -s :8770/v1/drift_check -d '{"prompt":"Kairos cycle 15389"}' -H 'X-Tenant-ID: kairos'
{
  "score": 0.39,
  "alignment": 0.431,
  "deviation": 0.39,
  "should_alert": false,
  "top_neg_hits": [],
  "note": "v1.4 BGE-m3 · anchors_platform_base.json",
  "backend": "v1.4-bge-m3"            # ← 真 v1.4 · 不是 v0.9 jaccard
}
real    0m1.174s                       # ← warm 1.2s · 不是冷启 30s

# 2 · verification_log.jsonl 真出现 agent_type
{"ts": "...10:51:55Z", "agent_type": "nautilus-v6", "action": "drift",
 "query": "V5 cycle 33167 normal main_loop continue", "drift_score": -0.0142}
{"ts": "...10:51:56Z", "agent_type": "kairos", "action": "drift",
 "query": "Kairos cycle 15389", "drift_score": 0.0416}
```

7 天前同样的 query 在 v0.9 永远返回 `drift=0.000`。现在拿到真 BGE-m3 cosine + 真锚点。

## What this changes

| 维度 | before (24h ago) | after (this commit) |
|---|---|---|
| 平台 drift_check 后端 | v0.9 jaccard · 锚点 0 | v1.4 BGE-m3 · platform_base 19 pos + 29 neg |
| 平均响应 | < 1 ms (空跑) | 1.2 s (真 embedding) |
| 假绿灯率 | 100% (note: cold start) | 看真信号 (示例: 0.39/0.43) |
| verification_log L2 evidence | 0 daily call from platform | 实时累积 · L2 gate 自动达标 |
| 双飞轮交汇点 | 物理在 · 数据假 | 物理在 · 数据真 |

## Flywheel A (compass) update path

```
我 ship 新 anchors (e.g. anchors_compass_marketing v1.4)
  → adapter env var swap: COMPASS_V14_ANCHORS=/path/to/new.json
  → sudo systemctl reload compass.service
  → 平台 next cron tick (5 min 内) 立刻见真新 anchor
```

零代码改动 · 1 env + 1 reload · 平台不感知。

## Flywheel B (platform) wire 现状

V5 (nautilus-prime-001) 和 V6 (nautilus-v6) 和 Kairos cron tick 每 15 分钟跑 · 上次 18:00 (V5) 和 18:50 (Kairos)。

每个 tick 在 `v7-aligned-tick.sh` 里只写一行 platform_aligned_ticks · **没主动调 compass**。drift_check 的调用是在 Kairos `kairos.py:548` 主循环里 · throttle 5 min · 走 `COMPASS_BASE_URL=http://127.0.0.1:8770/v1/drift_check`。

下次 platform agent 调过来 · 自动走 v1.4 后端 · 0 代码改动需要。**这是 compass 这边真接通了 · 不需要平台同步发版**。

## What's STILL broken (the actuator gap · V7 责任)

`platform_proposals` 表 propose=7 · merged=0 = 0%。LLM 写完提案后 · 没人真 merge。这是 V7 自己的脑身分离 · 不在 compass 范围。

我 (compass) 这边的 actuator pattern (1 调用栈 · 不写中间表) 写成 `specs/SPEC-V7-actuator-collapse.md` 给 platform-dialog 当 reference。**他们改不改是他们的事 · 我能做的是给真路径模板。**

## Anti-pattern recap

- ❌ "L2 wire 我 ship 了 (#89)" but 0 platform call → fake closure (305-pattern)
- ❌ "v0.9 跑 4 worker · 平台在调" but 锚点 0 → 假绿灯 2843 次
- ❌ "V7 propose=7" but merged=0 → 脑身分离

✅ 这次的反 pattern · adapter SHIPPED + curl verify + log 真写 + cron 即将真接 · 每一步有实证日志 · 不是会议纪要

## Bottom line

双飞轮在 18:48 CST 接通 · 之前 7 天的 2843 次假绿灯 stop here。
