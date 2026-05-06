#!/usr/bin/env bash
# stress_audit.sh — sqlite audit_log scale stress test
#
# Goal: quantify sqlite scale limits to decide monthly partition trigger.
# Tests 4 scales: 1K / 10K / 100K / 1M rows.
# Per scale: INSERT throughput, SELECT p50/p95, DELETE+VACUUM, disk size.
#
# Usage:
#   ./stress_audit.sh           # runs 1K/10K/100K (skips 1M unless fast enough)
#   ./stress_audit.sh --full    # forces 1M scale regardless
#   ./stress_audit.sh --quick   # only 1K/10K
#
# Dependencies: bash, sqlite3, awk, date (GNU), /dev/urandom
# Cloud-friendly: pure shell + sqlite3 CLI, no Python required.

set -euo pipefail

# ---------- args ----------
MODE="default"
case "${1:-}" in
  --full)  MODE="full"  ;;
  --quick) MODE="quick" ;;
  --help|-h)
    sed -n '2,15p' "$0"
    exit 0
    ;;
esac

# ---------- setup ----------
TMPDIR_ROOT="${TMPDIR:-/tmp}"
WORKDIR="$(mktemp -d "${TMPDIR_ROOT}/stress_audit.XXXXXX")"
DB="${WORKDIR}/audit.db"
trap 'rm -rf "${WORKDIR}"' EXIT

# portable millis (GNU date %N, fallback to python/perl)
now_ms() {
  if date +%s%3N 2>/dev/null | grep -qE '^[0-9]+$'; then
    date +%s%3N
  elif command -v python3 >/dev/null 2>&1; then
    python3 -c 'import time; print(int(time.time()*1000))'
  else
    perl -MTime::HiRes=time -e 'printf("%d\n", time()*1000)'
  fi
}

human_bytes() {
  awk -v b="$1" 'BEGIN{
    split("B KB MB GB", u);
    i=1; while (b>=1024 && i<4) { b/=1024; i++ }
    printf("%.1f%s", b, u[i])
  }'
}

# ---------- schema mirrors compass audit_log ----------
init_schema() {
  sqlite3 "$DB" <<'SQL'
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA temp_store=MEMORY;
PRAGMA cache_size=-64000;

CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  ts INTEGER NOT NULL,
  action TEXT NOT NULL,
  resource TEXT,
  metadata TEXT
);
CREATE INDEX idx_user_ts ON audit_log(user_id, ts DESC);
CREATE INDEX idx_ts ON audit_log(ts);
SQL
}

# ---------- insert N rows in batches of 100/tx ----------
insert_rows() {
  local N=$1
  local BATCH=100
  local users=64       # 64 distinct users → realistic skew
  local now_s
  now_s=$(date +%s)

  # Generate SQL stream: each batch wrapped in BEGIN/COMMIT
  awk -v N="$N" -v B="$BATCH" -v U="$users" -v NOW="$now_s" '
    BEGIN {
      srand(NOW);
      actions[0]="login"; actions[1]="read"; actions[2]="write";
      actions[3]="delete"; actions[4]="export"; actions[5]="api_call";
      printf "PRAGMA journal_mode=WAL;\n";
      for (i=1; i<=N; i++) {
        if ((i-1) % B == 0) printf "BEGIN;\n";
        uid = "user_" int(rand()*U);
        ts  = NOW - int(rand()*86400*30);   # spread over 30 days
        a   = actions[int(rand()*6)];
        res = "/api/r/" int(rand()*1000);
        # short metadata json-ish blob (~80 chars)
        meta = sprintf("{\"ip\":\"10.%d.%d.%d\",\"ua\":\"ua_%d\",\"sz\":%d}", \
                      int(rand()*256), int(rand()*256), int(rand()*256), \
                      int(rand()*999), int(rand()*10000));
        # SQLite string literals MUST use single quotes (double = identifier ref)
        printf "INSERT INTO audit_log(user_id,ts,action,resource,metadata) VALUES('"'"'%s'"'"',%d,'"'"'%s'"'"','"'"'%s'"'"','"'"'%s'"'"');\n", \
               uid, ts, a, res, meta;
        if (i % B == 0 || i == N) printf "COMMIT;\n";
      }
    }
  ' | sqlite3 "$DB"
}

# ---------- select latency probe ----------
# Run K queries with random user_id, return p50_ms p95_ms
probe_select() {
  local K=$1
  local users=64
  local samples="${WORKDIR}/lat_$$.txt"
  : > "$samples"

  for ((i=0; i<K; i++)); do
    local uid="user_$((RANDOM % users))"
    local t0 t1
    t0=$(now_ms)
    sqlite3 "$DB" "SELECT * FROM audit_log WHERE user_id='${uid}' ORDER BY ts DESC LIMIT 50;" >/dev/null
    t1=$(now_ms)
    echo $((t1 - t0)) >> "$samples"
  done

  sort -n "$samples" -o "$samples"
  awk -v k="$K" '
    { a[NR]=$1 }
    END {
      p50_idx = int(k*0.50); if (p50_idx<1) p50_idx=1;
      p95_idx = int(k*0.95); if (p95_idx<1) p95_idx=1;
      printf "%d %d\n", a[p50_idx], a[p95_idx]
    }
  ' "$samples"
  rm -f "$samples"
}

