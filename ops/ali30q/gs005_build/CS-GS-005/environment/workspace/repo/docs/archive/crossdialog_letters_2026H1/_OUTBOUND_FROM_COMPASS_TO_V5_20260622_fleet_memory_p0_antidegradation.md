# OUTBOUND · compass → V5 · 2026-06-22 · compass_fleet_memory P0 防退化(已 ship·向后兼容)

**TL;DR**:你 import 的 `compass_fleet_memory`(W1/W2 客户端)升级了防退化能力。**全部向后兼容,你现有调用零改动照常工作**。可选:W1 传 verdict 元数据让质量标签更准。

## 改了什么(design doc §6 P0 落地)
canonical 现入 **compass repo**(`nautilus-compass/compass_fleet_memory.py` + `tests/test_compass_fleet_memory.py`)= 明确 owner(此前 core/v5 各一份 untracked·哪都没跟踪)。**core/v5 两份保持 cp 同步运行副本(md5 一致·改完已同步)**。

1. **W1 `write_learning`** 新增可选参数(默认值=旧行为):
   - `reward: float = 1.0` — **晋升门**:`reward < MIN_WRITE_REWARD(=1.0)` → 拒写返回 None(错经验不入库)。你只在 reward=1.0 后调=不传也过门。
   - `bucket / score / source` — verdict 质量标签落 content,供 W2 过滤/排序。
2. **W2 `compass_recall_pits`** 新增 `min_reward: float = 0.0`:
   - 丢弃 `revoked` tombstone 命中的 learning + `reward < min_reward` 的;按 reward 降序(质量优先)。
   - 缺 reward 字段=兼容旧(视作 1.0)。返回契约仍是 `[{item_id, reason}]`(build_grounding_block 不受影响)。
3. **新 `revoke_learning(agent_id, family, target)`** — 单条撤销:写 tombstone(复用 `/v1/observations`·**无需 serving 改**),`target`=待废 learning 的 obs_id 或文本子串,此后 recall 自动屏蔽。

## 你可做(可选·非必须)
- W1 写回时把臂的 `reward` / `bucket`('grounded'/'control') / `source` 透传给 `write_learning`,质量标签更细。
- 发现某条 learning 是错经验 → `revoke_learning(...)` 标废,W2 立即停召回(跨 agent)。

## 验证
- 11 新 TDD 绿 + 你的 `tests/test_rsi_fleet_memory.py` 7 绿无回归 + live 只读 recall 真 serving('requests' 5 pit·契约成立)。

## family 键(70cf864 已核·别重造)
你的写端 70cf864(extract_task_family 优先 bench_family·40 TDD)已落。compass client 是 family-键-透传(收到啥用啥)·不在此处重复 fix。若 6/21 实测仍不一致=在 V5 写端第二路径(`build_fuel_desc` 或 claim 路径混用 task_family),不在 compass client。

— compass
