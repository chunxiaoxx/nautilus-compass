#!/bin/bash
# old_disk_transfer.sh · 在新 GPU 机上执行:从旧盘机拉 Qwen 续传 + LME-V2 两个 tar
# 前置:新机 pubkey 已装入旧机 authorized_keys(用 vtf/link_machines.py 打通)
# 用法: OLD_HOST=223.109.239.11 OLD_PORT=13624 bash old_disk_transfer.sh report   # 只盘点不搬
#       OLD_HOST=223.109.239.11 OLD_PORT=13624 bash old_disk_transfer.sh go       # 盘点+搬运+校验
set -uo pipefail
MODE="${1:-report}"
OLD_HOST=${OLD_HOST:?need OLD_HOST}
OLD_PORT=${OLD_PORT:-22}
SSH="ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -o BatchMode=yes -p $OLD_PORT"
OLD="root@$OLD_HOST"
LOGD=/root/transfer_logs; mkdir -p "$LOGD"

NEW_QWEN=/root/data/models/qwen35-9b            # 数据盘(根盘 91% 满,勿落根盘)
NEW_TARDIR=/root/data/lmev2-screenshots         # tar 落数据盘,repo 侧 symlink 过来
REPO_TARDIR=/root/LongMemEval-V2/data/longmemeval-v2/trajectory_screenshots

echo "=== P0 probe old machine ==="
$SSH $OLD 'echo OLD_REACHABLE; hostname' || { echo "OLD_UNREACHABLE — 检查 OLD_HOST/OLD_PORT/key auth"; exit 1; }

# 自动探测旧机路径(重租后挂载点可能变)
OLD_QWEN=${OLD_QWEN_DIR:-$($SSH $OLD 'for d in /root/models/qwen35-9b /root/data/models/qwen35-9b; do [ -d "$d" ] && echo "$d" && break; done')}
OLD_TARS=${OLD_TAR_DIR:-$($SSH $OLD 'for d in /root/LongMemEval-V2/data/longmemeval-v2/trajectory_screenshots /root/data/LongMemEval-V2/data/longmemeval-v2/trajectory_screenshots; do [ -d "$d" ] && echo "$d" && break; done')}
echo "OLD_QWEN=$OLD_QWEN"; echo "OLD_TARS=$OLD_TARS"
[ -z "$OLD_QWEN" ] && echo "WARN: 旧机没找到 qwen 目录"
[ -z "$OLD_TARS" ] && echo "WARN: 旧机没找到 tar 目录"

echo "=== P1 inventory (双侧对比) ==="
$SSH $OLD "ls -la $OLD_QWEN/ 2>/dev/null; echo ---; ls -la $OLD_TARS/*.tar.gz 2>/dev/null" | tee "$LOGD/old_side.txt"
echo "--- NEW side ---"
ls -la "$NEW_QWEN"/ 2>/dev/null | tee "$LOGD/new_side.txt"
df -h / /root/data
[ "$MODE" = "report" ] && { echo "REPORT_ONLY_DONE"; exit 0; }

echo "=== P2a rsync tars -> 数据盘 ==="
mkdir -p "$NEW_TARDIR"
rsync -avP -e "$SSH" "$OLD:$OLD_TARS/*.tar.gz" "$NEW_TARDIR/" 2>&1 | tail -5 | tee "$LOGD/rsync_tar.log"
# repo 侧 symlink(幂等)
if [ -d "$REPO_TARDIR" ] && [ ! -L "$REPO_TARDIR" ]; then
  # 已有真目录且非空→把内容并进数据盘再换 symlink
  rsync -a "$REPO_TARDIR/" "$NEW_TARDIR/" && rm -rf "$REPO_TARDIR"
fi
[ -L "$REPO_TARDIR" ] || ln -sfn "$NEW_TARDIR" "$REPO_TARDIR"
ls -la "$REPO_TARDIR"/ | head

echo "=== P2b qwen 智能合并(只拉旧机更大的文件,防回退新机进度) ==="
$SSH $OLD "cd $OLD_QWEN && find . -type f -printf '%s %p\n'" | sort > "$LOGD/old_files.txt"
(cd "$NEW_QWEN" && find . -type f -printf '%s %p\n' 2>/dev/null | sort) > "$LOGD/new_files.txt" || true
python3 - "$LOGD/old_files.txt" "$LOGD/new_files.txt" > "$LOGD/qwen_todo.txt" <<'PYEOF'
import sys
def load(p):
    m = {}
    for line in open(p):
        line = line.strip()
        if not line: continue
        sz, _, path = line.partition(' ')
        m[path] = int(sz)
    return m
old, new = load(sys.argv[1]), load(sys.argv[2])
for path, osz in sorted(old.items()):
    nsz = new.get(path, -1)
    if nsz < osz:  # 新机没有或更小 → 值得拉
        print(path)
PYEOF
TODO=$(wc -l < "$LOGD/qwen_todo.txt")
echo "qwen files to pull: $TODO"
if [ "$TODO" -gt 0 ]; then
  (cd /tmp && rsync -avP --files-from="$LOGD/qwen_todo.txt" -e "$SSH" "$OLD:$OLD_QWEN/" "$NEW_QWEN/" 2>&1 | tail -5 | tee "$LOGD/rsync_qwen.log")
fi

echo "=== P3 verify ==="
for f in "$NEW_TARDIR"/*.tar.gz; do
  echo -n "$(basename $f): "; tar -tzf "$f" > /dev/null 2>&1 && echo TAR_OK || echo TAR_CORRUPT
done
echo "-- qwen incomplete 残留 --"; ls -la "$NEW_QWEN"/*.incomplete 2>/dev/null || echo "no .incomplete (完整或需 HF 补齐)"
echo "-- index 分片对齐 --"
python3 - <<'PYEOF'
import json, os
d = "/root/data/models/qwen35-9b"
idx = os.path.join(d, "model.safetensors.index.json")
if os.path.exists(idx):
    shards = sorted(set(json.load(open(idx))["weight_map"].values()))
    missing = [s for s in shards if not os.path.exists(os.path.join(d, s))]
    print(f"shards={len(shards)} missing={len(missing)}", missing if missing else "ALL_PRESENT")
else:
    print("NO_INDEX_YET")
PYEOF
echo "TRANSFER_DONE"