# ---------- delete + vacuum ----------
# Retention: delete oldest 25% (approx 7 days of 30-day window)
delete_and_vacuum() {
  local cutoff
  cutoff=$(sqlite3 "$DB" "SELECT ts FROM audit_log ORDER BY ts ASC LIMIT 1 OFFSET (SELECT COUNT(*)/4 FROM audit_log);")
  local t0 t1
  t0=$(now_ms)
  sqlite3 "$DB" "DELETE FROM audit_log WHERE ts < ${cutoff}; VACUUM;"
  t1=$(now_ms)
  echo $((t1 - t0))
}

db_size_bytes() {
  # include -wal if present
  local sz=0
  for f in "$DB" "${DB}-wal" "${DB}-shm"; do
    [ -f "$f" ] && sz=$((sz + $(wc -c < "$f")))
  done
  echo "$sz"
}

# ---------- run a single scale ----------
run_scale() {
  local N=$1
  rm -f "$DB" "${DB}-wal" "${DB}-shm"
  init_schema

  # INSERT
  local t0 t1 ins_ms ins_per_sec
  t0=$(now_ms)
  insert_rows "$N"
  t1=$(now_ms)
  ins_ms=$((t1 - t0))
  if [ "$ins_ms" -le 0 ]; then ins_ms=1; fi
  ins_per_sec=$(awk -v n="$N" -v ms="$ins_ms" 'BEGIN{printf "%d", n*1000/ms}')

  local size_pre
  size_pre=$(db_size_bytes)

  # SELECT (50 probes for small scales, 30 for large)
  local probes=50
  [ "$N" -ge 100000 ] && probes=30
  local lat
  lat=$(probe_select "$probes")
  local p50 p95
  p50=$(echo "$lat" | awk '{print $1}')
  p95=$(echo "$lat" | awk '{print $2}')

  # DELETE + VACUUM
  local del_ms
  del_ms=$(delete_and_vacuum)

  local size_post
  size_post=$(db_size_bytes)

  # CSV row + human size
  local size_pre_h size_post_h
  size_pre_h=$(human_bytes "$size_pre")
  size_post_h=$(human_bytes "$size_post")

  printf "%-7s %-15s %-12s %-12s %-15s %-12s %-12s\n" \
    "$N" "${ins_per_sec}/s" "${p50}ms" "${p95}ms" "${del_ms}ms" "$size_pre_h" "$size_post_h"

  # also export raw for summary
  echo "${N},${ins_per_sec},${p50},${p95},${del_ms},${size_pre},${size_post}" >> "${WORKDIR}/results.csv"
}

# ---------- main ----------
echo "=== sqlite audit_log stress test ==="
echo "workdir: ${WORKDIR}"
echo "sqlite:  $(sqlite3 -version)"
echo "mode:    ${MODE}"
echo

printf "%-7s %-15s %-12s %-12s %-15s %-12s %-12s\n" \
  "scale" "insert_per_sec" "select_p50" "select_p95" "delete+vacuum" "disk_pre" "disk_post"
printf "%-7s %-15s %-12s %-12s %-15s %-12s %-12s\n" \
  "-----" "--------------" "----------" "----------" "-------------" "--------" "---------"

# Always run small scales
SCALES=(1000 10000 100000)
case "$MODE" in
  quick) SCALES=(1000 10000) ;;
  full)  SCALES=(1000 10000 100000 1000000) ;;
esac

for N in "${SCALES[@]}"; do
  run_scale "$N"
done

# Conditional 1M — only if 100K finished < 60s end-to-end
if [ "$MODE" = "default" ]; then
  last_100k=$(awk -F, '$1==100000 {print $2}' "${WORKDIR}/results.csv" || echo 0)
  if [ -n "$last_100k" ] && [ "$last_100k" -gt 0 ]; then
    # estimate 1M insert time at observed rate
    est_sec=$(awk -v r="$last_100k" 'BEGIN{printf "%d", 1000000/r}')
    if [ "$est_sec" -lt 300 ]; then
      echo
      echo "100K rate=${last_100k}/s — projecting 1M ≈ ${est_sec}s, running 1M scale..."
      run_scale 1000000
    else
      echo
      echo "100K rate=${last_100k}/s — projects 1M > 5min, skipping (use --full to force)"
    fi
  fi
fi

# ---------- summary / recommendation ----------
echo
echo "=== Summary ==="
awk -F, '
  BEGIN {
    danger_scale = 0
    danger_p95 = 0
  }
  {
    n=$1; ips=$2; p50=$3; p95=$4; dv=$5; sz=$7
    if (p95 > 100 && danger_scale == 0) {
      danger_scale = n
      danger_p95   = p95
    }
    last_n=n; last_p95=p95; last_dv=dv; last_sz=sz
  }
  END {
    print "Largest scale tested: " last_n " rows  (post-VACUUM " int(last_sz/1024) " KB, p95=" last_p95 "ms, vacuum=" last_dv "ms)"
    print ""
    print "Postgres trigger recommendation:"
    if (danger_scale > 0) {
      print "  >>> SQLite p95 crossed 100ms at " danger_scale " rows (p95=" danger_p95 "ms)."
      print "  >>> Switch to Postgres (or monthly partitioning) BEFORE " danger_scale " rows/table."
      target = int(danger_scale * 0.5)
      print "  >>> Safe trigger: monthly partition rotation at " target " rows/month."
    } else {
      print "  SQLite p95 stayed under 100ms across all tested scales."
      if (last_n >= 1000000) {
        print "  No urgent need for Postgres. Revisit when single table > 1M rows or DB > 1GB."
      } else {
        print "  Run with --full to test 1M scale before declaring sqlite safe."
      }
    }
  }
' "${WORKDIR}/results.csv"

echo
echo "Raw CSV: ${WORKDIR}/results.csv  (preserved until script exit)"
echo "Done."
