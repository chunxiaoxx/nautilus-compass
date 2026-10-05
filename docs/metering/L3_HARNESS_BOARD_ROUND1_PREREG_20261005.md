# L3 harness 对比榜 · 首期预注册判据骨架 v0(2026-10-05 落;同日 v1 定版 sha16 见状态段)

> 链条:#3116(L3 owner=compass 判分读数供给,10/12 榜页上线)→ 榜判据 v1(LEADERBOARD_PREREG_CRITERIA_V1_20261005,sha16=282a268ca84ecf72)→ **本期判据(本档,开跑前必须齐,判据只许更严)**。
> 纪律:空白字段如实标"待回填",不臆写;齐备前不开跑、不出读数。

## 期判据表(开跑前置件)

| 字段 | 值 | 状态 |
|---|---|---|
| 被测物 A | **v5-harness**:github.com/chunxiaoxx/nautilus-v5 @ customer-demo-ship-1 @ `4e14a898`;入口 tools/uni_agent_bridge/mini_runner_e5.py(NautilusAgent+LocalSandbox) | ✅ 2026-10-05 platform 3216 函回填 |
| 被测物 B | **mini-swe-agent**(SWE-agent/mini-swe-agent)**@ v2.4.6 官方 release tag(commit `a83fcae82d2a`)**;main@`04d809ce` 参考(比 release 新 6 周,不采用——榜判据钉 release 保可复现) | ✅ 2026-10-05 3194 函拍定+同日 R171 锚定 commit |
| 模型配置(双臂同一) | **双臂同模型=MiniMax-M3 系**(A 臂已钉:127.0.0.1:18001 网关,model=nautilus-v5/MiniMax-M3 系,max_steps=25;B 臂接同模型同网关,采样参数对齐时钉死并双臂同——若 B 臂无法接同模型,按可比性纪律 1 降级为单臂读数,不并榜不对比) | ✅ 定版(采样参数=开跑对齐件,钉死后不得再动) |
| 任务集(双臂同一) | **SWE-bench Verified 500 题 resolved%**(L1 注记口径已冻结) | ✅ platform 3194 确认 |
| 样本量门 | n≥30 进名次区;n<30 进观察区(榜判据 v1 N4) | ✅ 冻结 |
| 判分口径 | 按任务集口径引 L1 注记(SWE-bench=resolved%,harness+dataset 双 tag) | ✅ 冻结(随任务集回填落具体值) |
| 判分者 | compass 独立判分读数供给(判读免费);harness 自报读数只收引用标 [不可验](UNVERIFIABLE 墙) | ✅ 冻结 |
| 证据层 | 全档 [实测]/[推断]/[不可验] 强制标注 | ✅ 冻结 |
| 名次规则 | 单一主指标;并列明写;负结果照实名次;U 态不上名次 | ✅ 冻结 |
| 配置披露列 | **榜面增设(接受 platform 3216 意见)**:双方同列 工具面/推理后端/max_steps/环境;**配置差不加权、不进名次规则**(加权系数=主观自由度,违反预注册精神);不可比项以披露+降级处置代替惩罚 | ✅ 定版(裁定见下) |
| 利益披露 | 双方无装订关系;赞助按榜判据 v1 N5 披露 | ✅ 冻结 |

## 配置差裁定(✅ 2026-10-05,回应 platform 3216"是否加权由可比性五纪律裁定")

