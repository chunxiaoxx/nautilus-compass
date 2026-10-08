# 主站改版 compass 供给包(应 SITE-COMPREHENSIVE-REVIEW P0 件 · 死线 10/10)

> 平台主责改版,compass 按分工供内容。本包=两张产品卡完整装订素材+统一导航条建议,平台取用即贴,零二次加工。五条外链 2026-10-08 外网复验全 200。

## 卡一:NACRE 判分模型

| 字段 | 内容 |
|---|---|
| 卡标题 | NACRE 判分模型 |
| 一句话 | 压缩×验证×因果倒置的原生判分模型——让 AI 给 AI 判卷有据可查 |
| 支撑行1 | 判分准确率 88.51%(Qwen3-1.7B + NACRE LoRA,J1/J2/J7 三门全绿) |
| 支撑行2 | 部署精度纪律:fp16 零漂移可用 / int4 禁用(291 案实测,PRECOR) |
| 支撑行3 | 判据开源 + 判例集 v1.4 封版,判读全程可复算 |
| CTA 主 | 提交评测 → https://nautilus.social/intake.html |
| CTA 次 | 模型与判据 → https://huggingface.co/nautilus-compass/nacre-judge-v1 (200✅) |
| 详情页 | https://compass.nautilus.social/ (200✅) |
| 卡片状态徽标建议 | 10/12 开业 |

## 卡二:caliber-bench 元基准

| 字段 | 内容 |
|---|---|
| 卡标题 | caliber-bench 元基准 |
| 一句话 | 评测 AI 评测器的基准——测判分器本身是否可靠 |
| 支撑行1 | v0 已开源(HF dataset,含判据张力样本与三态标注) |
| 支撑行2 | 元基准样例包 10/12 与榜面同窗发布 |
| 支撑行3 | 定位:行业首个判分器自检基准(命名 10/7 定稿,原 signal-decay-bench) |
| CTA 主 | 数据集 → https://huggingface.co/datasets/nautilus-compass/caliber-bench-v0 (200✅) |
| CTA 次 | 判据披露 → https://nautilus.social/criteria/ (200✅) |
| 卡片状态徽标建议 | 开源可用 |

## 统一导航条建议(全站六页共享,片段直贴)

```html
<nav class="site-nav">
  <a href="/">首页</a>
  <a href="/leaderboard.html">榜单</a>
  <a href="/unipat.html">产品</a>
  <a href="/status.html">判读查询</a>
  <a href="/criteria/">判据</a>
  <a href="/intake.html">提交</a>
  <a href="https://compass.nautilus.social/">NACRE</a>
</nav>
```

样式随平台现有设计体系;唯一要求:七页(含新增产品卡锚点)全站一致,消除六页零互链。

## 配套交代

- L2 样例加厚:归 v5 v1.5 窗(本包不含);
- data 站 headless 深验:compass 承,10/11 终检交付;
- 本包素材数据锚出处:PRECOR_BC_VERDICT / judge_lora_p3 三门记录 / 判例集 v1.4 封版件,仓内可溯源。

—— compass · SITE-CONTENT-PACK · 2026-10-08
