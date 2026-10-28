# 沉淀承载面地基 V1(2026-10-04 · 平台先行设计,待两框提案定稿接线)

> 承用户 2026-10-04 定调(两大体系沉淀);v5 已交 TSI v1 骨架(shared specs/ 777ea162),
> 三缺口(基准注册表/轮次台账/承载面)10/6 前补。本文=平台侧承载面地基预设计,
> 提案到即按此接线;字段以提案定稿为准,本文是草案不是正本。

## 一、registry 台账(承载选项 C 的实体设计)

### 1. trainings.json(轮次台账——TSI 六环之"燃烧室+动力计量"台账化)

每轮一条,git 溯源,触发器=每训练轮判读回流时写一次:

```json
{
  "round": "r78",
  "date": "2026-10-05",
  "fuel": {"pool_snapshot_sha": "...", "trajectory_count": 50, "source": "f041-f060+v5自跑"},
  "recipe": {"ref": "v5仓路径@commit", "method": "GRPO/LoRA-7b-qlora", "params_hash": "..."},
  "criteria_version": "v2-final(T1全量100集/窗,T2主配对Wilcoxon)",
  "preregistration": {"hash": "...", "committed_at": "...", "doc_ref": "..."},
  "eval": {"canary": "GREEN/RED", "canary_trend": "...", "full": "753 win_rate=..."},
  "verdict_ref": "verdicts trace(writeback:...)",
  "negative_result": false,
  "owner": "v5"
}
```

### 2. benchmarks.json(基准注册表——"每轮用什么尺子量的"可查)

```json
{
  "benchmark_id": "pusht-frame-v2",
  "criteria_version": "v2-final",
  "preregistered_hash": "...",
  "heldout_ref": {"coord": "URL/sha", "intersection_with_training": "0(机器验)"},
  "history": [{"round": "r76", "result_ref": "..."}, {"round": "r77", "...": "..."}],
  "custodian": "compass(判读主权)"
}
```

compass 侧同构:judging_pipelines.json(P3 后训练管线台账:燃料白名单快照/训练轮/护栏检查/上线判读引用)+ memory_io.json(记忆 IO 正本元数据:输入源/分级/时效/淘汰策略版本)。

## 二、org_state 端点扩展(承载选项 B)

沿 frames/rulings/verdicts 同款零新表模式(每请求读文件):

- GET /api/platform/org/trainings?limit=50 —— 轮次台账
- GET /api/platform/org/benchmarks —— 基准注册表
- 消费方预注册:值守轮(状态盘点)/周报 digest/外部判官材料引用(招募稿可链"我们的判据史")

## 三、网站沉淀区信息架构(承载选项 A)

nautilus.social 新区(与 posts 社区并列),四个视图:

1. **训练管线**(v5 涡轮增压):六环图(TSI 指标实时)+轮次时间线(每轮可点开:燃料/配方/判据/结果,负结果同权展示)
2. **判读与记忆**(compass):判例集(CASEBOOK 链接)/verdict 索引/记忆 IO 架构图
3. **基准注册表**:每把尺子的注册页(判据版本/held-out/历史对照)
4. **判读回流(EGR)**:缺口报告→定向单的闭环展示

前置依赖:v5 posts 渲染层双库缺陷修复(已三催)——同一 8001 服务,修好 posts 即具备新区渲染地基。

## 四、接线时序

1. v5/compass 提案到(10/6)→字段定稿→registry JSON 落地(首批数据手填 r76/r77 历史)
2. 端点开发+TDD(预计半天)
3. 网站新区(依赖 posts 修复,公开面上线前呈用户一步)
4. 消费方接线:周报 digest 引用 trainings 端点;招募材料链基准注册表
