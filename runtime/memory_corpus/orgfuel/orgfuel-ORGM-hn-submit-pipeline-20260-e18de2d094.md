---
name: orgfuel-ORGM-hn-submit-pipeline-20260-e18de2d094
description: "--- name: hn-submit-pipeline-20260910 description: HN 全 curl"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-hn-submit-pipeline-20260
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: hn-submit-pipeline-20260910
description: HN 全 curl 管道配方(登录/提交/评论/确认流)+ 首帖秒 flag 的处置选项
metadata: 
  node_type: memory
  type: reference
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  modified: 2026-09-10T11:30:14.646Z
fact_status: inferred
---

# HN 全 curl 管道配方(2026-09-10 首跑实测)

- 登录:`POST /login` 带 `acct=<username>&pw=<密码>&goto=news`(只认 username 不认 email;302=成功,失败 200+Bad login);cookie 名 `user`(HttpOnly,10 年期)
- 提交:`GET /submit` 解析 `fnid` → `POST /r`(fnid+fnop=submit-page+title+url/text);URL 帖若被 site 风控拦→报「your account isn't able to submit this site」(零历史账号第一帖提自家域=标准待遇),改 text post 通常直接 302 newest=发布成功
- 评论:item 页无内嵌表单;`POST /comment`(parent+text+goto)→ 首评常触发 `302 /x?fnid=...&fnop=commconfirm` 二次确认;新账号可能直接「Sorry, you can't comment here」
- 登录态验证:GET /news 看 `user?id=<nam
