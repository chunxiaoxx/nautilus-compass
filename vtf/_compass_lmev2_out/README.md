# LME-V2 small tier · compass memory 首次全量出数（2026-08-30）

> LongMemEval-V2（LME-V2）small tier 451 题（web 240 + enterprise 211）· compass_chunk_hybrid（bge-m3 embed · cuda）
> 运行机：GPU 实例 651799（48G）· evidence 原件在本目录 tar 包内

## 口径

- **评测**：LongMemEval-V2 small tier，`/root/LongMemEval-V2/run_compass.py`（绕过 method 白名单直调 evaluation.harness）
- **memory**：compass_chunk_hybrid（`/root/compass_cfg.json` · bge-m3 device=cuda · top_k 8）
- **reader（subject）**：doubao-seed-2-0-pro-260215 @ ARK API（与 e2e 500 全量口径同款 subject，营销口径一致）
- **judge**：doubao-seed-2-0-pro-260215 @ ARK（newapi glm-5.3-flash 因内容审查拦截题干弃用，见 TRANSFER_RUNBOOK）
- **温度**：0.6 / top-p 0.95 / top-k 20 · reader 并发 4 · prompt-build 单 worker（BGE 线程竞态约束）
- 运行日期：2026-08-30 · 两域均 0 Traceback

## 结果

| 域 | 题数 | overall（含拒答） | 实答正确率 | 拒答 |
|---|---|---|---|---|
| web | 240 | **19.6%** | 26.8%（168 实答） | 72（30%） |
| enterprise | 211 | **12.8%** | 17.4%（155 实答） | 56（27%） |
| 合计 | 451 | 16.4% | 22.4%（323 实答） | 128（28%） |

### web 域分类型（实答中）

| 类型 | n | correct | wrong | unknown |
|---|---|---|---|---|
| procedure | 42 | **52.4%** | 40.5% | 7.1% |
| gotchas | 15 | 46.7% | 46.7% | 6.7% |
| dynamic | 51 | 17.6% | 27.5% | 54.9% |
| static | 60 | 11.7% | 21.7% | **66.7%** |

## 解读（诚实边界）

1. **absolut 数不可与 e2e 500 直接比**：LME-V2 是多 session 长对话 haystack，与 e2e 500（LME-M 单 haystack）任务结构不同；此批为 compass 在 V2 上的**首次未调优基线**。
2. **短板画像与 V1 一致**：procedure/gotchas（可检索的明确规则）显著强于 static/dynamic；static/dynamic 的 unknown 率 55-67% 指向**检索未召回相关上下文**（多 session 切分/路由适配未调优），非 reader 拒答癖。
3. **1.5B smoke 前置验证**：全量前用 Qwen2.5-1.5B 本地 vLLM 烟测 3 题全链路绿（0% 分数=模型弱属预期），管线六坑定案见 `vtf/TRANSFER_RUNBOOK.md`。

## 复跑

命令全文见 `vtf/TRANSFER_RUNBOOK.md` "LME-V2 管线 smoke 全通定案"节。全量参数：`--domain web|enterprise --tier small --base-url $ARK_BASE_URL --model doubao-seed-2-0-pro-260215 --prompt-workers 1 --reader-concurrency 4 --evaluator-* 同 ARK`。

## 文件

- `compass_web_small/aggregated_metrics.json` / `per_question.jsonl`（240 行逐题）
- `compass_enterprise_small/` 同构（211 行）
- `run_args.json` 两域各一（精确复跑参数）
- `lmev2_results.tar.gz`（远端打包原件）
