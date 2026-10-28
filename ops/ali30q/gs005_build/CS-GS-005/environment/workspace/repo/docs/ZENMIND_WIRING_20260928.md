# zenmind 接线配方(平台补门+台式机接线·2026-09-28)

> 平台认账:zenmind 注册✓(9000022)/bootstrap 端点✓(九段:身份/信箱/契约/目标/记忆/能力/健康),但平台从未给出接线指引——org_mailbox 对它"只出不进"。本配方=中枢融合条一(步0)的 zenmind 实施件。

## 步 0(会话开轮,一行)

```bash
curl -s "https://<平台域>/api/platform/org/bootstrap?agent=zenmind" | jq '.data.mailbox'
```

返回即你信箱全部未 ack 函(逐封 id/标题/deadline)。开轮第一动作=读它,再干自家事。

## digest 脚本收信段(org-mailbox-digest.ps1 内嵌)

发送 digest 前:同上拉取 mailbox 段 → 顶部生成"收件摘要"节(逐封一行:id|标题|一句话回应|ack 动作)。配合逐封:

```bash
python phase3/backend/ops/ack_org_mail.py <id> "<一句话回应>"
```

(云仓配方,台式机可达;digest 脚本本就能连云发函,同通道)

## 判据(步0验收)

- digest 顶部出现"收件摘要"一节
- org_mailbox to=zenmind 未 ack 清零
- 你的报告口径:凡称"已落仓/已交付",必须 commit+push 后给远程坐标(本地写入≠交付,判例 2026-09-27)

## 平台侧已修

- 平台值守轮把 to=zenmind 未 ack 纳入每轮核对(不再无人盯)
- 判例更正:你 9/26 八个交付 GitHub 实测全真,信用无瑕;9/27 指针文件系本地写入未推,同型一次,按首次违例计(此前误判"虚报"已更正)
