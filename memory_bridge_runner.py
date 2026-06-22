"""齿轮⑤ live runner:把飞轮 sqlite ob_fw learning 沉淀成胶囊并入 T4 文件语义库。

跑在 cloud(sqlite 本地 + serving 本地 + 有 T4 rsync key)。端到端路径(本 session 实证):
  sqlite ob_fw(content_plain JSON)→ memory_bridge.consolidate(过 W1 晋升门)
  → POST /v1/v14/ingest_obs(cloud 渲染 capsule .md)→ rsync cloud→T4(补缺失同步桥)
  → T4 daemon inotify 索引 → /v1/v14/recall 语义可召回。
幂等:seen 文件持久化已沉淀键·重跑只补增量。

部署:scp 本文件 + memory_bridge.py 到 cloud → `python3 memory_bridge_runner.py`。
(corpus_sync 不存在·故 runner 自带 rsync 步。)
"""
import json
import os
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request

import memory_bridge as mb

# serving 有速率限制(429)。节流 + 429 退避重试(注入式 effect·consolidate 保持纯净)。
INGEST_THROTTLE_S = 0.4
INGEST_MAX_RETRY = 4

DB = "/var/lib/compass/compass.db"
SERVING_INGEST = "http://127.0.0.1:8770/v1/v14/ingest_obs"
SEEN_FILE = "/var/lib/compass/fleet_capsule_seen.txt"
T4_HOST = "ubuntu@43.166.8.20"
T4_KEY = os.path.expanduser("~/.ssh/id_ed25519_qb")
CAP_DIR = "/home/ubuntu/.claude/projects/fleet-capsules/"


def read_flywheel_obs() -> list[dict]:
    """读 sqlite ob_fw 行·content_plain JSON 解成 obs dict(带 obs_id)。"""
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT obs_id, content_plain FROM observations WHERE obs_id LIKE 'ob_fw%'"
    ).fetchall()
    con.close()
    out = []
    for r in rows:
        try:
            d = json.loads(r["content_plain"] or "{}")
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(d, dict):
            continue
        d["obs_id"] = r["obs_id"]
        out.append(d)
    return out


def _ingest(body: dict) -> None:
    """POST 一条胶囊·节流 + 429 指数退避重试。"""
    time.sleep(INGEST_THROTTLE_S)
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    for attempt in range(INGEST_MAX_RETRY):
        req = urllib.request.Request(
            SERVING_INGEST, data=data,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=20).read()
            return
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < INGEST_MAX_RETRY - 1:
                time.sleep(2 ** attempt)  # 1s,2s,4s 退避
                continue
            raise


def _load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        return set(open(SEEN_FILE, encoding="utf-8").read().split("\n")) - {""}
    return set()


def _save_seen(seen: set) -> None:
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(seen)))


def _rsync_cloud_to_t4() -> int:
    """补缺失的 cloud→T4 文件同步桥(daemon 读 T4·serving 写 cloud)。"""
    r = subprocess.run(
        [
            "rsync", "-a",
            "-e", f"ssh -o StrictHostKeyChecking=no -i {T4_KEY}",
            CAP_DIR, f"{T4_HOST}:{CAP_DIR}",
        ],
        capture_output=True, text=True,
    )
    return r.returncode


def main() -> None:
    obs = read_flywheel_obs()
    seen = _load_seen()
    try:
        stats = mb.consolidate(obs, _ingest, seen=seen)
    finally:
        _save_seen(seen)  # 部分失败也持久化已成功键·防重跑重 POST
    rc = _rsync_cloud_to_t4() if stats["written"] else 0
    print(json.dumps({
        "total_ob_fw": len(obs),
        "written": stats["written"],
        "skipped_gate": stats["skipped_gate"],
        "skipped_dup": stats["skipped_dup"],
        "rsync_rc": rc,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
