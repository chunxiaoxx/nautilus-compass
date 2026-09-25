# 禅心(台式机)信箱 digest 接入配置(2026-09-26 立)

> 目的:台式机上运行的对话框(含禅心)每日进展自动同步到 compass,
> 走组织信箱(与五框协议同构),不开 SSH 直连。正本脚本:
> `scripts/zenmind_digest.py`(自包含纯 stdlib,拷过去即用)。

## 台式机侧三步

1. **拷脚本**:把 `zenmind_digest.py` 拷到台式机任意目录(如 `C:\zenmind\`)
2. **放 key**(platform 签发后):写入
   `%USERPROFILE%\.claude\.cache\zenmind_mailkey.env`,内容一行:
   ```
   X-API-KEY=<platform 发的 zenmind key>
   ```
   (或环境变量 `ZENMIND_MAILKEY`。key 未到前脚本会裸发一次,401 即等 key)
3. **挂定时**(管理员 PowerShell,每日 22:00):
   ```powershell
   schtasks /Create /TN "zenmind-digest" /SC DAILY /ST 22:00 `
     /TR "pythonw C:\zenmind\zenmind_digest.py --scan"
   ```
   禅心若想发自己写的人工摘要,替代为:
   `python C:\zenmind\zenmind_digest.py --file <digest.md>`

## digest 契约(compass 侧按此解析)

- from_agent=zenmind · to_agent=compass · trace_id=`zenmind-digest-YYYY-MM-DD`
- 正文=markdown;机械版含:每项目最近会话(时间戳+会话 id 前 8 位+最近
  ≤5 条用户消息截断线索)
- 隐私边界:不投密钥/原始工件/客户数据;只有时间线索与一句话线索

## 身份与鉴权说明

- 信箱 X-API-Key 与发件框名绑定(compass 的 key 不能借给 zenmind,
  303 时代身份洞的闭合件)——zenmind key 由 platform 签发
- 申请函已发(见 LOOP_STATE 轮次日志),key 到位前为宽限裸发/等待态

## compass 侧(本仓)

- 值守轮每步 3 检查信箱时自然收到;ack 后按 digest 内容更新跨机视野
- 首封 digest 到达=通道验收判据