1. **工具面差异(v5 LocalSandbox: str_replace_editor+submit 无 shell vs mini-swe-agent 容器全工具)=harness 本体差异的一部分,属被测能力,如实披露不惩罚**——harness 对比测的正是各 harness 在给定模型下的编排/工具运用;但 v5 已明示此为"容器化全工具 agent 横比下位配置",榜面 caveat 如实转述:**Round 1 读数不代表 v5 全能力,解读须带此披露**;
2. **模型必须同**(MiniMax-M3 系双臂同网关)——模型不同=不可比,按纪律 1 降级单臂,不并榜;
3. **max_steps=50 双臂同**(R177 smoke 暴露 25 偏紧(B 臂 10/10 打满零提交),用户 2026-10-05 拍板双臂同步放宽至 50——判据演进程序:开跑前修订+判绩账记档,开跑后不得再动;初版 25 的裁定史留档);
4. 采样参数开跑对齐时钉死并双臂同,钉死后入档不得再动(纪律 5:中途换判据=该期作废)。
5. **采样参数钉死(R171,2026-10-05;R177 演进 max_steps 一项)**:model=MiniMax-M3 系(v5 网关)/**max_steps=50**/temperature=0/top_p=1(贪心,SWE-bench 对比惯例)双臂同;max_tokens 等其余=harness 各自默认,开跑时如实记录(默认参数差异=harness 本体差异,披露不惩罚,同配置差裁定 1)。

## 正榜题源(R177 演进,2026-10-05)

- smoke 用的 heldout30(repo 分布 astropy 19+django 11=2 repo)**分布偏,不作正榜样本**;
- 正榜 Round 1 题源=**SWE-bench Verified 分层抽样 n=30(按 repo 比例配额,固定 seed 入档)**,双臂同题面(ENV 行注入同 smoke 配方,harness 代码零改动);n=30 达名次区门槛(N4),剩余 470 题滚动扩样(榜页如实标 n);
- 全 500 题滚动目标不变(任务集口径=Verified 500 resolved%,n 滚动披露)。

## 判分工序预注册(2026-10-05 R183 落,用户拍板"双臂跑完自动判分出 Round 1 读数")

- **判分环境**:A100 现役机复用(2026-10-05 R184 用户纠偏"没找对数据盘"后实测:vdd4 数据盘 98G 仅用 8%=87G 余,判死结论作废)。部署=static docker 27.3.1 全落 /root/vdd4(dockerd --data-root=/root/vdd4/docker-root,系统盘满不落盘)+swebench 5.0.2 venv@/root/vdd4+HF 走 hf-mirror;评测分两批(非 django 先/django 后)防镜像超容,每批评完立即 rmi;与双臂运行机(Windows 本机)物理分离=非实现者隔离落地件。环境件全 [实测](docker info/hello-world 拉取/dataset 500 rows)。
- **判分命令**(官方口径,零改):`python -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path preds_arm_{a,b}.json --run_id l3r1_{a,b} --max_workers 4`——predictions 由 collect_predictions.py 生成(idx→instance_id 对齐断言,A 臂 patch 取 trajectory.final_patch,B 臂取 patch.diff,缺件如实记 _note)。
- **resolved 定义**:官方 report 的 resolved 列(FAIL_TO_PASS 全过 且 PASS_TO_PASS 全过);unresolved 按 apply fail/test fail/environment error 分桶如实报,负结果照报。
- **抽查 ≥20%**(可比性纪律 4):n=30 抽 6 题/臂,复核=评测执行日志逐题与 report 判定一致性(容器误判/环境错装核对),抽查记录落档。
- **读数**:双臂 resolved/30+分桶+配置披露列全开;榜页标 n=30;判读免费。
- 双臂完成检测:进程退出+30 题产物齐(trajectory/patch.diff 计数),由值守轮轮询触发,不设 cron。

## 任务集选择(✅ 2026-10-05 已拍=SWE-bench Verified 单集起步,platform 3194 函确认;下文推荐理由留档)


- 首期建议单任务集起步(双臂可比性优先,不铺面);
- 推荐 **SWE-bench Verified**(500 题,resolved%,harness 对比最主流口径,L1 注记已冻结其口径与 cutoff 披露);备选 Terminal-Bench(resolve rate,harness+dataset 双 tag 天然适配 harness 对比叙事);
- GAIA 需工具栈披露且 validation 主轨 165 题,首期不作推荐。

## 可比性纪律(✅ 冻结)

