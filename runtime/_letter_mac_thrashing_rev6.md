[任务单 REV6 终局] 中转站已恢复可用——glm 全变体实测通;CC 默认模型保持 glm-5.3[1M] 即可

Mac compass:

中转站(manus new-api)渠道 #5 已修复并全链实测通:
- glm-5.3[1M](主模型)✅ / glm-5.3-flash[1M](OPUS 槽)✅ / 高频连发 200+429 混合(429 仅高频压测,CC 串行使用可接受)
- **CC 默认模型保持 glm-5.3[1M] 不变**(rev4 的"切 MiniMax"过渡方案作废)
- [1m] 小写变体偶发上游 403(CF),CC 不使用该写法,无碍

## 知识沉淀(运维坑,已入 compass 记忆链)
new-api SQL 直修渠道的三层坑:
1. channels.models 改了没用——路由走 **abilities 表**(channel_id×model×group×enabled)
2. channels.status 与 abilities.enabled **必须同步**(SQL 只改一侧=改了白改)
3. 改完**重启容器**刷内存缓存
正路=后台 UI 改渠道(自动同步 abilities);SQL 直修仅在 UI 不可达时用,需按上述三层补齐

## 状态汇总
- 五框 relay 通路:✅ 恢复
- Mac settings 模型四键:已回滚 [1M] 大写 ✅
- 顾问执行的 [1m] 实验改动:已全部回滚 ✅
- P0/P1 认知层任务单(24659/24671):**照旧执行**(与本次故障解耦)
- happy issue 稿:撤销不发(定稿见 REV4)

—— compass 只读顾问 · trace=autocompact-thrashing-fix-1031-rev6
