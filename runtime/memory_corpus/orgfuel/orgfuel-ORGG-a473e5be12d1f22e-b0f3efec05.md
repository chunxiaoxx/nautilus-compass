---
name: orgfuel-ORGG-a473e5be12d1f22e-b0f3efec05
description: "判读档判例 MACMINI_MIGRATION_PLAN_20261011 · 二、Mac mini M6 适配挑战 #"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-a473e5be12d1f22e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 MACMINI_MIGRATION_PLAN_20261011 · 二、Mac mini M6 适配挑战
## 二、Mac mini M6 适配挑战

| 挑战 | 影响 | 解法 |
|---|---|---|
| **bash 版本** | macOS 自带 bash 3.2(无关联数组/EPOCHSECONDS) | brew install bash(5.x) |
| **路径差异** | C:\Users\chunx → /Users/chunx | 全局路径审计+替换 |
| **Python 环境** | 需重建(MiniForge/uv) | pyenv或uv+requirements.txt |
| **BGE 模型** | 需重下(~2GB) | huggingface-cli(M2 芯片 MPS 加速) |
| **paramiko SSH** | 需重装 | pip install |
| **daemon_start.sh** | python3 别名指向不同 | 统一 python3 路径 |
| **MPS vs CUDA** | Mac 用 MPS,CUDA 代码需适配 | 判读推理走 A100(不经本机GPU),本机只用CPU做轻量推理 |
