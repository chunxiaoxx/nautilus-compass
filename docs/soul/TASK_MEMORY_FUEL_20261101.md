# 任务立项:组织病灶→记忆产品能力(燃料转化+业界调研)

> 发起: 用户 2026-11-01 深夜令;执行: 新会话(立项会话 53 次 compact 移交,勿在本会话续做)
> 一句话: 把迁移+阿里 15 天的组织失败模式,转化为 compass/assay 的**可判据能力**,并对标业界开源,找到低成本高效率的最小实现路径。

## 一、核心洞察(用户定调)

迁移三机+阿里一期的教训不是成本,是**独家燃料**: 13GB 真实失败语料+复盘正本,业界没有第二家有这样完整的"AI agent 组织失败模式库"。痛点是业界普遍的(每家 agent 团队都会踩),我们的答案可以是产品——**把自己的坑变成判别人的题**(CS-xxx 快筛矩阵已是雏形)。

## 二、燃料坐标(已固化,勿再考古)

- **失败模式库**: `docs/soul/ORG_FOUR_Q_AUDIT_20261031.md` §二/§七审 8(静默失败三期同构)+ `docs/RETROSPECT_ORG_14D`(六病)+ 阿里终局复盘(nautilus-core/docs/CODESENSE_PHASE1_FINAL_RETRO_20261030,13 类组织模式)。
- **具体病例**: 判据转述链失真(1012 转述≠1027 正本)/自报绿 3 次被抓/部署旧版 3 连/tar 截断假绿/编码错位静默 recall 0/件数剧场(治理件版复发)/SSOT 漂移/compact 摘不掉注入地板/thrashing 两期对拍(Win 3/1315 vs Mac 6/325)。
- **已有判据雏形**: CS-xxx 快筛矩阵·判据锁+gate0·M5 三件套(fact_status/dedup_check/沿链一跳)·SSOT 副本一致性探针(7/17)。
- **记忆基建现状[实测 11/1]**: 原始层 13GB(全框 jsonl)/提炼层 compass 1100 条 .md 11MB/索引层 BGE-m3(PID 3652)/服务层 本框 hook+MCP 8097+daemon 9876;**lifecycle 设计未通电**(working→episodic→semantic→procedural+forget_at+decay,参数在 MCP 无执行器)。

## 三、调研清单(广泛搜索,开源为主)

- **记忆层开源**: mem0 · letta(MemGPT) · zep+graphiti · cognee · memobase · langmem · memos · a-mem · hindsight(已触客)。
- **学术**: Generative Agents(reflection) · MemoryBank(Ebbinghaus 衰减,与我们 lifecycle 同源) · HippoRAG。
- **平台自带**: Claude Code memory+auto-memory(自身即样本) · Cursor rules。
- **每家回答四问**: 机制一句话 / 怎么解决"遗忘"与"保真" / 局限 / 与我们重叠度+可借鉴件。

## 四、产出定义(判据,防件数剧场)

1. **深度分析文档**: 痛点→能力映射表(我们 N 类失败模式 × 业界方案对照 × 差异化定位),每行标证据层;
2. **调研报告**: ≥8 家开源逐家档案(上表四问),信息以官方 repo/文档为准防幻觉;
3. **≥2 个最小立项**进 ROADMAP 建轨,每个带: 预注册判据+成本估算(人日)+检验器;禁"分析完就完"的散文;
4. **对外叙事一段**: compass="记忆的验证机构"(arbitrate what agents remember)pitch 素材,供触客复用。

红线: 动手前先 grep 仓内旧实物(竞品终核/创世十家尽调已有底,别重造);结论标 [实测]/[推断]/[不可验];引用外部事件必核(前科: Zep 收购=幻觉)。

## 五、已有底账(直接复用)

- 创世十家尽调: memory genesis-ten-launched-20261015(EverOS/hindsight/mem0/letta/cognee 已投帖,48h 纪律);
- 竞品终核四项: memory competitor-final-audit-20260930;
- 判分两线定价: 判读免费+装订收费(memory judging-two-line-pricing-20261003)——记忆判别可挂同类预注册。

时间线建议: 新会话 1-2 个工作日出初稿,先分析映射表后调研(映射表是骨架)。

—— compass · 2026-11-01 · TASK-MEMORY-FUEL-20261101
