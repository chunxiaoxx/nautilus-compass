# 晓天平台 harbor 模板解析(2026-10-25)· 与 CS 题包 diff

## 模板结构(demo 实物)
```
harbor-task-template/
├── task.toml          # schema 1.3(注释极详:每字段可空性)
├── instruction.md     # 现象/要求/约束三段式(不泄根因)
├── tests/test.sh      # 判分 shell(set -euo;reward.txt 写 0-1)
├── solution/solve.sh  # golden.patch 应用
├── solution/golden.patch
└── environment/Dockerfile  # 阿里内网镜像源(mirror.aone.alibaba-inc.com)
```

## 与我们 CS 包的关键差异(适配清单)
| 项 | 我们 | 模板(平台要求) |
|---|---|---|
| schema_version | 1.4 | **1.3**(回退或双版本) |
| 判分 | ut_runner python | **test.sh 写 reward.txt**(shell 出口) |
| metadata | 无知识树 | **knowledge_path/L0-L3 四级知识树必填** |
| tags | 自由 | 知识树路径 tags |
| 镜像 | 通用 | **阿里内网 mirror.aone.alibaba-inc.com**(Dockerfile 要改) |
| network | no-network | public/allowlist 选项化 |
| instruction | 自由结构 | 现象/要求/约束三段式(不泄根因红线) |

## 适配动作(每题出包前)
1. task.toml 降 schema 1.3+补 knowledge_path 四级(按题目领域填 D 对应知识树)
2. ut_runner 结果 → test.sh 包装(shell 写 reward.txt)
3. Dockerfile 换阿里内网镜像源
4. instruction.md 对齐三段式
5. 平台五脚本(task-pre-valid/build/eval/codesense-check/submit)预检
