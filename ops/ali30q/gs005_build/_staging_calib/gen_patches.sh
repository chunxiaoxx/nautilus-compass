#!/bin/bash
set -e
REPO=staging/workspace/repo
IMPL=impls
OUT=patches
GOLD_ROOT=../CS-GS-005/solution
# 恢复基线
reset_base() { git -C $REPO checkout -q . ; git -C $REPO clean -qfd ; }
# full_score: 金标 bridge + 缺失件归位
reset_base
cp ../CS-GS-005/solution/v5_bridge_golden/helix_bridge.py $REPO/v5_bridge/helix_bridge.py
mkdir -p $REPO/packages/nautilus_core
cp $GOLD_ROOT/nautilus_core_helix_chain.py $REPO/packages/nautilus_core/helix_chain.py
git -C $REPO add -A; git -C $REPO diff --cached HEAD > $OUT/full_score.patch
# equivalent
reset_base
cp $IMPL/helix_bridge_equivalent.py $REPO/v5_bridge/helix_bridge.py
git -C $REPO add -A; git -C $REPO diff --cached HEAD > $OUT/equivalent.patch
# defective
reset_base
cp $IMPL/helix_bridge_defective.py $REPO/v5_bridge/helix_bridge.py
git -C $REPO add -A; git -C $REPO diff --cached HEAD > $OUT/defective.patch
# guessed
reset_base
cp $IMPL/helix_bridge_guessed.py $REPO/v5_bridge/helix_bridge.py
git -C $REPO add -A; git -C $REPO diff --cached HEAD > $OUT/guessed.patch
reset_base
wc -l $OUT/*.patch
