# assay 可复算包 · {题号}(replay-verifiable judge pack v2)

## 独立重放三步(甲方拿到即可验证)
```bash
# ① 环境重建
uv venv .venv-judge && uv pip install -r requirements.freeze
# ② 判分重放(同一命令·同一读数)
.venv-judge/bin/python tools/ut_runner.py items/{题号} --runs 4
# ③ 比对(结果应与本包 score 一致;不一致=判分无效,立即联系我们)
```

## 签名链
| 层 | 签名者 | 内容 | 可验方式 |
|---|---|---|---|
| L1 判分 | ut_runner 自动 | score/ut_vector | 重放比对 |
| L2 校验 | compass 判读层 | 矩阵+门判定 | JE V 交叉 |
| L3 锚定 | compass 签名 | 时间戳+环境指纹+读数哈希 | 本包附带 |

## 证据分层
- [实测]: 自动判分+三连稳定——可直接复算
- [推断]: 判读层分析——附依据,可质疑
- [不可验]: 主观判断——如实声明

## 完整性
- instruction.md sha256: {hash}
- task.toml sha256: {hash}
- tests/ 目录 sha256: {hash}
- 本包生成时间: {ts}
