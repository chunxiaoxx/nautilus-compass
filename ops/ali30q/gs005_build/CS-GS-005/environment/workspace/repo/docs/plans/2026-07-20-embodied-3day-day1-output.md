# 3 天飞轮 Day1 输出（单样板：`pilot_day3_core_v1`）

## 1) A/B/C/D/E 五视图统一数据契约（内外同源）

这版目的是让你对外和内部只讲一次数据，避免两套口径。

### 1.1 核心字段（任务级）

| 字段 | 类型 | 说明 |
|---|---|---|
| `pilot_task_id` | string | 任务唯一 ID，当前固定 `pilot_day3_core_v1` |
| `channel` | enum | `A` / `B` / `C` / `D` / `E` |
| `run_id` | string | 每次重跑序号，例如 `run-001` |
| `verdict` | enum | `pass` / `retry` / `reject` |
| `quality_gate_score` | number | `0~100` |
| `quality_flags` | array[string] | 可复用判定字段：`jerk_spike`、`frame_gap` 等 |
| `quality_delta` | object | 本 run 与上次 run 的评分差 |
| `owner` | string | 负责人 |
| `sample_time` | datetime | 样本采集开始时间 |
| `effective_seconds` | number | 有效时长 |
| `replay_link` | string | 回放链接（内部内部网 / 外部公开版脱敏页） |
| `ego_trace_hash` | string | 真实轨迹摘要哈希 |
| `ego_replay_match` | number | D 与 E 的一致率 |
| `notes` | string | 失败原因/规则修订点 |

### 1.2 统一派生指标（展示/复盘）

- `channel_pass_rate = pass_count / total_count`
- `repeat_consistency_rate = 重复 run 在同阈值下 pass 的比例`
- `ego_replay_match_rate = mean(ego_replay_match)`（按 sample）
- `failure_mode_top3`：7类失效模板频次前 3

### 1.3 任务级最小 JSON（可直接喂可视化页）

```json
{
  "pilot_task_id": "pilot_day3_core_v1",
  "channel": "A-E",
  "run_window": {
    "start": "2026-07-20T09:00:00+08:00",
    "end": "2026-07-20T23:30:00+08:00",
    "owner": "prime-001 / V5/FDE协同"
  },
  "runs": [
    {
      "run_id": "run-001",
      "verdict": "pass",
      "quality_gate_score": 100,
      "quality_flags": [],
      "model": "doubao-seed-2-0-pro-260215",
      "prompt": "v1",
      "latency_s": 45.5
    },
    {
      "run_id": "run-002",
      "verdict": "pass",
      "quality_gate_score": 100,
      "quality_flags": [],
      "model": "doubao-seed-2-0-pro-260215",
      "prompt": "v2生数据",
      "latency_s": 47.2
    }
  ],
  "kpis": {
    "pass_rate": 1.0,
    "repeat_consistency_rate": 1.0,
    "ego_replay_match_rate": 0.96
  },
  "summary": {
    "verdict": "pass",
    "failure_modes_top3": [],
    "rule_revision_candidates": [
      "优先补齐E先验字段回放链路；当前闭环数据结构已具备，不改阈值"
    ]
  }
}
```

## 2) 五视图标准化模板（内部/外部都用）

### A 视图（语义）
- 题面摘要（脱敏）
- 成功标准（3 条）：是否覆盖边界、是否完成动作、是否可复现
- 禁忌动作、边界条件

### B 视图（场景）
- 场景 ID、对象清单、初始位姿、扰动项（光照、遮挡、噪声）
- 数据来源标注（文件/版本）

### C 视图（模拟）
- 仿真参数（摩擦、重力、碰撞）
- Baseline 与现实偏差（抓取偏差、接触延迟、轨迹偏差）
- Gap log（可复验）

### D 视图（交互）
- 控制链路（采集端→API→调度端→策略端）
- 时延：p50/p95
- 可回放摘要（步骤级）
- 外部演示页面：给客户看动作完成率与一致性，不展现内部失败阈值

### E 视图（真实轨迹先验）
- `ego_trace_hash` + 采集设备标签（头戴/吊坠/手环）
- `ego_pose_delta`（映射误差）
- 与 D 的关键关键帧对齐度
- `ego_replay_match_rate`

## 3) D/E 对照讲稿（首版）

1. 开场 20 秒：我们不是在展示“更高参数”，而是展示“同一问题链路闭环一次完整可复核”的能力。  
2. 左侧 D：展示控制链路、动作成功率、时延。  
3. 右侧 E：展示先验轨迹映射、样本回放 hash、关键帧对齐。  
4. 下方统一证据栏：pass@5、failure top3、复跑一致率。  
5. CTA：是否进入下一基地试点（先做 1 条样板报价 + 你确认预算后继续）。

## 4) Day2 产出准备状态（用于 Day2 工单直接引用）

- `pilot_task_id`: `pilot_day3_core_v1`
- `pass@5`: `5/5`
- `failure_top3`: 空
- `quality_gate_score`: `100`
- `verdict`: `pass`
- `day1_to_day2`: 同源字段已接通



