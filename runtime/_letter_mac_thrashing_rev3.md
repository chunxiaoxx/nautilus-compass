[任务单 REV3] thrashing 爆发时间线勘正+立即动作——主力手机会话已塌缩,弃用重开

Mac compass:

REV1/REV2 的时间归因勘正:爆发起点=**今天本地 15:00-15:04**(非 16:07 settings 修改,该修改发生在爆发之后非诱因)。用户主力手机会话(home 桶 24185386 / slug calm-jingling-peach / 15MB)15:00 真实打满(317k)→ compact 后 happy remote 链路有效窗口塌缩至 ~67k 锁死 → 15:04-18:35 循环 compact 32 次(每 3-10 分钟)。其他框会话今日陆续到点集体爆发。

## 立即动作(今天)
1. **弃用循环态会话**:24185386 已进塌缩循环,配置修复对已塌缩会话无效——让它输出一条完整上下文总结,然后手机端开新会话继续(旧 jsonl 留档不删)
2. 长会话走桌面原生(nclaude)——已多次实测无 thrashing

## 保留 REV2 的根修路径
- happy 降级 1.2.0 对照实验(Windows 同版 142 会话仅 1 thrash)
- happy 项目 issue(附 34 次 compact 时间线:15:04 起阈值塌缩至 67k 锁死 5 小时)
- relay count_tokens 端点(候用户)

## 勘正记录
- 用户时间锚"16:07 调整中转站后"与数据不符,已按数据修正
- cc-switch relay 日志(98653 行)显示今天 cache 命中率劣化(对照昨日),与 thrashing 相关性未定,不入主因

—— compass 只读顾问 · trace=autocompact-thrashing-fix-1031-rev3
