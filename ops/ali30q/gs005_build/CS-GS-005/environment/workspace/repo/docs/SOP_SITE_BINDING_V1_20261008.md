# SOP · 平台装订员(网站生产系统岗位规范 V1)

> 总动员令第一份岗位实物(2026-10-08 00:5x)。岗位归属:platform(装订权);规范对齐:soul 治理规范库(候其 SOP 正本库合流)。
> 装订权≠内容权(soul 治理条款):平台持有挂载/视觉统一/验收权;各框保留内容正本权与撤回权。

## 职责

接收各框产品页材料(信箱总线)→装订→上站→验收→登记→回执。全链 agent 可执行(自研 agent 职能化首岗)。

## 流程(六步,每步带判据)

1. **收件**:材料经 org_mailbox 提交(格式=md 正本+仓@commit 坐标+版本号+目标位置);验收:坐标可寻址(判不可寻址前必穷尽函内坐标)。
2. **审材**:内容正本权在提交框;平台只查①坐标真实②版本与正本一致③无未批对外承诺(SLA 数字/收款承诺=用户批)。
3. **装订**:md→HTML 走 flywheel 渲染器(自动化,双正本滞后检测);装订版带版本标识+底稿来源(参照 index_v2.html v2.0-alpha 注释式)。
4. **上站**:部署窗执行(22:00-07:30 禁);nginx 配置+证书(acme.sh 禁 certbot;sites-enabled 禁 .bak);push+restart+curl 三验。
5. **验收**:外网 https 200+关键内容标记命中+md5 与云侧一致(三验);版本标识核对;变更回函附 md5。
6. **登记**:台账(ORG_PRODUCTIZATION_LEDGER)记一行(页名/版本/坐标/验收读数/时间)+回执提交框。

## 变更与冲突

- 任何页变更走判例台账(BYZ 判例模式);两外壳勘误→页面同步(双向匹配表,compass #10438 建议)。
- 决策卡结论与先行实现冲突→按结论回退(已书面承诺 soul,#10454)。
- 双修禁令:一页一 owner,他框代修须平台登记(leaderboard.html 先例)。

## 验收探针模板(装订员日常)

```bash
curl -sL -m 15 <url> -o /tmp/live.html -w "%{http_code} %{size_download}\n"  # 外网
md5sum /tmp/live.html; ssh cloud 'md5sum /var/www/nautilus/current/<file>'   # 云侧比对
grep -o -m3 "<版本标识>|<关键内容标记>" /tmp/live.html                       # 内容命中
```

## 岗位矩阵(职能化 roadmap,候各框 SOP 合流)

| 岗位 | 职能 | 归属 | 状态 |
|---|---|---|---|
| 装订员 | 本 SOP | platform | V1 本文 |
| 站长 | 门面整体/IA/导航/版本 | platform | 候 RFC 结论 |
| 验收员 | 独立验收(非装订人自验) | compass(第三方) | 候 SOP |
| 值守员 | 死线红灯/巡检/催办 | platform loop | 在役(loop cron) |
| 规范库 | SOP 正本治理 | soul | 候其出 |
