# 跑分测试全过程经验沉淀 · 2026-09-04

> 覆盖:LME-V2 线(8/30-9/4,451 题)+ e2e LongMemEval-S 线(500 题)+ cheap-tier 验证轮。
> 终局数字见 `docs/nautilusmem/SCOREBOARD.md`;本文只存方法论。

## 最终成绩(一句话版)

- LME-V2:d12 现役 **web 40.0% / ent 38.4%**(裸跑 19.6/12.8,约 3 倍);cheap-tier 挑战双域未超(36.3/36.5)→ 关闭
- e2e 500 题:42.6% → **75.4/81.6%**(摘要层,预注册门全过);检索 vs mem0 P@1 +11.6pt
- 速度:memory_query p95 0.34-0.80s vs 官方 LLM controller 26.9s(~80×)

## 八条教训(按通用性排序)

### 1 · 判官可信度先于成绩(本线 5 次 judge 事故总教训)

判官会把基础设施故障伪装成"系统答错":
- 401(key 变量名)→ LLM 判分行全零
- 网关断连 → 14.2% 题被记错题(e2e 线 5.4pt 失真)
- max_completion_tokens 被 reasoning 吃满 → 空响应系统性压分,且**集中在难题**(偏差非噪声)
- 修正后分数方向可以相反:web +3.3 / ent −1.9 / cheap-ent +5.7 —— 不重判=在发错误数字

**规则**:任何 LLM-judge 分数出门前必过判分卫生五件套:预注册锚 · judge 冒烟(函数调用级)· 双口径强制披露 · 重判工具随栈 · Wilson 置信区间。全文见 `docs/nautilusmem/PROTOCOL.md`。

### 2 · 长命令第一次跑对就固化模板

两次事故(401/4096)都出在"凭记忆重拼启动命令"。修:带 `--evaluator-max-completion-tokens 16384 --evaluator-reasoning-effort low` 的启动模板 + 启动 3 分钟自检(grep 401=0 / 进度在走 / run_args 验配置)固化进 `vtf/TRANSFER_RUNBOOK.md`(commit d7df1d6)。**多参数命令禁止手拼第二次。**

### 3 · 长任务的后续动作写成 watcher

`watch_ent_rejudge.sh`:harness 进程退出 → 自动 `judge.env` → `rejudge_cheap.py` 重判 → ALL_DONE。9/4 首次全程无人值守跑通。"跑完记得回来做 X"不该靠记性。

### 4 · 预注册纪律的价值在否决自己

判据先落盘再跑数,跑完不挪门柱。本线三次自我否决:LoRA 检索增强(代理指标涨/端到端平)、abstention gate(误拒 92/89 越界)、cheap-tier 三改组合(双域未超)。**拒绝噪声改进也是产出。**

### 5 · 小样本惊喜先怀疑抽样

12 题 +16.7pt 的初读是抽样偏差(全同题型),30 题混合后修正(8/27 教训)。扩样后再信。

### 6 · 进度不动 ≠ 卡死

判别三件套:进程 `ps stat` + 产物文件 mtime + 日志尾部。本线多次"慢题风暴"(难判题重试循环)被正确判别为慢而非僵死,避免误杀进程(红线:不杀 python)。

### 7 · 数据搬运卫生

二进制过 ssh 通道会污染(md5 漂移)→ 一律 `base64 -w0 | base64 -d` + 两侧 md5 对账;进仓口径照抄已验证模式(`*.jsonl.gz` + VERDICT.md + md5 指针;`*.log`/裸 `*.jsonl` 被 gitignore)。

### 8 · 下结论前先看实物

断言"rejudge 是串行的"实为 4 并发(ThreadPoolExecutor 就在文件里)——没读文件先外推。探针红灯先证伪自己;性能/实现断言同理:**先读源码再下结论。**

## 判官事故全录(5 次,供检索)

| # | 日期 | 坑 | 症状 | 修复 |
|---|---|---|---|---|
| 1 | 8/30-31 | judge 预算 4096 被 reasoning 吃满 | 空/截断输出系统性记 0,d13 发现 | 16384+low 重判(d12) |
| 2 | 9/3 | judge 网关断连 | e2e 71/500 题误记 0 | 同 judge 重判补齐(#40) |
| 3 | 9/4 | 401 key 变量名(.ark_env vs judge.env) | web LLM 行全零 | judge.env+重判(flips +47/−0) |
| 4 | 9/4 | 4096+medium 漏带修正 flag | ent 空响应风暴+慢题 | watcher 自动重判(+16/−4) |
| 5 | (历史) | newapi 内容审查拦截题干 | PermissionDenied | 换 ARK doubao |

共性:**全部是"启动/配置/基础设施"层问题,无一例是判官模型本身的判断力问题。**
