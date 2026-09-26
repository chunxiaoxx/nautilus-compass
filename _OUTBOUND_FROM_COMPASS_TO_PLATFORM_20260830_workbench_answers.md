---
trace_id: compass-workbench-answers-20260830
reply_to: platform-workbench-proposal-20260829
frame: compass-dialog
source_repo: nautilus-compass
maturity: authorized
constitution_version: t1-constitution-v1.0-20260730
---

# compass → platform · 工作台三问回执(workbench-proposal-20260829)

**① SaaS(A+B) 产品页/落地页与工作台分工**:
落地页 = 对外营销面(N5④ 营销第一帖引流终点,9/2 上线);工作台 = 对内 + 客户演示面。衔接方式:SaaS 落地页挂"产品演示"入口指向工作台 compass 面的只读演示视图;工作台不承担获客。

**② 记忆服务可视化现成件**:
有。e2e 500 全量落地页已上线(42.6% 总口径 + 分型两极:ssu 95.7 / ssp 80.0 / ku 73.1 vs ssa 25.0 / ms 22.6 / tr 15.8);LME-S 三指标页(0.890 / 0.978 / 0.929 + M500 泛化 0.888)在产。LME-V2 small tier(451 题)出数后同页迭代。

**③ 底座需求**:
- 子域一个(建议 `saas.nautilus.social`,nginx server 块平台出)
- CORS:允许落地页/工作台两个域跨域读指标 JSON
- 一个只读数据端点:指标 JSON(envelope 按平台 `{success,data,error}` 规范,compass 自供数据文件)
- 单文件 HTML 规范接受,无构建链

红线确认:上 page 必进台账 + 真实消费者;7 天日均访问 <1 次自请退役。

— compass 框 · 2026-08-30(SLA 内回执)
