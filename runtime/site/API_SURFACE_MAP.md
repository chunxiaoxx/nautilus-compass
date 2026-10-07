# 网站前后端对接表 v1(compass 材料包 · 2026-10-07)

> 网站系统搭建/开发对接正本:产品页 × 真端点映射。原则:产品页先静态上线,活数据分批接(10/10-11)。

## 一、在役真端点(外网 200,已实测)

| 端点 | 类型 | 数据/功能 | 前端对接方式 |
|---|---|---|---|
| `/leaderboard.html` | 静态页 | Round1 榜面(26.7/16.7/+10pp,sha16) | 直接链接/iframe 嵌首页 |
| `/unipat.html` | 静态页 | 评测榜入口+L2 样例链接 | 导航 |
| `/intake.html` | 静态页+表单 | 评测提交受理(邮箱 CTA) | 产品页主 CTA |
| `/criteria/` | 静态页 | 判据披露(判据锚正本清单) | 信任背书链接 |
| `/pipeline.html` | 静态页 | 五段管道+读数 | 数据产品页底座 |
| `/pipeline/e2e` | **活 API** | 每单五段链验证(DB 实态:total20/full8) | 产品页"管道实态"数字直读 |
| `org.nautilus.social/L2_report_sample.md` | 静态 | 深度报告样例 | L2 卡片"看样例" |
| HF `nautilus-compass/*` | 外链 | 判分模型+元基准 | 产品卡直链 |

## 二、待建端点(前后端对接深化 10/10-11)

| 端点 | 来源 | 用途 | 优先级 |
|---|---|---|---|
| `/api/leaderboard.json` | Round1 定版报告(DB/CSV) | 榜面活数据 | P1(10/11 前) |
| `/api/intake` POST | intake 表单→受理台账 | 在线提交替代 mailto | P2(开业后) |
| `/api/judge_status?id=` | 判读台账 | 客户查进度(判读卡状态) | P2 |
| `/api/corpus_stats` | corpus_pipeline manifest | 语料计数器公开(自证) | P3 |

## 三、页面归属与装订

- **首页(本包 index.html)**:平台=基础设施叙事+产品体系导览——平台 own,compass 出稿;
- **产品页**:评测榜/判读服务/元基准(NACRE)→compass 供内容;数据管道→v5;具身→flywheel;agent 训练→v5(回退为产品页之一);
- **装订规则**(生态律):各框材料走信箱总线提交,平台统一视觉+上线;单框不得占整站。

## 四、视觉基调

白底/单主色(--accent #0a5ad6)/系统字体/1px 分隔线;结构优先于装饰;移动端单列自适应(已内建)。
