# Assay BC1 — 组织记忆验证基准(首版)

> 30 题 · 四维 · 机器判分 · 诚信计分(U 不充正分)。
> 种子全部来自一个 AI 组织 130 天真实运行史(脱敏参数化,防背题)。
> 发布:2026-09-27 · 出题规格:[item_framework_v0](ASSAY_BC1_item_framework_v0.md)

## 考什么

| 维度 | 题数 | 一句话 |
|---|---|---|
| DIM1 跨框状态一致 | 7 | 从时间线/声明/原始行推出真实状态,抓矛盾 |
| DIM2 写入门质量 | 8 | 毒写拒收/去重阈值/锚池语义门 |
| DIM3 重犯率 | 7 | 复发计数/假绿识别/漂移 margin |
| DIM4 归因可追溯 | 8 | 环节违例/锚池审判/skip 保真 |

每题判据显式引用 criteria@catalog-v0;public 18 / holdout 12
(holdout 封存,首外部考生起用,保证你没见过题)。

## 怎么考(外部考生流程)

1. 报名:[开一个 exam-signup issue](https://github.com/chunxiaoxx/nautilus-compass/issues/new?template=exam-signup.md)(选 BC1,接受诚信条款)
2. 取卷:考卷=`runtime/assay_bc1_20260927/` 下 `selftest_exam_paper_v2.json`
   同构的 public 18 题(应考邮件回复时发你当期版本,含题面+数据,
   **不含真值**)
3. 作答:任意方式(人/agent/脚本),交 `answers.json`(格式见考卷头)
   ——诚信条款:答案与工件须可复算,U(不可算)不充正分,瞎猜 FAIL
4. 判分:我们跑 [`verify_bc1.py`](../../runtime/assay_bc1_20260927/verify_bc1.py)
   (判分器公开,你可自跑预判),三态成绩单 ed25519 签名回执给你
5. 上墙:成绩(默认匿名代号)入 BC1 板;对判分不服可凭工件 90 天
   窗口挑战(§5b)

## 自家成绩单(诚实计分示范)

- v2(发布版题集):**18/18 PASS · 0 FAIL · 0 U**
  [成绩单(签名)](../../runtime/assay_bc1_20260927/SELFTEST_SCORECARD_V2.md)
- v1(首测):11/18——7 个 FAIL 经审计**全部为出题侧缺陷**
  (含 2 题真值错误=考生比真值对)。全套工件保留:
  [v1 成绩单](../../runtime/assay_bc1_20260927/SELFTEST_SCORECARD.md) ·
  [非实现者复算 GREEN](../../runtime/assay_bc1_20260927/RECOMPUTE_SELFTEST.md)
  ——「出题缺陷→审计→修复→重考」完整公开样本,这就是我们卖的东西:
  **连自己的丑数字也上墙的验证所**。

## 复算

题集与判分管线全公开:clone 本仓 → `python runtime/assay_bc1_20260927/verify_bc1.py <answers.json>`。
decision_set sha256=3b9def7d…(v2)。

## 边界

- 首版只含机器判分题型;v5 长程三维另册(RSI 线)
- 组织记忆验证原型,非通用 agent benchmark;分数只在该题集语义内可比
- 运营方:伊洛科技有限公司(Nautilus Assay)· 赔付条款 §5b 适用
