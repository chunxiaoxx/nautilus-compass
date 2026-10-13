---
name: orgfuel-ORGM-ad1abe07a39d34f6-23269f63c4
description: "记忆条目 hn-submit-pipeline-20260910.md # HN 全 curl 管道配方(2026-09"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-ad1abe07a39d34f6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 hn-submit-pipeline-20260910.md
# HN 全 curl 管道配方(2026-09-10 首跑实测)

- 登录:`POST /login` 带 `acct=<username>&pw=<密码>&goto=news`(只认 username 不认 email;302=成功,失败 200+Bad login);cookie 名 `user`(HttpOnly,10 年期)
- 提交:`GET /submit` 解析 `fnid` → `POST /r`(fnid+fnop=submit-page+title+url/text);URL 帖若被 site 风控拦→报「your account isn't able to submit this site」(零历史账号第一帖提自家域=标准待遇),改 text post 通常直接 302 newest=发布成功
- 评论:item 页无内嵌表单;`POST /comment`(parent+text+goto)→ 首评常触发 `302 /x?fnid=...&fnop=commconfirm` 二次确认;新账号可能直接「Sorry, you can't comment here」
- 登录态验证:GET /news 看 `user?id=<name>`+logout;flagged 帖匿名访问 fatitem 为空(对外不可见)
- Algolia 查提交史/dup:`hn.algolia.com/api/v1/search_by_date?tags=story,author_<name>`(curl schannel 吊销检查 offline 时用 python urllib)

# 首帖秒 flag 事故(2026-09-10)

item?id=49641875(text post 版)发
