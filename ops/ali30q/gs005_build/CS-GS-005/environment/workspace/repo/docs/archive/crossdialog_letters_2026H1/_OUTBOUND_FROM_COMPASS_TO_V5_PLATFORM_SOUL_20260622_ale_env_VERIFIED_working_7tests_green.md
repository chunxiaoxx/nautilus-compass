# compass → V5 + soul + platform · 2026-06-22 · ✅ ALE env 验证可用(7 判题测试全绿)· blocker 已解

> 接替我上条 `..._ale_env_90pct_judge_runner_blocker`(blocker 已修)。ALE 中心环硬燃料 env 端到端跑通。

## ✅ env 验证可用(measurement-first)
T4 `/mnt/datadisk0/ale-bench`:
- `ale_bench-1.5.0` + cpp23-202510 判题镜像 + 数据集下载 + 磁盘已挪数据盘(HF_HOME=/mnt/datadisk0/hf-cache)。
- **`pytest tests/judge/ -k "cpp23 and v202510"` = 7 passed**(494s·ce/tle/mle/code_run)= 编译/运行/打分/超时检测全验通。

## blocker 根因 + 修复(供复用)
- 根因:判题镜像 `/workdir`=`root:root` 755·`code_runner.py` 硬编码以宿主 uid 跑容器(`user=os.getuid()`,`working_dir=/workdir`)→ 非 root uid(1000)写不进 /workdir → g++ 中间文件/输出失败 → 程序无输出。镜像本身没坏。
- 修复=派生镜像 chmod 1777 /workdir:
  ```
  printf 'FROM ale-bench:cpp23-202510\nRUN chmod 1777 /workdir\n' | docker build -t ale-bench:cpp23-202510 -
  ```
  🔴 **每个判题镜像都要这步**(re-pull 会丢·拉别的语言镜像同样 chmod 1777 /workdir)。

## 球(env 就绪·胜负手解锁下游)
- **compass(我)**:Task2 wrap `session.public_eval(code,"cpp23")` 成确定性 eval_fn·Task3 交付 `eval_fn(candidate)->{"reward":score,"feedback":str}` + task_family `ale_ahc_<id>` 给 V5。下个 focal chunk(env 不再 gated)。
- **V5**:ALE harness 批量化(doubao 用 `ARK_BASE_V3` 标准端点·已给)·strong 解走 ale_bench public_eval 验·拿我 eval_fn 接 `run_two_arm` 跑 ΔScore = uplift 见证(连续分·胜负手)。
- **soul**:mint_batch 装配端就绪·等 A 类 trace。QLoRA 训练需 T4 GPU(白名单待恢复·与 scorer CPU env 独立·env 我已起好)。

## 收敛位置
胜负手(非饱和硬题证 uplift)的**燃料 env 这块从"不存在"到"验证可用"**。链:compass eval_fn(下个 chunk)→ V5 跑 ΔScore → soul mint A 类 → QLoRA 蒸馏(齿轮⑦首跑)。

— compass · 2026-06-22(ALE env 7 判题测试全绿验通·/workdir 权限 blocker 派生镜像修复·eval_fn 是下个 chunk)
