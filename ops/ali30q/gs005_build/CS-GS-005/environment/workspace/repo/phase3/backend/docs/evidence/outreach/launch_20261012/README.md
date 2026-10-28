# 10/12 榜单开业·作战总卡

> 北极星 L3 层首发动作。一切文案数字占位符 `{DATA_*}` 发布前必填(来源=compass 定版榜面,禁手估)。
> 身份口径(用户未拍前默认):x.com 主发=用户 Premium 个人号 @chunxiaoxx,文案署名 "Nautilus (an org of 8 AI agents)";若用户拍组织号,文案零改动换号发。

## 发布时刻表(北京时间)

| 时刻 | 动作 | 渠道 | 方式 |
|---|---|---|---|
| D-1(10/11) | 榜页终检+占位符全填+预发 dry-run | — | 平台 |
| D日 20:30 | x.com thread 首发(Premium 号,美东早 8:30 黄金档) | x.com | 自动 API 或作战卡粘贴 |
| D日 21:00 | discord(2-3 个 AI/agent 社区服务器) | discord | webhook 自动 |
| D日 21:30 | reddit r/LocalLLaMA | reddit | OAuth 自动或粘贴 |
| D日 22:00 | Show HN(周二上午美东=讨论高峰) | HN | 发帖器(凭据到即自动) |
| D日 22:30 | Dev.to 榜单解读文(关联 10/5 首文) | Dev.to | API 自动 |
| D+1 | 知乎想法+即刻(中文版) | 知乎/即刻 | 粘贴兜底 |

## 渠道×状态(2026-10-05 盘点)

| 渠道 | 通道 | 状态 |
|---|---|---|
| x.com | API v2(缺 X_API_BEARER)/作战卡 | **作战卡兜底就绪**,API 开通即全自动 |
| reddit | OAuth script(缺 4 件凭据) | 代码就绪,等用户建 app |
| discord | webhook(缺 URL) | 代码就绪,等用户建服务器给 webhook |
| HN | hn_post.py(缺 HN_ACCT/HN_PW) | 发帖器在仓,凭据挂账 |
| Dev.to | API | ✅ 已通(10/5 实测 201) |
| 知乎/即刻 | 无 API | 粘贴兜底 |

## 待用户凭据清单(给了即全自动)

1. reddit:https://www.reddit.com/prefs/apps 建 script app → REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET / REDDIT_USER / REDDIT_PASS
2. discord:任一服务器频道 → 整合→Webhook → DISCORD_WEBHOOK_URL
3. HN:HN_ACCT / HN_PW
4. x.com(可选):developer.x.com 建 app(免费层即可写)→ X_API_BEARER;不开就用作战卡粘贴(已预生成 x_post_card.md)

## 转化缺口(10/5 发现,发布前补)

- **无外部行动入口**:门户试金局卡的"判分服务"现链接到 GitHub 文档(正本无站页),外部读者看完榜单没有可提交首检的表单/邮箱。已补:榜页 CTA + footer 均挂 mailto **chunxiaoxx+external@gmail.com**(agent_mail.py 方案A Gmail 别名路由的对外公共别名,10/3 激活实测;主邮箱 chunxiaoxx@gmail.com,映射规则 `{local}+{agent}@gmail.com`,正本 v5 仓 tools/org_lib/agent_mail.py@dca9fbc3)。
- Dev.to 基线(10/5 12h):reactions 1 / comments 0(评论 API 拉不到,等用户贴);L2 基线自此起计。

## 发布前检查(死线 10/11 晚)

- [ ] 榜页 URL 可访问(外网 curl 200)
- [ ] 全部 {DATA_*} 已填,文件里 grep 无残留占位符
- [ ] 判据 sha16 与 compass 定版一致(d20d167f934af255 为期判据锚,榜页引用须逐字对表)
- [ ] 免费首检入口链接可点通
- [ ] x thread 逐条 ≤280 字符(超长会被 API 拒)

## 发布后读数(登记进 outreach_ledger.jsonl)

- +48h:各渠道 view/like/comment(回读 API:x 免 API 层手记/reddit OAuth 读/discord 手记/Dev.to API 自动)
- +7d:同口径复读+判分页访问增量+免费首检提交数(唯一转化硬读数)
