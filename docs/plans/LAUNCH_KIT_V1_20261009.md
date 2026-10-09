# 开业日公告物料 v1(10/12 · 判分 API 公告+当日 checklist)

> R443 备料 · 10/11 终检正日后启用 · 判据:所有数字/链接均为在档实锚,发出前过一遍终检 13 项

## 一、判分 API 公告文(主站口径,中文)

---

**Nautilus Compass 判分 API 开放 · 判读永久免费**

AI 评测结果谁说了算?我们给出第三种答案:不问厂商,不问社群,问**可复算的证据链**。

自 2026-10-12 起,Nautilus Compass 独立判卷机构面向公众开放:

**已上线能力(全部免费):**
- **判读状态 API**:`GET https://nautilus.social/api/judge_status?id=<card_id>`——每张判读卡的判定/证据链/流程时间线/判据 sha16,机器可读;
- **免费判读入口**:提交评测产物走 [intake](https://nautilus.social/intake.html)(L1 机器判读/L2 深度报告/L3 定制,SLA 明示);
- **判据预注册披露**:所有判据先冻结后判读([criteria](https://nautilus.social/criteria/)),sha 锚定不可事后改;
- **公开榜单**:首榜 Round1 已定版(A 26.7% / B 16.7%,判据+复算全锚);
- **判分模型**:NACRE judge v1 权重公开([HF nautilus-compass/nacre-judge-v1],三态 88.51%,fp16 部署纪律在档);
- **独立复算**:任何判定可请求第三方复算,复算免费。

**定价边界(一句话):判读永久免费;装订收费**——深度报告/判例集/协议植入,只做判后事。

**已走通的首例链路**:intake → 判据预注册 → 三态判读 → delivered → 第三方独立复现(平台复现首卡 nautilus-l1-0002 全锚命中)。

---

## 二、开业日 checklist(10/12 当日时序)

| 时点 | 件 | 责任 | 判据 |
|---|---|---|---|
| 上午 | 终检 13 项复跑(final_check.py)| compass | 13/13 PASS;data 站项按 10867 回复处置 |
| 14:00 | XERJ Release 跟进(maintainer 窗)| compass | pack 挂出即发 Ivan 跟进函(带链接) |
| 18:00 | 平台白窗部署验收配合(提前 2h 函告窗)| platform 主/compass 验 | 401 才算过;验收单全量 |
| 20:30 | 三链接 200 终验(intake/criteria/leaderboard)+API 探活 | compass | 全 200+judge_status 返回 ok:true |
| 21:00 | PRECOR 博客首发(候署名+投递拍板 R374)| **候用户** | 拍板未到则顺延,不空发 |
| 21:05 | 判分 API 公告(本文 §一)随博客链发出 | compass | 公告内 6 链接全 200 |
| 22:00 | 回音巡检(评论/函/issue 三通道)| compass | 有音即回,48h 纪律 |

## 三、候拍板清单(开业前唯一阻塞)

1. **PRECOR 署名+投递两拍板**(R374 决策卡已备三天)——10/11 前定,博客 21:00 档依赖此件;
2. Einsia 首触函(开业三链接齐后发,48h 窗纪律)。

## 四、证据层

- 公告文数字:全部引自在档实锚(88.51%=P2 三门全绿档;26.7/16.7=Round1 定版档;首例复现=10727 确认)[实测];
- API 端点存活:judge_status/intake/criteria 本轮 curl 200 [实测](10/9 23:1x);
- checklist 时序:[推断](基于交接档+10878 部署窗承诺,upgrade_path=10/11 终检后按实际微调)。

—— compass · LAUNCH-KIT-V1 · R443 · 2026-10-09 深夜
