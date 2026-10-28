# 组织工作台(org workbench)· 产品化方案 v0

trace_id: org-workbench-design-20260829
frame: platform-dialog(主导)· 用户指令:把成熟功能和 PMF 产品做成图形化工作台,投入使用产生价值

## 0. 原则(从历史教训来)

1. **自己先用**:工作台 v0 的第一用户是四框+用户本人(每天看的驾驶舱)——fde.nautilus.social 零流量教训:没有真实消费者的页面不叫产品
2. **API 已全在,只缺脸**:convergence/bootstrap/mailbox/supervisor/dashboard.py 全是现成端点——v0 是"拼装+图形化",零新后端
3. **一框一面,平台打底**:平台做组织驾驶舱(示范+底座),各框认领自己的产品面

## 1. 工作台 v0 · 组织驾驶舱(平台,本周)

- **形态**:单文件 HTML(无构建,轮询 API),部署 `org.nautilus.social`(nginx 加 server 块)
- **四块**:
  - 记分牌:五数字(convergence)+verified 曲线(supervisor report jsonl 历史)
  - 组织 mailbox:四框未读/回执/deadline 倒计时(牙齿联动可视化)
  - 资产台账:八节能力索引(🟢🟡⚪ 三态,消费计数)
  - 生产活体:executor verdict 流/agent 能力榜(9010 等)
- **判据(预注册)**:上线后 7 天内四框+用户日均访问 ≥1 次(自己用起来);死页面=下线

## 2. 产品化候选矩阵(引导各框认领)

| 框 | 成熟功能 | 图形化产品 | PMF 证据 | 主导 |
|---|---|---|---|---|
| compass | 记忆服务(LME-S 0.89/0.98/0.93) | **SaaS(A+B 组合,已开枪)**+落地页 | 基准碾压+workbuddy 首调 | compass(已认领) |
| 飞轮 | 数据管道+交付线(81pp n=2 复核中) | **交付看板**(国曙 23 题/QC/结算)+管道进度页 | 甲方真实交付 | 飞轮 |
| V5 | executor 生产+自愈(verified 538 陡涨) | 并入组织驾驶舱生产块(不单独做) | verdict 曲线 | 平台代做 |
| 平台 | 六服务底座 | **组织驾驶舱 v0(先做=示范)** | 四框日均使用 | 平台 |

## 3. 底座规范(平台提供给各框)

- 部署位:nautilus.social 子域(nginx server 块模板平台出)
- API:统一 envelope `{success,data,error}`;CORS 按子域开
- 设计:单文件 HTML 优先(无构建链);图表用轻量(内联 SVG/极简)
- 登记红线:每个页面上线必须进台账行+真实消费者(§⓪-E DoD)——零流量页面按遗忘环退役

## 4. 排序

1. **本周**:驾驶舱 v0(平台,示范)+倡议函(带 v0 实物,比空函有力)
2. **随 compass 节奏**:SaaS 产品页(compass 主导,平台供 API/CORS/部署)
3. **飞轮 seed2 终裁后**:交付看板(有 81pp n=2 数据可展示)
4. /var/www 坟场(2 月旧项目数百报告+5 子站遗迹)→ §⓪-E 遗忘环专项(归档,另案)

## 维护
- 各框认领/新增页面 → 更新候选矩阵+台账;v0 上线后本文件随验收更新
