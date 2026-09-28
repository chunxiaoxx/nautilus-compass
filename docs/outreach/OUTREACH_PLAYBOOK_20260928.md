# 外联运营手册 v1(2026-09-28 · agent 持续执行版)

> 用户令:对外外交外联要优化脚本和策划,让 agent 持续做。
> 本档=外联轮值的执行正本:渠道/节奏/话术/脚本坐标,agent 每轮照此取件。

## 一、渠道矩阵(全部实测验证过,含坑与脚本)

| 渠道 | 状态 | 脚本/配方 | 坑 |
|---|---|---|---|
| GitHub issue/PR | ✅ 最稳 | gh CLI 直发 | T1 教训:AI 腔被骂,话术见三原则 |
| Discord 普通频道 | ✅ | scripts/post_discord.py | Chrome154 配方 v3 在脚本头 |
| **Discord 论坛频道** | ✅(9/28 实战) | **scripts/discord_forum_post.py** | 七坑全录在脚本头(Shift+N/弹窗重渲染/trapClicks/标题框坐标) |
| 知乎专栏 | ✅ | scripts/cn_publisher.py | 四修已入库;AI works 提报差封面一步 |
| awesome 列表 | ✅ | gh PR | 双列表 fork 坑;先查列表生命体征 |
| dev.to | ⚠️ 有配方 | curl 浏览器 UA | 零流量三根因档在案;低优 |

**Chrome 常备**:9224=Discord(Temp profile+socks10808)/9225=知乎;发帖前
`curl localhost:<port>/json/version` 探活,死了按各脚本头配方拉起(登录态
随 profile 持久,重启免扫码)。

## 二、节奏(反剧场:每轮只一个外联动作)

- **每日配额**:1-2 个外联动作(发/回/盯),不批量轰炸(风控+人味)
- **D3 触达批次**:剩余 4 家,每周 2-3 家节奏,话术 v3(人味版,见下)
- **盯帖 SLA**:已上墙内容(Discord 主帖/follow-up/TypeSafe 背书信/
  GitHub issue)每轮值守巡检;有回复 **12h 内**回应;被删/被标记→停,话术回炉
- **新渠道开拓**:每周最多 1 家,先查生命体征(awesome 教训)再投

## 三、话术三原则(T1 之死与 T3/背书信之活换来的)

1. **人味优先**:像工程师聊天,不像文案;删掉所有"slop writing"式形容词
2. **技术钩子**:开头给具体数字/坑/实测(如背书信的 440.1x/64 calls),
   不给形容词
3. **免费价值先行**:先给(复算/mini 审计/体检报告),不索取;同行姿态
   credit 给足(TypeSafe 信=范本,runtime/typesafe_proof/discord_letter.txt)

## 四、agent 轮值动作表(照此取件,坐标即命令)

| 触发 | 动作 |
|---|---|
| 值守巡检 | cdp_tool.py lastid 读 9224 频道尾;gh issue list 各仓;有回复→12h SLA 内回 |
| D3 批次 | 从 c1_outreach 名单取下家→查仓库活性→gh issue 发(话术三原则) |
| 复算成果出 | 同类背书信模板(runtime/typesafe_proof/PUBLIC_LETTER_DRAFT.md)→对应社区发 |
| 中文稿/文章 | cn_publisher.py zhihu <md> --publish(发布=默认动作,不再等用户点) |
| 外联结果 | 全部落 LOOP_STATE T 表 + 工件(截图/直链),失败照记 |

## 五、当前外联面存量(2026-09-28)

- 已上墙:Discord 主帖+follow-up+**TypeSafe 背书信**(9/28,盯回应中)、
  知乎中文稿+AI works(95%)、awesome-jev 双 PR(merged)、NanoJev PR#12(open)
- 观察窗过:inbox-zero#3835/hono-jev#7(判静默归档)
- 等对方:ClawHub RFC(勿二催)、T3 甲方反应
- M1 仍=0:外联面持续供给曝光,转化杠杆=投流开户(用户件)

## 变更纪律
手册改动走 commit;新坑(渠道/UI 改版)当天回写脚本头注释,配方不散落会话。
