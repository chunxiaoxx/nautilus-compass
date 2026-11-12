[任务单 REV5 终版] thrashing/relay 故障终局——CC 已切直连中转(家宽出口)+裸名 glm-5.3,快测通

Mac compass:

REV4 再勘正。终局配置与事实:

## 真相(三层错误叠加→今天爆发)
1. 官方 zhipu key 失效(#1 瘫痪)
2. 切换第三方中转 newapi.07211996.xyz 时,渠道被配在 **manus 的 new-api** 上——**manus 机房出口 IP 被中转的 CF/nginx 拦截(403/1010)**,所有经 manus 的转发全灭(502/429/503 混杂)
3. 渠道 key 还配错(sk-YcY6tNT/sk-tU6bGHC 均非正确 key)
→ CC 对错误响应的应激 compact = thrashing 循环。CC CLI/happy 透传均无责。

## 终局配置(10-31 深夜已生效,CC 快测"通")
- Mac settings.json:`ANTHROPIC_BASE_URL=https://newapi.07211996.xyz` + 正确 key + **模型四键=裸名 `glm-5.3`**(家宽出口直连,实测 200)
- skills 43→8;模型别名 *_MODEL_NAME 键已清

## 已知限制与后续
1. **令牌模型权限**:中转令牌仅授权裸名 `glm-5.3`;`[1M]`/flash/MiniMax/k3 变体均"无权访问"——若中转有管理权,给令牌加模型或建 `[1M]`→裸名映射,恢复 1M 长窗声明
2. 裸名无 [1M] 声明 → CC 按 200k 窗,长会话 ~180k compact 一次(单次可接受,非循环)
3. manus relay 的 glm 渠道(#4/#5):出口被拦,弃用留档;若中转白名单加 115.159.62.192 可复活(对方操作)
4. P0/P1 认知层任务单(24659/24671)照旧执行
5. thrashing 相关旧函(24674/24703/24717/24688/24760)中与 happy/CC 版本相关的结论作废,以本函为准

## 给用户的操作提示
- 正在用的循环态手机会话:弃用重开(交接文档已在 NAS)
- orgup 可开(五框走新通路)

—— compass 只读顾问 · trace=autocompact-thrashing-fix-1031-rev5
