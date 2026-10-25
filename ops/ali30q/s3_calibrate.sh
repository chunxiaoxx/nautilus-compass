#!/bin/zsh
# S3 标定(双态验证 shell 版·CS-511 实测配方)
# 用法: s3_calibrate.sh CS-511
set -e
ITEM=$1
BASE=~/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items/$ITEM
J=~/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/.venv-judge/bin/python
cd $BASE
[ -f pytest.ini ] || { echo "缺 pytest.ini"; exit 1; }
echo "═══ 坑版(应部分挂)═══"; $J -m pytest tests/ -q 2>&1 | tail -1
echo "═══ 金标(应全过)═══"
cp -r solution/. environment/workspace/repo/
$J -m pytest tests/ -q 2>&1 | tail -1
# 还原坑版
cd environment/workspace/repo && git checkout -- . 2>/dev/null || true
cd $BASE
echo "═══ 变体逐个(如有)═══"
for v in _s3_variants/*.py; do
  [ -f "$v" ] || continue
  name=$(basename $v .py)
  cp "$v" environment/workspace/repo/marchant_metrics/ 2>/dev/null || cp "$v" environment/workspace/repo/
  $J -m pytest tests/ -q 2>&1 | tail -1
  cd environment/workspace/repo && git checkout -- . 2>/dev/null; cd $BASE
done
echo "✅ 标定完成(读数供四门素材)"
