# CS-010 判分结果入 fuel_trajectories 预注册判据（2026-10-25）

## 任务与范围

来源：平台函 #21856。仅回填执行时快照中 `CS-010/_s5/*_result.json` 且 `score != null` 的结果；不补造缺失槽，不覆盖原始结果。

## 冻结判据

1. 去重键：`traj_id = judge-CS-010-<model>-run<run>`；重复执行必须幂等。
2. `verdict`：仅 `score == 1.0` 记 `PASS`；其余非空分数记 `FAIL`。
3. `trajectory` 保存 JSON 对象：`model`、`run`、`score`、按 UT 名稳定排序后的 `ut_vector` 布尔数组、`ut_names`。
4. `label_origin = ali30q-judge`，`submitter = compass`，`qid = CS-010`。
5. `context = S3判分 <model> run<run>`。
6. 执行后必须 DB 回读：本批 `traj_id` 数量、逐条 score/verdict、重复键数；任何一项不符即 RED。
7. 证据层：DB 回读为 `[实测]`；未能从 DB 回读的内容不得报为完成。

## 实现者自测与独立复算

- 实现者：本会话生成参数化 SQL 并执行。
- 非实现者复算坐标：本档 + `CS-010/_s5/*_result.json` + DB 查询命令；交接不预填预期读数。
