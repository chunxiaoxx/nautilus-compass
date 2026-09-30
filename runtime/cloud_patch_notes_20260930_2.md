# 云 daemon 补丁备件(待部署窗口)· 2026-09-30 轮 3

## 补丁 A · status/ping 诊断通道豁免 in-flight 门(本地版已改,云端待窗口)
- 背景:冷启动风暴中业务 handler 全忙 → status 也被 P7 门拒绝("daemon overloaded")
  → 运维在风暴中失去观测能力(本轮实测:overload 时拿不到 RSS/P9 读数)
- 修法:overload 分支 MSG_PEEK 首行,`"status"`/`"ping"` 放行(只读不 encode 不占池)
- 状态:本地 ~/.claude/plugins/nautilus-compass/daemon.py 已改+compile 过;云端部署待
  风暴平息窗口(重启=又一轮冷启动,勿在风暴中叠加)

## 观察:冷启动风暴机制
- 触发链:重启 → 全客户端重试 → P9 全 miss → 每请求载入项目(BGE 冷嵌入慢)
  → 8 handler 全忙 → in-flight 32 满 → overload 拒绝 + RSS 峰值(并发载入叠加)
- 自限性:LRU 4 项目 warm 后 P9 命中率上升 → 风暴衰减
- 待验:7 分钟观察读数(后台任务 bvwvutw58)
