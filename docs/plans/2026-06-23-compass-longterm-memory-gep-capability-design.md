# compass 能力跃迁设计 · 真正长期记忆 + GEP 全面 + OKF/LLM-WIKI2 + 主助推 RSI

> 日期 2026-06-23 · 状态 DESIGN(brainstorming 产出·待 writing-plans)
> 目标(用户): 让 compass 从"扁平 bge-m3 语义召回库"跃迁为 **真正的活长期记忆 + 全面 GEP 进化 + 主动助推 RSI**,涵盖 OKF(对外互操作)与 LLM-WIKI2(长期记忆知识格式)。
> R3 诚实: 本 doc 是设计;真 build/部署留 fresh session。代码大量已存(见现状盘点),核心是**接通+部署+补全**,非从零造(anchor#5)。

## 0. 现状盘点(grounded · build/test/deploy 三态)
| 能力件 | 代码 | 测试 | 部署/运行 | 证据 |
|---|---|---|---|---|
| bge-m3 语义召回 | ✅ | ✅ | ✅ LIVE | 本 session live recall ok:true |
| ⑤记忆并库桥(split-brain) | ✅ | 14 TDD | ✅ LIVE(`compass-fleet-capsule.timer` 15min·11min前成功) | slice1 |
| W1 晋升门/W2 召回/revoke | ✅ | ✅ | ✅ LIVE | 6/22 ship |
| **LLM-WIKI2 fuse · 4-tier 生命周期**(`recall.promote_lifecycle_tier`·working/episodic/semantic/procedural + Ebbinghaus decay + forget_at) | ✅ | ✅ 8 测(`test_lifecycle_fuse`) | ❌ **没 driver 在跑** | spec `paper/LLM_WIKI2_FUSE_DESIGN.md` |
| **tier_promotion_driver**(批量驱动晋升) | ✅ | ✅(`test_tier_promotion_driver`) | ❌ **不在 cloud** | SSH `No such file` |
| **L2 dream-layer 蒸馏**(`storage/l2_distiller`·nightly·Ollama 可选 $0·跨 L1 组压缩) | ✅ | ✅ | ❌ **没 timer·不在 cloud** | SSH |
| **OKF**(exporter/validator·memory→OKF bundle·厂商中立) | ✅(v2.3.0 分支) | ✅ round-trip | ❌ 没部署·无消费者 | cloud 无 okf/ 目录 |
| **GEP**(P1/P2 capsule_schema 预备态·P3 poi_rerank) | 🟡 部分 | 部分 | ❌ 没部署 | cloud 无 gep/ 目录 |
> 🔴 关键结论:**长期记忆的机器(LLM-WIKI2 4-tier fuse 逻辑 + driver + L2 蒸馏)全有代码全测过,但没有任何进程在线上驱动它** → 记忆写了 tier/decay/promote 字段却永不晋升/衰减/蒸馏 = **当前是扁平召回库,不是活的分层长期记忆**。OKF/GEP 同样 code-存在-未部署。代码位于 `feat/v2.3.0-release` 分支。

## 1. 三相程序(排序 = 价值/风险/依赖)

### Phase 1 · 真正长期记忆上线(LLM-WIKI2 fuse 实运行 · 最高 ROI · anchor#5-clean)
把已有但没跑的生命周期机器接通+部署,让记忆真正"活"起来:
- **tier 晋升 driver 部署**:周期跑 `tier_promotion_driver`(复用 `recall.promote_lifecycle_tier`)over 真实记忆库 → 高 reinforce_count/过 promote_after 的胶囊 working→episodic→semantic→procedural 晋升;过 forget_at 的归档。挂 `compass-tier-promotion.timer`(类比 fleet-capsule timer)。
- **Ebbinghaus decay 执行**:衰减未访问胶囊的 salience;reinforce_count 在每次 recall 命中时 +1(回灌 access event)→ 真正"用进废退"。
- **L2 dream-layer 蒸馏部署**:`l2_distiller` nightly(Ollama qwen2.5:7b 可选·缺则确定性 extractive)跨 L1 组压缩成 L2 摘要 → 长期记忆密度↑、冷查↓。挂 `compass-l2-distill.timer`(nightly)。
- **recall 接生命周期**:召回排序加 tier 权重(procedural/semantic 优先)+ 命中即 reinforce(闭合 access→promote 回路)。
- **验证(verification-before-completion)**:① 跑 driver 后 DB/文件实测有胶囊真升 tier ② L2 timer 产出 `_l2` 摘要 ③ recall 命中后 reinforce_count 真 +1 ④ 冷查延迟不退化。
- 依赖:最少(代码全在·只缺部署+wire)。**= 用户"真正长期记忆"的直接实现。**

### Phase 2 · OKF + GEP 全面实现(格式互操作 + 进化/质量自然选择)
- **OKF 接通**:部署 `okf/exporter`(memory→OKF bundle·type 提升+wikilink 有向图+cited-by)+ validator。给一个真消费者(对外 MCP 资源端点 / landing 导出)——否则仍是无人用的工具。**= 厂商中立对外互操作·咬 compass 对外引流核心。**
- **GEP 全面**(接 architecture-fusion 设计 `2026-06-23-architecture-fusion-design.md`):
  - OKF 技能图依赖边:胶囊声明 `depends_on` 接进 link graph → 召回从单条语义升级到**技能组合检索**。
  - 复用复利加权:召回排序 = verifier 成功率 × reuse_count × **难度确认门**(防饱和易题正反馈·复用 `run_doubao_pass_at_k`)。
  - 两阶治理门 + quarantine:reward gate(已有 W1)+ 同 family canonical 逻辑矛盾检查 → 冲突进隔离区(防 cross-agent 投毒·2026 已现 6487 恶意 skill)。
  - 负样本 forbidden_pattern 胶囊:失败轨迹→避坑胶囊→召回负向注入(接住"扔掉最便宜高信号料")。
  - 写共享泛化变换:晋升 cross_agent 前剥离任务特定常量、只留模式。
- 复用 `gep/`(P1/P2 schema·P3 rerank)+ `okf/`——接通+补全,不重造。

### Phase 3 · 耦合架构主助推 RSI(从被动召回→主动助推器)
- W2 召回喂飞轮时:优先返高 tier + 复用复利排序 → 更准 peer learning。
- forbidden_pattern 负向注入 → producer 避坑。
- L2 蒸馏胶囊 → 喂 soul 蒸馏燃料(一鱼两吃:长期记忆压缩物同时是蒸馏料)。
- 🔒 与 RSI 闭环耦合的放大效应 gated on 北极星"证一次 uplift"(见 `canonical_rsi_fde_flywheel_consolidation_and_organic_coupling_20260623`)·但 Phase 3 的接口设计现在可定。

## 2. 架构 / 数据流
```
ingest_obs(带 tier/decay/promote_after/depends_on)
  → 文件语义库(Store B·BGE 索引)
  ←── ⑤桥 ── 飞轮 sqlite learning(Store A·已 LIVE)
  ↓ Phase1 生命周期(周期 driver + nightly L2):晋升/衰减/归档/蒸馏
  ↓ Phase2 GEP:技能图依赖边 + 复用复利 + 治理门 + 负样本
recall(tier 加权 + 复用复利 + 命中 reinforce)→ ⑥ W2 喂飞轮(Phase3 主助推)
```

## 3. 测试 / 错误处理
- 全程 TDD(已有 `test_lifecycle_fuse`/`test_tier_promotion_driver`/`test_l2_distiller`/`okf/test_*`/`gep` 测可复用扩展)。
- L2 蒸馏 Ollama 不可用 → 确定性 extractive fallback(已设计·never on ingest path)。
- 部署每件挂 timer 后 verification-before-completion 实测(driver 真升 tier / L2 真产摘要 / recall reinforce 真 +1)。
- 治理门防 poisoning;tier 误升/误归档 → 可逆(归档=mv 非删·参 cycle archive 先例)。

## 4. 开放问题(待 writing-plans / fresh session)
1. tier-promotion driver 跑在 cloud 还是 T4(daemon 读 T4·参 ⑤桥 rsync 拓扑)?
2. L2 蒸馏 Ollama 在哪个盒(GPU 抢占?$0 但要 qwen2.5:7b)?缺则 extractive。
3. OKF 真消费者是谁(对外 MCP resource / landing 导出)——没消费者 = 又一个 unwired 件。
4. GEP 复用复利的难度门数据源(doubao 实测·成本)。
5. 与 v2.3.0 分支的关系:这些代码在 feat/v2.3.0-release,Phase 1 部署是否顺带把 v2.3.0 合入 main(收口)?

关联 [[canonical_rsi_fde_flywheel_consolidation_and_organic_coupling_20260623]] · `docs/plans/2026-06-23-architecture-fusion-design.md` · `paper/LLM_WIKI2_FUSE_DESIGN.md`
