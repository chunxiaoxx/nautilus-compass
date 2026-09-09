#!/bin/bash
# 启动 V5 Memory Daemon · 后台跑 · 第一次 cold-load BGE 后常驻
# 可重复跑 · 如已在跑则 noop
#
# 2026-09-01 竞态修复 (root cause of 2026-08-30 内存灾难):
#   旧逻辑: ping 不通 → nohup 拉新。但新 daemon 冷加载 BGE ~30s 内
#   ping 不通 → 并发调用各自拉一份 → 当晚 18 份 × 870MB ≈ 15.7GB。
#   修复: ① mkdir 原子锁串行化 ② 锁内复查 ping ③ spawn 后 120s 冷启动豁免。
#   Git Bash 无 flock,故用 mkdir(原子系统调用) + mtime 判 stale 锁。

PLUGIN_DIR="$(dirname "$(readlink -f "$0")")"

PYTHON=""
for c in python3 python; do
    if command -v "$c" &>/dev/null; then PYTHON="$c"; break; fi
done
[ -z "$PYTHON" ] && { echo "❌ no python"; exit 1; }

# ── 快路径: 已 alive ───────────────────────────────────
if "$PYTHON" "$PLUGIN_DIR/daemon.py" ping 2>/dev/null; then
    echo "✅ V5 Memory Daemon 已在跑 (port 9876)"
    exit 0
fi

# ── 半死残留清理 (2026-09-09 睡眠-唤醒案例修复, 原 9/15 项提前) ──────
# ping 失败有两种: 拒连(无进程, netstat 空, 本段自然跳过) 或 连上无响应(半死残留抢连接)。
# 残留不清 → 新实例 bind 失败 → 双 LISTEN 抢连接 → 客户端随机超时。
# 防误杀: 二次 ping 确认 (daemon 偶发忙时不杀)。
sleep 3
if ! "$PYTHON" "$PLUGIN_DIR/daemon.py" ping 2>/dev/null; then
    for _pid in $(netstat -ano 2>/dev/null | grep ":9876" | grep "LISTENING" | awk '{print $NF}' | sort -u); do
        echo "🧹 清理 9876 半死残留监听 PID $_pid"
        taskkill //PID "$_pid" //F >/dev/null 2>&1
    done
    sleep 1
fi

# ── 竞态防护 ───────────────────────────────────────────
LOCK_DIR="$PLUGIN_DIR/.cache/daemon_start.lock"
MARKER="$PLUGIN_DIR/.cache/daemon_started_at"
GRACE=600   # spawn 后 600s 内视为冷加载中,不重复拉起
            # 2026-09-08 实测总冷启动 349s(BGE 294s+anchors 40s+bind)——原 120s 是双实例竞态根源
STALE=300   # 锁存活超过 300s 视为残留 (正常持锁 ≤60s)

mkdir -p "$PLUGIN_DIR/.cache"

if mkdir "$LOCK_DIR" 2>/dev/null; then
    # 拿到锁: 本调用负责探活 + 拉起
    trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT

    # 锁内复查: 排队期间前一个调用可能已拉起
    if "$PYTHON" "$PLUGIN_DIR/daemon.py" ping 2>/dev/null; then
        echo "✅ V5 Memory Daemon 已在跑 (port 9876)"
        exit 0
    fi

    # 冷启动豁免: 最近 GRACE 秒内刚 spawn 过 (BGE 加载中, ping 不通是正常的)
    if [ -f "$MARKER" ]; then
        mage=$(( $(date +%s) - $(stat -c %Y "$MARKER" 2>/dev/null || echo 0) ))
        if [ "$mage" -lt "$GRACE" ]; then
            echo "⏳ daemon ${mage}s 前刚 spawn (BGE 冷加载 ~30s) · 跳过重复拉起"
            exit 0
        fi
    fi

    # 后台启动 · nohup + disown
    echo "启动 V5 Memory Daemon ..."
    date +%s > "$MARKER"
    nohup "$PYTHON" "$PLUGIN_DIR/daemon.py" >> "$PLUGIN_DIR/.cache/daemon.log" 2>&1 &  # 2026-08-23 torch shortpath fix · 2026-09-08 死因日志落盘(原 >/dev/null 黑箱)
    DAEMON_PID=$!
    disown $DAEMON_PID 2>/dev/null
    echo "PID: $DAEMON_PID · 等 BGE load (~30s) ..."

    # 轮询 ping 直到 alive (最多 60s) —— 持锁期间, 并发调用走"跳过"分支
    for i in $(seq 1 60); do
        sleep 1
        if "$PYTHON" "$PLUGIN_DIR/daemon.py" ping 2>/dev/null; then
            echo "✅ V5 Memory Daemon ready (took ${i}s)"
            echo "   port 9876 · PID file: $PLUGIN_DIR/.cache/daemon.pid"
            echo "   log: $PLUGIN_DIR/.cache/daemon.log"
            exit 0
        fi
    done

    echo "❌ daemon 60s 内没起来 · 看 $PLUGIN_DIR/.cache/daemon.log"
    exit 1

else
    # 锁被占: 先判 stale (持锁者崩溃没释放的情况)
    lage=$(( $(date +%s) - $(stat -c %Y "$LOCK_DIR" 2>/dev/null || echo 0) ))
    if [ "$lage" -gt "$STALE" ]; then
        echo "⚠️ 锁残留 ${lage}s (>$STALE) · 清除后重试"
        rmdir "$LOCK_DIR" 2>/dev/null
        exec bash "$0" "$@"
    fi
    echo "⏳ 另一个 daemon_start 正在启动 daemon · 跳过"
    exit 0
fi
