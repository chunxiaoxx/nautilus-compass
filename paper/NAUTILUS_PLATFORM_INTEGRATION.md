# Nautilus Compass v0.9 主站集成 Prompt

> 给 nautilus.social 主站维护对话框使用。目标:把已 build 好的 Compass landing page 作为主站二级页面 (路径 `/compass`) 接入,与主站 header/footer/style 完全融合,而非独立 landing。

---

## 背景 (你需要知道的)

- **Compass v0.9** 是 Nautilus 7-capability 之一 (导航能力),已 build 完成。
- 产物: 单文件 `landing/index.html` (~22KB · inline CSS · 内嵌 tab JS · 11 sections · 中文为主)。
- 当前部署位置 (源文件): `C:\Users\chunx\.claude\plugins\nautilus-compass\landing\index.html`
- 你**不需要**懂 Compass 内部实现,只需把这个 HTML 嵌进主站。

---

## 1. 页面结构对齐 (必须)

把 Compass 内容塞进主站模板,**移除 Compass 自带的 header/footer**,保留 main 内容区。

- ✅ 复用主站 **header**: 主页 / 7 Capability / 文档 / Discord
- ✅ 复用主站 **footer** (统一 · 不要 Compass 单独 footer)
- ✅ 主色调 / 字体 / 间距 / 按钮样式对齐主站 design tokens
- ✅ 加 **breadcrumb**: `主页 > 7 Capability > Compass`
- ✅ 保留 Compass 的 11 sections 和 tab JS 交互

**Fallback** (如果你没有主站源码访问权): 提取主站 `<header>` `<footer>` HTML + 主 CSS 变量 (`--primary` `--bg` `--font` 等),注入到 Compass HTML 顶部并删除其原 header/footer。

---

## 2. nginx 路由方案 (推荐 A)

- **A (推荐)**: `nautilus.social/compass` → `/var/www/nautilus/compass/index.html`
  ```nginx
  location /compass { try_files $uri $uri/ /compass/index.html; }
  ```
- B (备选): `compass.nautilus.social` → 301 重定向到 `nautilus.social/compass`

选 A 的理由: SEO 权重统一、cookie/session 共享、主站导航无缝。

---

## 3. 主站入口位置

- **主页 hero 下方** 的 7-capability 卡片网格中,Compass 卡片需:
  - icon (指南针/罗盘)
  - badge: `v0.9.0 released`
  - 链接 → `/compass`
- **主导航** "7 Capability" 下拉菜单加 Compass 项
- **文档侧栏** 加 Compass 入口 + 链接到 `/compass/install`

---

## 4. SEO

- `sitemap.xml` 追加 `/compass` 和 `/compass/install` (priority 0.8)
- `<meta name="description">` 已在 HTML 中,保留
- `<meta property="og:image">` **待补** — 暂用主站默认 OG 图,后续替换为 Compass 专属
- 加 `<link rel="canonical" href="https://nautilus.social/compass">`

---

## 5. 测试 Checklist

- [ ] 桌面 (1920 / 1440 / 1280) 渲染正常
- [ ] 移动响应式 (375 / 414) header/footer/内容不溢出
- [ ] tab JS 切换工作 (11 sections 内的 tab 组件)
- [ ] 主站 nav 链接全部可点
- [ ] breadcrumb 路径正确
- [ ] `/compass` 直链可访问、刷新不 404
- [ ] Lighthouse: Performance ≥ 85, SEO ≥ 95

---

## 6. 完成后回报内容 (必须)

部署完成后,在对话框报告:

1. **部署 URL**: `https://nautilus.social/compass` (确认 200)
2. **截图**: 桌面 + 移动各 1 张
3. **Visual diff**: 跟主站其他页面 (如 `/about`) 对比 — header/footer/字体/间距是否一致
4. **入口验证**: 主页卡片网格截图 + 点击跳转录屏/截图
5. **SEO 验证**: sitemap.xml 节选 + Lighthouse 分数

---

**优先级**: P0 (Compass 已 release,等这一步上线)
**预期工时**: 2-4 小时
