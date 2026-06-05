# /goal 起手包 · compass 双轮接线闭环(fresh session 入口 · 2026-06-05)

> 复制下方「/goal verbatim」段到 fresh session。本文件是详情底本。设计=`docs/plans/2026-06-05-fde-rsi-dual-flywheel-closure-design.md`,计划=`...closure.md`,诊断 memory=`session_20260605_compass_dual_flywheel_diagnosis_design.md`。

## /goal verbatim(粘这段)

```
/goal compass-dual-flywheel-wiring

【北极星·不变】平台 agent-first 生态;FDE+RSI 双轮;耦合/自训按外部信号(批次被字节接收 + checklist 通过率)解锁,不先建当卖点(anchor #2/#3)。

【总判定·本 goal 根据】compass 不缺能力,缺"接线 + 外部 ground truth"。6 能力 5 项建好但没接生产热路径/默认关,唯 metamemory 真生产 live。平台 RSI benchmark 三连负已证伪内部自评 → 外部 ground truth(专家复核+字节接收)是双轮唯一燃料。本 goal = 把已建能力接到生产 + 新建专家→ground truth 回路。详见 docs/plans/2026-06-05-fde-rsi-dual-flywheel-closure-design.md。

【lane·compass own·不碰别框 turf】检索/记忆生产接线 + FDE verdict→PoI adapter + 专家复核回路。不碰平台内部 RSI wiring(平台 held until 正信号)。soul own RUBRIC/checklist_scorer;v5 own copilot/keystone。

【凭据·已备·读这个·值不回显】C:\Users\chunx\.claude\.cache\.fde_api_secrets.env(MiniMax/Serper/Brave/Firecrawl/GoogleSA/飞书 App)。

【可验证终态·全满足=done】
  T1 缺口2 检索栈进生产(最高价值·解"长期记忆"):reranker(bge-reranker-v2-m3 本地交叉编码器·非LLM)接进生产 daemon recall 热路径(COMPASS_PROD_RERANK 开关)+ 加载失败降级不破 recall + benchmark 在【生产路径】实测 P@5 ≥0.90(vs 裸 bge-m3 0.86)。query-rewrite/lifecycle 同模式跟进(rewrite 若用 LLM 则 opt-in 守黑盒)。每步 TDD red→green。
  T2 缺口1 跨设备 ingest 修:先云端实测证实 /v1/v14/ingest_obs 是否静默失败(ingest_obs+content vs daemon ingest+text @daemon.py:1092)→ 对齐 action/字段 → 云端 POST→recall 召回得到。证实不存在则跳过+记差异。
  T3 缺口3 FDE verdict→PoI adapter:soul checklist 通过率+专家复核结论→compass.poi_credit(复用 proof/poi_credit_store.py)+ 云端 COMPASS_CLOUD_POI_BOOST=1 + mock verdict→credit→boost 验。真数据待 soul verdict 流(G-verdict)。
  T4 缺口4 专家复核回路:feishu_client 读复核工作台 Bitable(通过/打回+理由+分项分)→结构化→双喂(a)T3 PoI (b)T3胶囊管线(复核理由=避坑知识)。mock 端到端跑通;真飞书数据待真批次(G-batch)。

【gated 边界·撞到停+报+不空转】
  G-platform 不碰平台内部 RSI/PoI live wiring(平台 held)→ 只接 FDE 外部信号。
  G-verdict T3 真数据待 soul checklist_scorer 真实 verdict 流 → 先 mock。
  G-batch T4 真飞书复核数据待真批次 → 先 mock(G3.1 scope 已授)。
  G-cloud 云端实测/改动需 SSH 云端 → 撞到无权限停报。
  G-prod-DDL 生产 DDL/公网 post/改别框 turf → 停 + AskUserQuestion。

【每个增量纪律】
  · 改代码用 using-git-worktrees 隔离,不污染 main;ship 前 R4 git 检查;不 -A/push/force。
  · verification-before-completion:T1 必须 benchmark 在【生产 recall 路径】实测分提升(非只单测/非只 benchmark 管线)才标 done。
  · 守黑盒护城河:ingest/recall 热路径不调 LLM(本地 BGE/交叉编码器可,LLM 需 opt-in flag)。
  · 不重复造轮子:reranker/rewrite/lifecycle/poi 全链代码已存,只接线不重写。
  · R1 drift / R2 全做 / R3 4h / R5 anchor 触发即停。
  · 每轮一句话报:做了 Tn 哪步 + 验证证据(file:line/分数/命令输出)+ 下一步 / 撞哪个 G。
  · 凭据值永不回显/不入 git。

【起手序】T1(reranker 进生产·先 Task1.1 调研注入点)→ T2(ingest 修·先云端实测)→ T4(专家回路 mock)→ T3(PoI adapter)。按 plan docs/plans/2026-06-05-fde-rsi-dual-flywheel-closure.md 的 TDD task 执行。

【DONE】T1/T2 验证(生产路径分提升+跨设备召回通)+ T3/T4 mock 端到端跑通 + design/plan 行更新;或剩余全卡 G-verdict/G-batch/G-cloud/G-platform 等用户/别框 → 停报。
```

## 关键 file:line 锚点(执行用)
- 生产 recall 路径:`daemon.py:610-720`(handle_request recall)、`recall.py:1241-1267`
- reranker benchmark 用法:`tests/eval_rerank.py`;分数 `RESULTS.md:54-56,186`
- lifecycle 提升函数:`recall.py:708`(`promote_lifecycle_tier`)
- llm_backend hook:`metamemory/builder.py:76`(生产 `recall.py:1247` 未传)
- 跨设备 ingest bug:`ops/v0.9_to_v14_adapter_patch.py:187-216` vs `daemon.py:1092,982`
- PoI 全链:`sql/004_poi_credit.sql`、`proof/poi_credit_store.py:18`、`proof/poi_reconciler.py:37-44`、`recall_pkg/poi_weighting.py:37`、云端 boost `ops/patch_v14_recall_poi_boost.py`(默认关)
- 专家回路:`vertical-task-factory/fde-toolbox/feishu_client.py`(download_row_attachments/read_bitable_records)+ T3 胶囊管线 `feishu_retention_scaffold.py`

## 续调研(4 路 agent 可 SendMessage 续)
a929e3a457429c03e(胶囊/PoI/跨设备)· a3266fa277170adcc(检索/WIKI2/LLM/metamemory)· aed0e51d88e747735(平台/v5 进展)· 第4路 ad619c6d8b7f840f4 超时(历史文档回顾未完)。
