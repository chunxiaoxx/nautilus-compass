# 全自动多平台发布器架构案(2026-10-01 · 用户令+组织六点令「外发全自动」)

> 目标:Reddit/知乎/Discord/X 等**零人工**发布,可复用可审计。
> 原则:每平台走**官方/正式通道优先**,CDP 浏览器自动化只作无 API 平台的兜底;凭证集中管理;发布全程留痕入台账。

## 一 · 现状盘点(实测)

| 平台 | 现役资产 | 卡点 | 正道 |
|---|---|---|---|
| X | x_post.py(9226 CDP,已修 Inline 钮) | 登录态依赖浏览器 | ✅ 可用;可选升 X API($100/m 基础档写帖,**不划算,CDP 够用**) |
| Reddit | 稿备+CDP 死通道(shadow DOM/busy) | 浏览器自动化脆 | **PRAW+Script App OAuth**(官方免费):reddit.com/prefs/apps 建 script 型 app→client_id/secret+账号→全自动发帖/评论/读信 |
| 知乎 | 9225 键盘管道(dry-run 18/18) | 403 复验中 | 无官方 API→CDP 兜底维持 |
| Discord | 9224 CDP 配方(9/27) | — | **Webhook 最优**:频道 webhook URL 一行 curl,零登录零浏览器 |
| dev.to | API key 在仓 | 平台衰退(已放弃) | — |
| HN | curl 管道 | 需养号 | 维持 |
| 广场 | X-Agent-Key API ✅ | — | ✅ 已全自动(今天 id=27 实证) |

## 二 · 统一发布器设计(pub.py)

```
tools/publisher/
  core.py        # publish(platform, content, opts) -> receipt
  adapters/
    x_cdp.py     # 现 x_post.py 重构并入
    reddit_praw.py   # PRAW adapter(新,正道)
    discord_webhook.py  # requests POST(新,最简)
    zhihu_cdp.py # 9225 管道并入
    square_api.py   # X-Agent-Key(已在)
  creds/         # 各平台凭证(env 文件,.cache 不入仓)
  receipts/      # 每次发布 JSON 回执(platform/url/ts/content_sha)→ 周汇入 OUTREACH_LEDGER
```

- **内容适配层**:一稿多格式(markdown 主稿→X 截断版/Reddit 全文/知乎富文本/Discord embed)
- **审计链**:发布前 content_sha 入台账(发什么有据),回执带 URL(发到了有证)——与 B 级外发制(1840)对齐:发布=已批内容的执行动作
- **失败语义**:回执记 error+可重试;连续 2 失败升报 LOOP 轮

## 三 · 落地序(今天起)

1. **Discord webhook**(30min,最简先行):拿频道 webhook URL→adapter 上线
2. **Reddit PRAW**(1h):需用户一次性操作——**reddit.com/prefs/apps → create app → script 类型 → 填名称+redirect(任意 http://localhost)→ 得 client_id/secret 给我**(此后永久自动)
3. **pub.py core+内容适配**(1h):X/广场并入统一入口
4. **知乎 403 复验+CDP 管道并入**(已有基础)
5. receipts→台账周汇自动化

## 四 · 与组织线的挂接

- 六点令「外发全自动」首验靶=今晚 BC1 知乎发布(B 级卡已批,21:00 窗,用 9225 管道自动发=首验)
- Muse/Manus 机制调研(与平台合做)→ 对标后补差距分析
- 主线三:发布器=「对外组织化」的基础设施件,署名规范落地后全平台统一带组织背书行
