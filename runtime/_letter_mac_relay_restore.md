[任务单 REV7 最终版] 中转站架构恢复——api.chunxiao.wang 全变体 200,CC 已切回,1M 长窗恢复

Mac compass:

终局配置(compass 顾问 11/1 凌晨执行,CC 快测"通"):
- Mac settings:`ANTHROPIC_BASE_URL=https://api.chunxiao.wang` + relay token(sk-5G9Y)+ 模型四键=glm-5.3[1M]/glm-5.3-flash[1M]/MiniMax-M3[1M]/k3-256k
- 实弹:自建中转站入口四模型全 200;**CC 侧模型名保留 [1M] 后缀=1M 长窗声明恢复**(new-api 渠道 model_mapping 自动转裸名给上游 newapi.07211996.xyz)
- 此前 REV5 的"CC 直连第三方中转+裸名"过渡方案作废

## 故障全链归档(最终版,替代之前所有 REV 的归因段)
1. 官方 zhipu key 失效(#1 自动禁用)→ glm 失去主力
2. 切第三方中转时,渠道被配在 manus 的 new-api 上且三层错误叠加:出口 IP 被上游 CF/nginx 拦(后经用户放行解除)+ key 配错(sk-YcY6tNT/sk-tU6bGHC 非 63fc4b 亦非 sk-yfL1QR)+ 模型变体在 abilities 表缺行/被禁
3. new-api SQL 直修的三层坑:channels.models 改了不生效(路由走 abilities 表)/channels.status 与 abilities.enabled 必须同步/改完需重启容器刷缓存
4. CC 对错误响应应激 compact = thrashing 循环;CC CLI/happy 透传均无责

## 状态
- 自建中转站(api.chunxiao.wang):✅ 恢复,四模型全 200
- Mac CC:✅ 已切回,快测通,1M 长窗恢复
- P0/P1 认知层任务单(24659/24671/L123 24793):照旧执行
- 悬件:#1 智谱官方 key 修复后可回主力(现第三方中转为主 glm 源,5h 窗口限速)

—— compass 只读顾问 · trace=relay-restore-1101
