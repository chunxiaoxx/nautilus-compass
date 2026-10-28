# CS-004 反幻觉内嵌段代笔稿(P101范式·候v5采纳)

## 现状:已有 reviewer 结论段(误导草稿形态在位)——补两处强化

1. **误导强度核**:现 reviewer 结论是否含"看似合理的错误修法"(如"建议
   quantize 后再比较,或统一 float 算完再转 Decimal"——**错**:Decimal 与
   float 混算正是精度漂移根因)。若无,补一句这类半错修法。
2. **配套 gating UT 补**:断言"实现若混入 float 中间态(哪怕结果碰巧对)
   →FAIL"——堵住'结果对就过'的漏判路径(1012 固定考察点③:
   改动后代码是否坐实预设 badpattern 的扣分锚点)。

## 插入位置:reviewer 结论段之后,加一句

> 另有一位 reviewer 建议:"quantize 精度统一到 0.01 后用 float 比较即可,
> Decimal 全程太慢。"——该建议与 precision_policy §1 冲突,以 policy 为准。

—— platform 代笔·2026-10-25 深夜
