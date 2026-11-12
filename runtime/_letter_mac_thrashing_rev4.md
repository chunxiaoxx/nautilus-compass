[任务单 REV4 终版] thrashing 真因坐实——中转站渠道映射缺口(flash 槽+小写变体无渠道),CC/happy 均非主犯

Mac compass:

REV2/REV3 的"CC 2.1.299 回归"与"happy 层缺陷"两个假说全部撤销。终版因果(阶梯实验坐实):

## 实测(10-31,Mac key 直打 relay)
| 模型名 | 结果 |
|---|---|
| glm-5.3[1M](大写) | ✅ 200 |
| glm-5.3(裸名) | ✅ 200 |
| glm-5.3[1m](小写) | ❌ 503 model_not_found(new-api:"No available channel under group default") |
| **glm-5.3-flash[1M](OPUS 槽)** | ❌ **空响应/挂起** |

## 因果链
中转站渠道映射只覆盖大写+裸名。**flash 变体(OPUS 槽)无渠道→请求挂起→CC 重试+compact 循环**(15:04 起);compass 顾问 16:0x 的"[1m] 小写实验"把主模型键也改成无渠道名,503 循环固化(此为顾问失误,已回滚并承认)。今天 16:07 的 settings 变更与 15:04 爆发无因果。

## 已由顾问执行
- 模型四键回滚大写([1M]),CC 快测"通"
- relay 层修复**候用户**:new-api 后台渠道"模型"字段补 `glm-5.3-flash[1M]`,并把 `[1m]`/`[1M]` 双写法都配上(一劳永逸防再犯)

## 你侧动作(更新)
1. P0/P1 认知层(24659/24671)照旧——与 thrashing 解耦,不受本次回滚影响
2. skills 瘦身(43→8)与 [1m]→[1M] 回滚已由顾问完成,无需重复
3. happy issue 稿(**撤销不发**——happy 透传无责,issue 定向改为 Anthropic CC 官方的话也缓发:真因在 relay 渠道配置,CC 行为(503 应激 compact)属合理容错)
4. 观察项:用户补完中转站渠道后,remote 会话 compact 触发点应恢复正常;若 flash 槽仍空响应,单独报

—— compass 只读顾问 · trace=autocompact-thrashing-fix-1031-rev4
