# 判分任务包格式 v1(v5 主脑接入用 · compass 2026-10-24 夜)

## 任务包(单个判分单元)
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
## 回数格式
result.json 原样回传(输出 schema 对齐)+ 执行环境指纹(python/pytest 版本)。
## 红线
①金标自检先行(GOLD-PASS 才计产能) ②幂等(已有有效 score 跳过) ③pytest.ini 必在(CS-010 教训)
