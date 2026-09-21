# Hosted Jev 独立校准评估·预注册协议(2026-09-21 深夜立项)

> 触发:awesome-jev 维护者关门留门原文确认——"a standalone, reproducible evaluation
> of Jev (the hosted model, not a reproduction)" 会被 Evaluation and calibration 收录。
> 报数纪律:开工先落预注册判据(本档),判据只紧不松。

## 一 · 评估对象与声明

- 对象:**TypeSafe Jev hosted API 模型**(console.typesafe.ai;或 Requesty 网关),
  模型版本钉死(评估期间锁定,版本号入回执 subject)。
- 评估的声明(由我们产出,供第三方复算):「Jev 在决策集 D 上的校准水平
  (Brier/ECE)为 X/Y」——注意:这是**我们做新评测并自证可复现**,不是复算 TypeSafe
  的声明(其官网无逐集数字可复算)。与 Genesis 系列的区别如实标注。

## 二 · 决策集 D(自建,预注册)

- 形态:N 道(目标 200-400)确定性决策题,三类混合:
  ①布尔事实判断(可机器验证真值,如数值比较/集合成员/日期推理)
  ②三选一分类(闭合标签集)
  ③数值区间判断(离散档位)
- 生成纪律:程序化生成+种子固定(脚本+seed 入档,**任何人可再生成同集**);
  每题真值由生成器内置(零人工标注=零标注争议)。
- 污染控制:题目为程序化合成(非公开基准题),LLM 预训练无法逐题记忆;披露
  「合成题≠真实任务分布」边界。

## 三 · 判据(预注册,锚 calibration-claim-verify-v1)

- 每题记录:Jev 的选择+完整概率分布(API 返回)。
- 指标:top-label Brier / ECE(15 bins)/准确率;三套口径同报
  (严格全题/按置信度分层/按题型分层)。
- 复现件:决策集生成脚本+全部原始响应(jsonl)+计算脚本=VerifyPack v0.3 包
  (calibration claim kind,subject=API 版本+题集 seed,TTL 90 天)。
- 红线:不重跑不并行不挑选(一次全量;失败请求如实记录,不剔除)。

## 四 · 成本与前置

- 预算:Jev 宣称便宜 40-400x;按 400 题×3 类估算 ≈ $1-5 级。**需用户提供
  TypeSafe(或 Requesty)API key + 预算上限批准**。
- 时间:key 到手后半天内出全部读数+回执。

## 五 · 产出与去向

1. 研究报告+签名回执(墙挂档)
2. PR 重投 awesome-jev(按维护者口径:standalone study of hosted model)
3. TypeSafe 外联跟进弹药(函 #1 附件级证据)
4. 校准产品线首弹(引擎+判据+回执全链演示)
