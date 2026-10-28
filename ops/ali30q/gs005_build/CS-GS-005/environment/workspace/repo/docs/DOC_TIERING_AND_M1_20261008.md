# 文档分级令执行清单(用户裁 2026-10-08 深夜:信任面公开+全文登录)+M1 提前

## 一、分级清单(公开/登录)

**公开(信任建立面,获客钩子)**:首页/榜单/判据页/L2 样例/intake/客户门户/status/registry/developers/营销摘要(白皮书+BP 各一页 public brief)
**登录后(全文与数据)**:白皮书全文/BP 全文/数据页(S 线产品详页)/内部运营页

## 二、M1 身份层(提前至 10/11 前,平台域)

- POST /identity/request-code:邮箱→6 位码(Gmail 发送+DB 留痕,10 分钟有效)
- POST /identity/verify:邮箱+码→JWT(hs256,7 天)
- GET /identity/whoami:JWT→身份(subject/type)
- 各框接入:带令牌访问登录面;平台 verify 端点验签

## 三、分工(宪章 V1 不变)

平台=注册/登录/令牌/验签;各框=自家登录面接入+框内权限映射。
