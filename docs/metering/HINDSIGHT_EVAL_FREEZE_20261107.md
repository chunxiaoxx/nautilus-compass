# Hindsight 独立评测 · 判据冻结档(2026-11-07 · V1.2 增补版)

> V1(`HINDSIGHT_EVAL_PREREG_V1_20261031.md`)+ V1.1 + V1.2 附录在此 commit 冻结,开跑。
> 首冻 commit `bf554727`(V1.1);V1.2 车道增补仍属开跑前(零题面已跑)。
> 任何判据变更=新版本档,禁原档放宽。结果无论好坏照发(V1 §四)。

## 冻结面(sha256 前 16 位)

| 文件 | sha16 |
|---|---|
| docs/metering/HINDSIGHT_EVAL_PREREG_V1_20261031.md | `fc752e330bb40b5c` |
| docs/metering/HINDSIGHT_EVAL_PREREG_V1_1_ADDENDUM_20261107.md | `69b11a6d6982620b` |
| docs/metering/HINDSIGHT_EVAL_PREREG_V1_2_ADDENDUM_20261107.md | `f02ca4780cf2481c` |
| tests/eval_longmemeval_accuracy.py(compass 参照 harness,零改动) | `fa815d3e10412c2d` |
| tests/hindsight_adapter.py(run-freeze 版:官方 client 端点) | `ced75862b09fc6a1` |
| tests/eval_hindsight_arm.py(hindsight 臂评测器·V1.2 车道默认) | `10f2f64feff148dc` |

## 环境

- hindsight 镜像:`ghcr.io/vectorize-io/hindsight:latest` · digest
  `sha256:19d0c08f3df79acac29384826419a1ca158129e81ec527cdcbd8c97ff4ef76da`
  (ghcr 直连停滞 → crane 经本机代理拉同名同 digest OCI tar → docker load,内容未变)
- hindsight-client==1.2.0(PyPI 官方)
- 数据集:LongMemEval-S 500 题(HF `xiaowu0162/longmemeval` main 分支 `longmemeval_s`,
  278,025,796 B;本地 `/tmp/longmemeval_s.json`,sha16=`08d8dad4be43ee20`)
- subject/judge/retain LLM:**qwen3.8-max @ 百炼 TokenPlan compatible-mode**
  (V1.2 附录;MiniMax-M3 为已验证 fallback)
- 参照读数:compass v0.8 = 56.6%(n=500 · DeepSeek V3.2 subject · 2026-05-04 锁);
  **跨 subject 模型对比,报告须显式标注**

## 执行序(冻结后依序)

1. Docker 部署(provider=minimax · 其余出厂默认)→ 合成内容 retain/recall 冒烟(不触
   LongMemEval 题面)
2. `--phase retain --full --workers 6`(500 bank / 25,112 retain)
3. `--phase eval --full`(recall→subject→judge,逐题 jsonl 留证)
4. 评测卡+报告发布,回贴 hindsight#5584

## 红线

- retain/recall 基础设施失败 → 显式 HindsightError 中止留证,禁静默跳过
- judge 失败 → 显式 error 标记+重试(harness 内建 429/5xx 退避),单列失败率
- 单批跑完,不跨批 cherry-pick;空 recall=数据照报 0 分
