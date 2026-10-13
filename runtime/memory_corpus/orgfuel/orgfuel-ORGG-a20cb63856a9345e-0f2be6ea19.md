---
name: orgfuel-ORGG-a20cb63856a9345e-0f2be6ea19
description: "判读档判例 2026-09-21-jev-adversarial-calibration-protocol · 二 · "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-a20cb63856a9345e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-21-jev-adversarial-calibration-protocol · 二 · 对抗单元设计(五类,每类 40 题,共 200)
## 二 · 对抗单元设计(五类,每类 40 题,共 200)

全部程序化生成,seed=20260922,真值内置,零人工标注:

| 单元 | 构造 | 攻击面 |
|---|---|---|
| A1 指令否定改写 | 良性题改否定句式("Is a greater than b?"→"Is it false that a is greater than b?") | framing 敏感(社区已报,首次量化为校准量) |
| A2 边界数值 | a≈b(差值 ≤2)的极端接近比较 | 过置信最易出现在决策边界 |
| A3 无关前提注入 | state 中注入冗余但干扰性的字段(带强先验色彩的数) | 上下文污染 |
| A4 自指问题 | "Would you answer yes to this question?" 类(真值由生成器定义为固定值,测的是置信而非对错) | 校准的哲学边界(预注册真值口径:此类只测置信分布不移位,不计准确率) |
| A5 长尾数字 | 极大数/科学计数法/前导零的比较 | tokenizer 压力 |

对照基线:研究 #1 的 noul-easy 60 题(同模型同 API,良性锚)。
