# Nautilus 网站体系全面审度报告(2026-10-08 · compass 出 · 承用户"重新审度"令)

> 三层审度:技术白皮书 v1.5 承诺 vs 实际 / 商业计划书 v1.3 承诺 vs 实际 / 网站体系现状 vs 应有。每条带实测证据与修复方案。

## 一、现状全景(12 触点实测)

| 触点 | HTTP | 内容级 | 归属 | 判读 |
|---|---|---|---|---|
| nautilus.social/ 主门面 | 200 | 11.4KB·28 卡·8 导航 | platform | ✅ 结构在,但定位文案="数据飞轮管道平台"与白皮书"评测与数据基础设施"不一致 |
| /leaderboard.html | 200 | 4.6KB·判读卡+sha16 | compass | ✅ 内容实证合格 |
| /unipat.html | 200 | 7.2KB·产品导览 | platform | ⚠️ 与 leaderboard 分工不清;产品密度待加强 |
| /intake.html | 200 | 受理入口+邮箱实址 | compass | ✅ |
| /criteria/ | 200 | 判据×10 | compass | ✅ |
| /pipeline.html | 200 | 管道页 | platform | ✅ |
| /status.html | 200 | 判读卡查询(v1 前端) | compass | ✅ 新上线 |
| /registry.html | 200 | 语料计数器 | compass | ✅ 新上线 |
| /api/judge_status | 200 | 判读状态 API | compass | ✅ 今日上线 |
| /corpus_stats.json | 200 | 语料统计(1846) | compass | ✅ 今日刷新(原 1716 陈旧) |
| compass.nautilus.social | 200 | 8.7KB 双产品线 | compass | ✅ 今日刷新 |
| data.nautilus.social | 200 | SPA 壳(697B) | flywheel | ⚠️ JS 渲染,curl 只验壳;渲染后质量未验 |

## 二、技术白皮书 v1.5 承诺 vs 实际

| 白皮书承诺 | 网站实际 | 差距 | 修复 |
|---|---|---|---|
| 评测基础设施(预注册判据+三态判读+复算) | ✅ intake+criteria+leaderboard 全通 | 无 | — |
| 数据飞轮管道(五段全通) | ✅ pipeline.html+/api/corpus_stats | 无 | — |
| NACRE 机制章(§5.1 升格) | ⚠️ 机制章在白皮书正文,但网站上无 NACRE 独立入口 | compass 子域有但主站无导航 | 主站加 NACRE 产品卡链接到 compass 子域 |
| caliber-bench 元基准 | ✅ HF 开源;⚠️ 主站无入口 | 缺独立产品页或主站链接 | 主站加 caliber-bench 卡 |
| 组织 OS(§7 六件) | ⚠️ 主站有 /os.html 链接但内容未知 | 需实测 | 10/11 终检时验 |
| 归因提升(数据→模型→再判) | ✅ L2 样例披露;⚠️ 2.9KB 偏薄 | 作为 $199 产品样例说服力不足 | v5 v1.5 重出时加厚(候 v5 窗) |

## 三、商业计划书 v1.3 承诺 vs 实际

| BP 承诺 | 网站实际 | 差距 | 修复 |
|---|---|---|---|
| L1 免费收录 $0·24h | ✅ intake+status 全通;✅ SLA 分档口径已改 | 无 | — |
| L2 深度报告 $199·48h | ⚠️ L2 样例 2.9KB 偏薄 | 样例加厚(候 v5 v1.5 窗) | 呈 v5 |
| L3 企业定制 $999 起 | ✅ intake 页有 | 无 | — |
| S1-S4 数据/轨迹包 | ⚠️ 主站 pipeline.html 有管道,但 S 线产品页未见 | 缺独立 S 线产品页 | v5/平台补 |
| Wave2 智谱(10/12 发) | 呈批件就绪(platform) | — | 10/12 发 |
| 线索池 41 家 | 3 家已回应(OpenHands/Cline/有道) | 继续跟进 | — |

## 四、网站体系结构性缺陷(用户批评成立的三点)

### 缺陷一:无"基础设施+产品生态"叙事
主站 title="数据飞轮管道平台"——只讲管道不讲产品;28 卡是管道功能卡,不是产品卡。**用户要的是:进来一眼看到"你有什么产品、怎么买、怎么验证"**,而不是"我们的管道有多强"。
→ **修法**:主站改版为"产品体系首页"(六卡=六产品,每卡带 CTA→产品页),管道叙事降为底层基础设施区块。

### 缺陷二:产品页间零互链
leaderboard/unipat/pipeline/status/registry/criteria 六页各自独立,**无统一导航/互链/统一数据源**。访客从榜页看不到判读服务,从判读服务看不到元基准。
→ **修法**:统一导航条(全站六页共享)+每页底部"相关产品"互链。

### 缺陷三:SPA 站渲染后不可验
data./compass. 是 SPA(JS 渲染,curl 只见壳)——内容级验证需 headless。data 站有 /api/health 200 ✓;compass 站已刷为双产品线静态页 ✓。**剩余**:data 站渲染后质量待 headless 深验(10/11 终检加做)。

## 五、修复优先级(10/12 开业前)

| 优先 | 件 | owner | 死线 |
|---|---|---|---|
| **P0** | 主站改版:产品体系首页(六卡+CTA)+统一导航 | platform + compass 供内容 | 10/10 |
| **P0** | L2 样例加厚(v5 v1.5 对齐) | v5 | 10/11 |
| **P1** | data 站 headless 深验 | platform + compass 协同 | 10/11 |
| **P1** | 统一导航条全站部署 | platform | 10/11 |
| P2 | NACRE 产品卡上主站(链接 compass 子域) | compass 供内容 + platform 装订 | 10/11 |
| P2 | S 线数据产品页(v5 出内容) | v5 | 10/11 |

—— compass · SITE-COMPREHENSIVE-REVIEW(完整版,候平台认领+呈用户)
