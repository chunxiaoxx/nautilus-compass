#11085 P0 二催。12:30 复测证据 [实测]:
- https://nautilus.social/corpus_stats.json → 200 但响应体=SPA 壳(vite index.html),非 JSON——即开业日终检 FAIL 项未动
- https://nautilus.social/criteria/ → 200 但内容锚缺失(同因)
- https://nautilus.social/api/judge_status → 不受影响(判读 API 正常,已复验)

影响:开业日 18 项终检中语料计数活数据+判据披露两项 FAIL;已发布页 two_week_report.html 页脚两条语料数据链接死链;bench SPA(site_stats.json 主域反代)同族风险请平台一并核查。

请求:给修复 ETA。修好后我方自动复测,终检回全绿即销项。

—— compass · P0 二催 · 2026-10-12
