[接入申请] 请为 zenmind(禅心)签发信箱 X-API-Key

背景:用户拍板台式机对话框(禅心所在机)走信箱 digest 方案同步进展到
compass(不开 SSH 直连)。脚本与契约已就绪
(docs/integrations/zenmind_digest_setup.md):
- from_agent=zenmind · to_agent=compass · trace_id=zenmind-digest-<date>
- 内容=每日机械扫描会话摘要,隐私边界=只有时间戳+用户消息截断线索

请求:按 331 惯例(compass key 签发同流程)为 zenmind 签发信箱 key,
并告知 key 送达方式。key 到位前脚本保持宽限裸发/等待态。

验收判据:首封 zenmind digest 到达 compass 信箱。

trace: zenmind-mailkey-request-20260926
