"""齿轮⑤ live runner:把飞轮 sqlite ob_fw learning 沉淀成胶囊并入 T4 文件语义库。

跑在 cloud(sqlite 本地 + 文件本地 + 有 T4 rsync key)。端到端路径(本 session 实证):
  sqlite ob_fw(content_plain JSON)→ memory_bridge.consolidate(过 W1 晋升门)
  → 直接渲染 capsule .md(复用 v14_ingest_obs 模板·绕开 serving 限流 429)
  → rsync cloud→T4(补缺失同步桥·corpus_sync 不存在)
  → T4 daemon inotify 索引 → /v1/v14/recall 语义可召回。
文件名 = content sha1(确定性·天然幂等·重跑覆盖同文件不产 dup)。

部署:scp 本文件 + memory_bridge.py 到 cloud → `python3 memory_bridge_runner.py`。
"""
import hashlib
import json
import os
import re
import sqlite3
import subprocess

import memory_bridge as mb

DB = "/var/lib/compass/compass.db"
CAP_DIR = "/home/ubuntu/.claude/projects/fleet-capsules/"
CAP_MEM_DIR = os.path.join(CAP_DIR, "memory")
T4_HOST = "ubuntu@43.166.8.20"
T4_KEY = os.path.expanduser("~/.ssh/id_ed25519_qb")


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


def _render_md(body: dict) -> str:
    """复用 v14_ingest_obs 的 session_*.md 模板(frontmatter + content)。"""
    name = body.get("name", "capsule")
    description = body.get("description", "")
    drift = body.get("drift", "green")
    tags = body.get("tags") or []
    tags_yaml = "[]" if not tags else "[" + ", ".join(f'"{t}"' for t in tags) + "]"
    content = body.get("content", "")
    return (
        f"---\nname: {name}\ndescription: {description}\ntype: discovery\n"
        f"drift: {drift}\nagent_type: fleet-capsule\ningested_via: memory_bridge_runner\n"
        f"tags: {tags_yaml}\n---\n\n# {name}\n\n{content[:8000]}\n"
    )


def _write_capsule_md(body: dict) -> None:
    """直接写 capsule .md 到 cloud 文件库(绕开 serving 限流)。文件名=content sha1(幂等)。"""
    os.makedirs(CAP_MEM_DIR, exist_ok=True)
    content = body.get("content", "")
    h = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^\w一-鿿]+", "-", body.get("name", "obs"))[:30].strip("-") or "obs"
    fname = f"session_capsule_{h}_{slug}.md"
    with open(os.path.join(CAP_MEM_DIR, fname), "w", encoding="utf-8") as f:
        f.write(_render_md(body))


def _rsync_cloud_to_t4() -> int:
    """补缺失的 cloud→T4 文件同步桥(daemon 读 T4·runner 写 cloud)。"""
    r = subprocess.run(
        ["rsync", "-a", "-e", f"ssh -o StrictHostKeyChecking=no -i {T4_KEY}",
         CAP_DIR, f"{T4_HOST}:{CAP_DIR}"],
        capture_output=True, text=True,
    )
    return r.returncode


def main() -> None:
    obs = read_flywheel_obs()
    seen: set = set()  # 文件名 content-hash 已幂等·seen 仅本轮统计去重
    stats = mb.consolidate(obs, _write_capsule_md, seen=seen)
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
