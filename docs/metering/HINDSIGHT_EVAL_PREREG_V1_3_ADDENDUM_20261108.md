# Hindsight 独立评测 · 预注册判据 V1.3 附录(2026-11-08)

> 车道终局增补(仍属跑批中断续行——500 题未出任何评分读数,judge 调用零次发出)。
> V1/V1.1/V1.2 其余条款全部不变;本附录只定 LLM 车道。

## 车道(用户 11/8 指定自建中转站)

| 用途 | 车道 | 端点 | 状态 |
|---|---|---|---|
| hindsight 服务端提取 | **glm-5.3-flash** | api.chunxiao.wang(自建中转) | 周限额已重置·实测通 |
| subject 答题 | **kimi-k3 (k3)** | api.chunxiao.wang | 实测通 |
| judge 判卷 | **claude-opus-5-5** | code.ai80.vip(code80 渠道) | 实测通 |

- **judge≠subject 分离**:较参照跑(DeepSeek V3.2 self-judge)为**更严**方向
  (消除同厂自判偏置),符合"判据只许更严"。
- 前史:qwen token-plan 月额度耗尽(11/18 重置);MiniMax token-plan 5h 滚动窗口
  (蚂蚁搬家不可控)——均如实记录于 run log,数据(31+ bank·MiniMax 提取)沿用,
  混合提取配置(31 MiniMax + 其余 glm)在报告披露。

## 冻结面增量

- tests/eval_hindsight_arm.py 车道默认改 V1.3(sha16 见 freeze 档更新)
- 中转 key 经 env 注入(RELAY_API_KEY/CODE80_API_KEY·源自 v5 .env,不落仓)

## 对比口径(最终)

- hindsight 臂 = kimi-k3 subject + opus judge + glm 提取
- 参照 56.6% = DeepSeek V3.2 self-judge —— **跨模型对比,报告显式标注**
