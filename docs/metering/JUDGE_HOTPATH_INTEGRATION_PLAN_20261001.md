# 判分器热路径接入清单(2026-10-01 · 装前申报 §1)

> 依据:用户 9/30 批「装记忆写入热路径评估,装前另行申报」;热路径实测 P50=30ms/P95=42ms/吞吐 118 条/s(runtime/loop/queue.md R4)。
> 本档=接入点清单与设计原则;影子评估判据另档,期满呈用户。

## 一 · 写入热路径的三个入口(daemon.py 实测)

| 入口 | 位置 | 流量 | 判分价值 |
|---|---|---|---|
| ingest action | handle_ingest(L1519;平台 agent V5/V6/V7 投喂) | 中 | **首选试点**:入口单一,返回值可带 verdict |
| session_writer | 会话结束摘要写入 | 高 | 二期(量大,判分收益=会话质量标记) |
| hook 写入门 | PostToolUse/SessionEnd | 零散 | 不接(信噪比低) |

## 二 · 接入设计(第一版=影子模式)

1. **只标记不拦截**:ingest 返回值加 `verdict: {label, confidence}` 字段+落盘到 verdict log(jsonl,一行一判定,含输入 hash)——不改任何入库行为
2. **判分器独立进程**(端口 9879):
   - 云端 daemon 刚做完内存根治,判分器(1.7B 底模 ~4G)绝不内嵌——独立进程,OOM 隔离,daemon 出口走 localhost TCP(同 9876 协议族)
   - 本地(Windows)同款:独立进程+惰性加载(首次判定才载模型)
3. **特征管道同源**:sample_text() 与 P2v2 训练同款(无作弊通道版);输入=text+tags+source
4. **三态语义**(U 态是特性):pass=正常/fail=标记可疑(如空文/复读/注入痕)/U=证据不足进待人工池

## 三 · 影子评估判据(草案,申报用)

| # | 判据 | 线 |
|---|---|---|
| S1 | 影子期 | 7 天,零行为变更 |
| S2 | 延迟 | ingest 端到端 P95 增量 <100ms |
| S3 | 可用性 | 判分器进程存活率 ≥99%(独立守护) |
| S4 | 读数 | 三态分布+fail/U 抽样 10% 人工复核一致率报告 |
| S5 | 关闸 | 任何生产影响(ingest 失败率上升)=立即摘除 |

## 四 · 装机前置(等申报批后)

- [ ] 判分器服务脚本 judge_server.py(9879,LoRA adapter 加载+三态 API)
- [ ] handle_ingest 出口加 verdict 钩子(env 开关 COMPASS_JUDGE_SHADOW=1)
- [ ] verdict log 轮转+周报脚本
- [ ] 云端部署窗口(daemon v3.3 观察期后,避免连续变更)
