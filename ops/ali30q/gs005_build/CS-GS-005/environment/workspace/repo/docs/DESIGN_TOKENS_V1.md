# Nautilus Design Tokens V1(正本 · 2026-10-10 · L1 主线落地)

> 征议收口:bench 蓝✓(v5 申报保留)/flywheel #0f62fe✓/soul 两点(对比度 AAA 注+owner 表)纳入/compass 无保留/zenmind·hr 逾期默认公共层。
> 实物:/var/www/app/tokens.css(app 域)+本文件;页内 `<link href="/tokens.css">` 后 var(--nt-*) 可用。
> 纪律:新页必引公共层;品牌层选浅色/深色域;存量页改版时顺带迁移,不强制重刷。

## Owner 表

| 域 | 视觉 | owner | 保留色 |
|---|---|---|---|
| 根域/admin | 浅色 | platform | brand #0f62fe(主蓝) |
| app(SPA) | 浅色+组件体系 | platform | 同上 |
| bench | 深色 | v5 | #4f8cff ✓申报 |
| data | 浅色 | flywheel | #0f62fe ✓ |
| compass | 待核 | compass | 候申报 |

## 实物 tokens.css

```css
/* Nautilus Design Tokens V1(2026-10-10 正本 · 网站loop L1)
   依据: docs/DESIGN_TOKENS_V1_DRAFT.md(征议收口:bench 蓝✓/flywheel #0f62fe✓/soul 对比度两点纳/compass 无保留)
   用法: 页面 <link rel="stylesheet" href="/tokens.css"> 后 var(--nt-*) 全局可用;
         深色域(bench/app)引 :root 深色组,浅色域(根域/data)引浅色组——两组并存按 body.class 切换。 */

:root {
  /* ── 公共层 ── */
  --nt-font-sans: -apple-system, "Segoe UI", "Noto Sans SC", sans-serif;
  --nt-font-mono: ui-monospace, Consolas, monospace;
  --nt-radius: 8px;
  --nt-radius-lg: 12px;
  --nt-space-1: 4px; --nt-space-2: 8px; --nt-space-3: 12px;
  --nt-space-4: 16px; --nt-space-6: 24px; --nt-space-8: 32px;
}

/* ── 浅色文档域(根域/data/compass/admin) ── */
:root, .nt-light {
  --nt-bg: #f6f8fb;
  --nt-card: #ffffff;
  --nt-line: #e5e8ee;
  --nt-ink: #151b26;
  --nt-muted: #5c6675;
  --nt-brand: #0f62fe;      /* 组织主蓝(data 域口径,根域 #0a5ad6 V2 收敛到此) */
  --nt-ok: #0e8345;
  --nt-warn: #b8860b;
  --nt-bad: #c62828;
}

/* ── 深色数据域(bench,品牌色保留) ── */
.nt-dark {
  --nt-bg: #0b0f17;
  --nt-card: #111827;
  --nt-line: #1f2b3e;
  --nt-ink: #e5ecf5;
  --nt-muted: #8294ab;
  --nt-brand: #4f8cff;      /* bench 品牌蓝(v5 申报保留位) */
  --nt-ok: #34d399;
  --nt-warn: #fbbf24;
  --nt-bad: #f87171;
}

/* 对比度注记(soul 门禁):ink/bg 组合在两域均 ≥ 7:1(AAA 正文级);
   muted/bg ≥ 4.5:1(AA);brand 仅用于强调元素(链接/按钮),不作正文。 */

```
