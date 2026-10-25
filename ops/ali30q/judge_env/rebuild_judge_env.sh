#!/bin/zsh
# 判分环境一键重建(venv-judge)——pytest 9.1.1 四件套(判分器最小依赖)
set -e
CS=${1:-$HOME/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense}
cd "$CS"
if command -v uv >/dev/null; then
  uv venv .venv-judge --python 3.13
  uv pip install -p .venv-judge/bin/python pytest==9.1.1 pyyaml
else
  python3 -m venv .venv-judge
  .venv-judge/bin/pip install pytest==9.1.1 pyyaml
fi
echo "✅ venv-judge 重建完成"
.venv-judge/bin/python -m pytest --version
