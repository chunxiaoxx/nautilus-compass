# compass 下一任务 · 胶囊消费端接线(2026-08-22 立)

> 背景:Gate B 首次 Gold(c093f98)已产出 `capsule_candidate=true` 的经验,但
> `capsule_distilled` 恒为 False——candidate→capsule→注入 recall→下次会话生效,这段线没接。
> 这是"compass 自己吃狗粮变聪明"的最直接一步,不花钱、不依赖 A800。
> 战略对照:Ilya/SSI 押持续学习+value function;我们的 B/燃料 QC 是其上游供给,胶囊层=我们自己的持续学习最小实现(L1 级)。

## 任务
1. **Gold candidate → 胶囊生成**:Gate B report 里 `experience_candidate`(source episode + reuse_advice + suite 溯源)按 `gep/capsule_schema.py` 生成正式胶囊文件(带 provenance:grant/run_id/suite_hash/verify rc)。
2. **胶囊 → recall 注入**:胶囊落入 compass 记忆层可被 recall 命中的位置(session memory 或 capsule 库,按现有 capsule_schema 约定,不自造新格式)。
3. **生效验证(一步一证)**:新会话(或 dry-run recall)询问相关任务(如"读 UTF-8 配置文件要注意什么"),确认胶囊内容出现在召回结果;截图/输出贴回本文件。
4. **promotion 语义保持**:distill=真生成+真注入,promotion 其余位(policy/poi/source_write)仍 false,不越权。

## 红线
- 不改 Gold 判定逻辑;胶囊只能引用已 verify 的 Gold 证据,不得自封。
- c2e 那条 delta=0 的经验不得成胶囊(无 headroom,已判 Repair)。

## 关联
- memory: session-contract-gold-replication-20260822(并行推进)
- docs/DOGFOOD_BRIDGE.md(统筹接线,另一任务勿混)
