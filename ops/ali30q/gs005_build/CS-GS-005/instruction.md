# CS-GS-005 · env 静默降级(降级必须可见)

## 背景

`repo/v5_bridge/helix_bridge.py` 是 agent 主进程写入链上账(helix blocks)的桥接层,
逐字提取自生产代码 `nautilus_v5/super_agent.py:377-412` 与消费侧
`nautilus_v5/daemon.py:858-878`(切段边界以 `# ---8<---` 标注)。

该桥接层引用的存储实现 `nautilus_core.helix_chain`(`PgStorage` /
`HelixChain.a_close_breath_pair`)在本仓库中**并不存在**——这正是历史上真实发生的
事故形态:桥接层 2026-05-18 上线,所引用的实现迟至 10/4 才被补入(commit
`defb148c6`「补缺失件」),期间 110+ 天每一次链上账都在静默丢失。

## 你的任务

修复 `repo/v5_bridge/`(可新增文件,但**不得删除或改写源切段中标注为真实代码的
控制流语义**),使得:

1. **初始化降级必须结构化可见**:存储不可用(依赖缺失 / DSN 未配置 / 连接失败)时,
   除日志外必须留下机器可读的降级报告(如宿主对象上的 `degraded` 标志与
   `degradation_report` 结构)。只打一行 warning 然后继续运行,视为未修复。
2. **消费侧不得静默吞错**:链不可用时,`close_breath_pair` 必须显式跳过并留痕
   (降级计数 + 可判读的返回结构,声明本次未封链及原因);不得裸调用后让
   `AttributeError` 被 `except Exception` 吞掉、返回 `None` 了事。
3. **降级不得伪装主通路**:降级运行时,链后端标记必须如实(如
   `chain_backend = "file_fallback"`);只有真实接通才可标记为主通路(`"pg"`)。

## 约束

- 修复不得引入网络调用;无 PG 的环境下所有测试必须可独立运行。
- `v5_bridge` 对外接口(`BridgeConfig` / `HelixBridgeHost` / `close_breath_pair`
  签名)保持兼容。
- 评测器以 `tests/` 下 UT 为准,三条 UT 全部锚定「静默降级」缺陷族。

## 验收

在修复后的仓库上运行 UT 全部通过;原始(未修复)仓库上全部失败。
