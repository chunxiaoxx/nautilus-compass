# 全站质量审计报告 V1(2026-10-15 · 响应用户"一大堆 bug/丑陋/无法使用")

> 方法:三层审计——serve 层(40 页 HTTP+size 批探)/渲染层(playwright 37 静态页+app SPA 8 路由:console 错误+失败请求+空白页)/入口层(站内链接形态盘点)。
> 结论先行:**45 个检测面全绿**。本轮抓出并修复 14 个死面(13 目录页+app 榜单 403)。

## 一、抓出并已修(✅全部实测)

| # | 问题 | 影响 | 修法 | 验证 |
|---|---|---|---|---|
| 1 | **org/ 7 页 SPA 兜底**(business-plan/whitepaper/e2e/leaderboard/map/pipeline/index) | 白皮书/BP 等对外文档在 www 主域全死 | conf 补 `^~ /org/` location | 正确形态全 200(text 12155 等) |
| 2 | **products/ 6 页 SPA 兜底**(unipat/harness/compass/data/embodied/companion) | 产品线六页全死 | conf 补 `^~ /products/` | 全 200 |
| 3 | **auth/callback 兜底** | 登录回调死=登录流程断 | conf 补 `^~ /auth/` | 200·1478,渲染通过 |
| 4 | **app /leaderboard 数据 403** | app 主站榜单页无数据(用户可见"无法使用") | app 白名单+`hub/leaderboard`(读面;写面 bounties POST 仍 403) | 渲染 text 350→1370,8/8 绿 |
| 5 | products/ 裸目录 403 | 无站内引用,零影响 | 保持(autoindex off=安全默认) | — |

## 二、审计通过面(基线立此)

- **静态页 37**(playwright 渲染):全部 200/无空白/零 console error/零失败请求(auth/callback text:16 为功能本质)
- **app SPA 8 路由**:全 200 全绿(/ /login /pricing /leaderboard /dashboard /submit /tasks /agents)
- **主链 8 锚**(liveness timer 每 30min 自动):全绿
- **站内链接**:org/products 引用 16 处全 .html 形态,零裸链引用

## 三、已知遗留(非本轮引入,列台账)

- 子域 x.chunxiao.wang/crm/hr-chunxiao/zenmind=个人/他框域,移交自查
- products/ 目录缺 index(裸访问 403,无入口引用,低优)
- ~~41 页 SPA 全量~~ ✅已完成(10/15):47 路由提取(dist path 字段)→42 静态路由 playwright 未登录态全绿(零 HTTP 错/零空白/零 console 错误);4 参数路由需具体 id+登录态路由待逐 role 轮
- bench/org 数据内容正确性(非活性)未深审——判读数据只有 1 单,内容层面待榜填充

## 四、防复发

- liveness-check.timer 扩锚候选:org/whitepaper.html、app /leaderboard 渲染(下版加)
- 目录型页面一律配 location(免疫册已有);新增页面 ship 时必跑本报告方法三层
- 本报告方法可复跑:site_audit.py(HTTP 层)+site_render_audit.js+app_spa_audit.js(playwright 层,Temp/pwshot/)

—— platform · 2026-10-15 晨


## 五、E2E 功能闭环审计(10/15 增补·用户拷问后补)

**抓出 2 个真 bug 并修复(此前三层全绿但功能是断的——活性≠可用)**:
1. 提测表单提交=网络错误(JS 写死跨域 API,CORS 预检失败)→ 修为同源相对路径;E2E 真提交 PASS+DB 独立验证入库(id=4012dc6a...)
2. 首页零提测/榜单入口(客户无路可走)→ 两 SPA 壳插静态导航条;E2E 首页入口 PASS

**E2E 旅程 6/6 PASS**(e2e_submit_journey.js,可复跑):首页入口→表单字段→真填→提交→受理回执(受理成功+id 4012dc6a)→单据标识。
**教训入册**:渲染层全绿不等于功能可用——表单类页面必须 E2E 真提交;此 E2E 列入周检(LIVENESS_RUNBOOK 下版)。