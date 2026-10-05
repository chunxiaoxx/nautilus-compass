# L3 smoke 双臂 ×10 题 · 判据档(2026-10-05,R177;正榜判据正本 L3_HARNESS_BOARD_ROUND1_PREREG_20261005.md)

> smoke 定位:**管道验证+磨合暴露,不出名次、不出 resolved%**(10 题无统计意义,判分=正榜独立工序)。
> 开跑前判据演进窗口内暴露的预算信号(max_steps=25 偏紧)记入本档,正榜开跑前重估。

## 题源(双臂同一)

- heldout30[0:10](全 astropy__astropy)+ ENV 行注入(`r81_env.env_line`,repo/base_commit 来自 extra_info.metadata);
- 题面逐字节双臂同:harness 代码零改动(A=mini_runner_e5.py@4e14a898 锚定,B=mini 2.4.6 官方);
- 重建配方:`smoke10_meta.json`(坑留档:首版 pandas to_parquet 使 prompt 列退化 str,回读验证抓出,pyarrow 显式 list<struct> 重建)。

## 配置钉死(双臂同)

| 参数 | A 臂(v5-harness) | B 臂(mini-swe-agent 2.4.6) |
|---|---|---|
| 模型/网关 | MiniMax-M3 系@127.0.0.1:18001 | 同 |
| temperature / top_p | 0 / 1 | 0 / 1 |
| max_steps | 25 | step_limit=25 |
| prompt 模板 | v5 STUDENT_PROMPT_VERSION(student-prompt-v0.1) | mini 官方 default.yaml 原文 |
| 工具面 | str_replace_editor+submit(无 shell,v5 自述"下位配置") | bash(LocalEnvironment) |
| 执行环境 | LocalSandbox+worktree(r81 池) | LocalEnvironment cwd=worktree(同 r81 池,同 base_commit) |
| 每命令超时 | (v5 沙箱内定) | 300s |
| wall 护栏 | 无 | 1800s/题 |

差异(模板/工具面/超时/护栏)=harness 本体差异与护栏,如实披露不惩罚(预注册配置差裁定 1)。

## 汇总读数口径(smoke 只报这些)

完成率(finished/Submitted)· patch 非空率 · 步数 · 耗时 · FormatError/退出原因分布——逐题可追溯(trajectory+patch+result)。

## 已暴露信号(开跑前演进窗口)

1. **max_steps=25 预算紧**(双臂):A 臂 task_1-3 打满 25 步(finished=False),B 臂首题打满(patch=0);astropy 大 repo 探索成本高。建议正榜前重估(判据演进程序+判绩账记档,开跑后不得再动);
2. B 臂完成协议(每轮必须 tool call,M3 文本收尾倾向)在 LimitsExceeded 路径下未炸(format_error 喂回兜住),25 步内未观察到 RepeatedFormatError;
3. socks 代理 env 毁 litellm/httpx(第 N 次复发)——b_runner 脚本级根治(清 env+NO_PROXY=*)。

## 产物坐标

- 题源+配方:`smoke10.parquet`/`tasks.json`/`smoke10_meta.json`
- A 臂:`nautilus-v5/tools/uni_agent_bridge/e5_workdirs/task_N_*(l3a 会话)`+`arm_a_run.log`
- B 臂:`b_arm/task_N/{trajectory,result,patch.diff}`+`arm_b_run.log`
- 汇总:`smoke_summary.json`(跑完落)
