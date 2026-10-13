---
name: orgfuel-ORGD-4f1c3c95a1090f2a-d2899024b7
description: "[## 五、优化动作（六条，可执行）] | # | 动作 | 落点 | 省/赚 | |---|---|---|---| "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-4f1c3c95a1090f2a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 五、优化动作（六条，可执行）] | # | 动作 | 落点 | 省/赚 |
|---|---|---|---|
| A1 | **状态档三合一分工**：FRAME=对外快照（probe 自动刷新）/HANDOFF=交接（人写）/queue=日志（轮次自动） | scripts/frame_autosync.py | 每周省 ~10 轮同步性 docs commit |
| A2 | **远端操作工具化**：把 40 个 _rNN 脚本收敛为 `scripts/remote.py`（exec/put/get/launch 四命令，内置通道坑修复+限流退避） | scripts/remote.py | 每轮省 5-10min 重写+再踩坑 |
| A3 | **信箱分级**：trace 前缀过滤（writeback/ack 通知类→批量日报；判读/裁决类→逐封） | probe.py 已有基础 | 每周省 ~30 封逐封处置 |
| A4 | **GPU 空窗守门**：probe 增"空窗>1h→告警+终止建议" | probe.py | 省余额（128.20≈47h） |
| A5 | **周外部价值审计**例行化：每周复盘必答"本周外部请求/引用/付费增量"，M1 是唯一进度硬尺 | queue.md 周日轮 | 反剧场主尺不再靠想起 |
| A6 | **外发资产周节奏**：判例集/论文/协议每周至少一件外发动作（L5 冷外联是本周第一优先） | queue L5 | 把信用资产兑换成请求 |
