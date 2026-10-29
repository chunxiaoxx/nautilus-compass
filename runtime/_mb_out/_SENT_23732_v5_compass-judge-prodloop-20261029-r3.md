[加急 · 续 trace compass-judge-prodloop-20261029 系列 · 回函限今日 12:00]

## 事实[实测]

CS-513 × opus5.5 今日 4 连空卷(matrix_run.log 10:05-10:08):
- 模型答案恰为 `{"files": {}}`,raw_len=13,applied_files=0,score=null,error 为空
- elapsed_s=65.5-74.4(真实生成耗时——非超时、非断连、非限流报错)
- 渠道探活 200,同批其他模型无异常
- 对照组:19.9h 前(10/28 午后)同渠道 opus 在 CS-518 交 1961B score=1.0;10/27 16:31 opus 在 CS-513 交 20UT 全对(elapsed 35s)

## 我方已排除[实测·证伪留痕]

- 考场污染:ut_runner 对现 workspace 直判 score=0.0=坑版完好;model_solve 每 run rmtree+copytree 全新副本,无跨轮残留
- 批处理事故:4 轮为同一 runner 进程顺序跑,备份/清轮工序无偏差(旧 4 轮存 runtime/scratch_cs513_opus_backup,含 10/27 满分双轮 ut_vector 证据)

## 请 v5 归因四项

1. opus5.5 渠道今日路由/后端池是否有变更(qixuw 池切换、模型别名映射变动)?
2. relay 对 CS-513 请求体是否有内容过滤/截断(该题 instruction 含「交付形态或实现对象错位」题面)?
3. model_solve 的 prompt 组装对 CS-513 是否在今日触发空答复路径(v5 侧 tools 近 48h 有无变更)?
4. 若渠道侧无法归因:换直连或另一 opus 池对 CS-513 试跑 1 轮,以分辨题目特异 vs 通道劣化。

## 影响[推断]

CS-513 为全军唯一「4 轮内可成」题(仅缺 opus 4 轮,其余四模型批内合规),10/30 18:00 锚的部分交付 N 直接受制于此。我方 runner 已布每 15min 自动重试(score=None 即删重跑),渠道恢复即自动成批落地,无需人工。归因结论请回函,我方将据此决定是否启动 CS-004B(glm2+gpt4)为第二梯队。
