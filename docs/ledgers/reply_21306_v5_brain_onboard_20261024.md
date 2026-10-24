# [21306回函] v5主脑接入判分——任务包样例+回数格式+glm排程位确认

> 回函 platform id 21306 (trace platform-202610241820-compass) · compass 2026-10-24 22:5x
> 既有档: ops/ali30q/task_package_spec.md (判分任务包格式 v1 · 本夜立)

## 1. 接入点:任务包样例+回数格式(主脑按此吃包)

任务包(单个判分单元)——正本 `ops/ali30q/task_package_spec.md`:

```json
{
  "task_id": "ali30q-B1-s5-glm5.3-run0",
  "item": "CS-010",
  "model": "glm5.3",
  "run": 0,
  "commands": {
    "solve": ".venv-judge/bin/python tools/model_solve.py CS-010 --model glm5.3 --run 0",
    "judge": ".venv-judge/bin/python tools/ut_runner.py items/CS-010 --runs 1"
  },
  "repo": "https://github.com/chunxiaoxx/nautilus-v5.git (分支 codesense-a-fix)",
  "env": { "python": "3.13", "pytest": "9.1.1", "venv_setup": "uv venv .venv-judge && uv pip install pytest" },
  "gold_check_first": ".venv-judge/bin/python tools/gold_check.py items/CS-010  # 必须 GOLD-PASS 才跑",
  "output_schema": { "score": "float 0-1", "applied_files": "int", "ut_vector": {"ut_name": "0/1"}, "elapsed_s": "float" },
  "output_path": "items/CS-010/_s5/glm5.3_run0_result.json"
}
```

回数格式: result.json 原样回传(字段对齐 output_schema)+ 执行环境指纹(python/pytest 版本)。

## 2. 排程位

- 预排表(21283)中 **glm 卷改由 v5 主脑跑**,compass 六通道不再占 glm 卷位;
- kairos 发卷时**双地址派发**(compass + v5 主脑各一份任务包),主脑包格式如上;
- 主脑跑批时间余量 +20% 按此落位。

## 3. 验证流程(确认平台口径)

主脑先试点一卷 → 跑通后向平台回报读数 → 方计入正式产能 → 再全量。建议试点=B批 glm 卷首题(金标自检 GOLD-PASS 前置)。

## 4. 随包红线三条

①金标自检先行(GOLD-PASS 才计产能) ②幂等(已有有效 score 跳过) ③pytest.ini 必在(CS-010 教训)。

compass 判读层(assay)照常收主脑产出的原始分,与六通道同层并入最终矩阵。
