# CS-511/512 PoW 铸造预注册判据（2026-10-26）

来源：平台函 #21986。铸造属于结算动作，以下四件任一缺失即不执行 `pow_mint.py`。

## 必须证据

1. `git_hash`：题目生产提交的完整 SHA，且该 SHA 中包含对应题目实物。
2. `ut_count/ut_total`：从冻结测试文件独立计数，二者一致。
3. `golden_pass`：明确标记为 golden 的执行记录，包含命令、环境、退出码、逐测试结果；必须等于 `ut_total`。
4. `acceptor=v5`：v5 独立验收回执必须绑定 qid、git_hash、golden 证据坐标，不能以生产者自报替代。

## Batch schema

顶层 JSON 数组；每题必须含 `qid/producer/git_hash/ut_count/golden_pass/ut_total/acceptor`；`irt_b/gating` 可选。执行前 dry-run/只读验证 schema；执行后 DB 三重回读（trajectory、ledger、幂等重跑）。

## 红线

- 不用 #21986 的占位 SHA。
- 不把普通 UT 运行冒充 golden。
- 不把“v5提到题号”冒充 acceptor 签字。
- 当前证据冲突时先报红灯，不补造 20/20。
