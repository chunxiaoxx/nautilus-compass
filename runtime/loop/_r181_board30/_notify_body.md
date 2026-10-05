L3 harness 对比榜 Round 1 双臂开跑通报(判据演进记档):

1. max_steps 25→50(判据演进,开跑前窗口内):R177 smoke 双臂×10 暴露 25 步预算偏紧(B 臂 10/10 打满零提交,A 臂 3/10 打满),经复核 2026-10-05 拍板双臂同步放宽至 50。A 臂 v5 仓 f1921b66 参数化 --max-steps(默认 25 保持 4e14a898 历史行为,harness 本体 NautilusAgent+LocalSandbox+prompt 模板零改动);B 臂 step_limit=50。判据正本 L3_HARNESS_BOARD_ROUND1_PREREG_20261005.md 配置差裁定第 3 条已更新,开跑后不得再动。

2. 正榜题源重抽 n=30(分层):smoke 所用 heldout30 repo 分布偏(astropy 19+django 11),不作正榜样本。正榜题源=SWE-bench Verified 500 按 repo 比例最大余数法分层抽样 n=30,seed=20261005 入档:django 14/sympy 5/sphinx 3/matplotlib 2/scikit-learn 2/astropy 1/xarray 1/pylint 1/pytest 1(seaborn/flask/requests 全库 ≤8 题,配额为 0,如实披露)。双臂同题面(ENV 行注入,harness 代码零改动),题源+配方坐标 runtime/loop/_r181_board30/(board30.parquet+tasks.json+board30_meta.json)。

3. Round 1 口径:n=30 达名次区门槛(榜判据 v1 N4),榜页如实标 n=30;剩余 470 题滚动扩样,任务集口径=Verified 500 resolved% 不变。判分=compass 独立判读(SWE-bench 评测按 L1 注记口径,harness+dataset 双 tag),判读免费。

4. B 臂护栏随步数预算同步放宽:wall_time_limit 1800s→3600s/题(披露项,不进名次规则)。

跑批进行中,判分抽查 ≥20% 后出读数,10/12 榜页上线。

compass · 判分机构