1. 双臂必须**同任务集+同模型配置+同采样参数**,任一不同=不可比,只出单臂读数不出对比;
2. 开跑前各自落期判据补全本档空白字段(只许更严),齐备后 sha16 锚定再跑;
3. harness 运行环境(镜像/依赖版本)双臂各自申报并留档;
4. 跑批产物逐题可追溯(输入坐标+输出坐标),判分抽查≥20% 复核一致性;
5. 中途换判据=该期作废重跑,判绩账记档。

## 状态

- [x] 2026-10-05 骨架 v0 落档(冻结项 8/11;待回填 3:被测物锚×2+任务集)
- [x] 2026-10-05 platform 3194 函:任务集=SWE-bench Verified 确认+被测物 B=mini-swe-agent 拍定——待回填收窄至 1 项(被测物 A v5-harness 坐标,platform 另函向 v5 索取,10/10 死线)
- [x] 2026-10-05 platform 3216 函:被测物 A 三件齐(v5 坐标+配置如实披露+B 无异议)→ **v1 定版**:上表全 12 字段齐,配置披露列增设+配置差裁定落档;A 臂环境披露如实记:Windows 11+Python 3.13,LocalSandbox 受限工具面(无 shell),推理 127.0.0.1:18001(MiniMax-M3 系),max_steps=25,v5 自述"容器化全工具横比下位配置"入榜面 caveat
- [x] 2026-10-05 R172:**v5 网关×mini-swe-agent 接入验证 PASS**(docs/metering/L3_GATEWAY_INTEGRATION_CHECK_20261005.md)——litellm 连接/tools 透传(参数名随请求 schema)/多轮回喂全 [实测];协议磨合点(M3 完成即收尾 vs mini 每轮须 tool call)与网关 chat 分支非 stream 挂起缺陷如实记(均不阻塞);B 臂接入配置定版。**开跑前置全部清零**
- [x] 2026-10-05 R177:**smoke 双臂×10 PASS(管道级)**(runtime/loop/_r177_l3smoke/SMOKE_PREREG.md+smoke_summary.json)——题源 heldout30[0:10]+ENV 行(双臂同题面,harness 代码零改动);A 臂 finished 7/10·patch 9/10·步均 18.1,B 臂 finished 0/10·patch 5/10·步均 25.0 全打满;**预算信号:max_steps=25 偏紧(B 臂全打满零提交)——正榜开跑前判据演进窗口建议重估(双臂同步+平台知会),开跑后不得再动**;smoke 不出名次不出 resolved%(预注册)
- [x] 2026-10-05 R181:**开跑**(双臂并行后台)——max_steps=50 演进生效(A 臂 v5 仓 `f1921b66` 参数化 `--max-steps`,默认 25 保持 4e14a898 行为,正榜显式传 50;B 臂 b_runner_r1.py step_limit=50+wall 3600s);题源 board30(runtime/loop/_r181_board30/board30.parquet+tasks.json,seed=20261005,回读验证过);A 臂 tag=l3r1a(held_out=true),B 臂 worktree 前缀 l3r1b;产物坐标 runtime/loop/_r181_board30/{arm_a_run.log,arm_b_run.log,board_b/}+A 臂 e5_workdirs/task_*;
- [x] 2026-10-05 R183:**A 臂返工一次(如实记档)**——首启 4 题作废:board30.parquet 首版 prompt 列漏烧 ENV 行(B 臂 tasks.json 有),A 臂 runner 靠题面 ENV 行预置 worktree→裸跑(env_ready=False 全零 patch);停臂→build 脚本修(ENV 行烧入+tasks.json 单源双出+回读断言)→tasks.json 前后 md5 一致(B 臂零影响)→废件逐个验 session_id 后清→重跑;修后首题 env_ready=True/18 步 patch 1947ch 实证;题源/seed/判据零变,仅题面制备修正;
- [ ] 跑批完成+判分抽查 ≥20% → 10/12 榜页上线

## 定版指纹

- **v1 定版 sha16(2026-10-05,三字段齐时点)**:见 commit 记录(本档定版时算)
- 变更规则:此后修改只许更严(收窄);放宽=B 侧变更走判据演进程序+判绩账记档
