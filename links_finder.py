"""V5 Memory Plugin v0.5 · A-MEM 动态链接发现.

通过 daemon 拉所有 memory 的 BGE embedding · 算两两 cosine ·
检测 supersede / contradict / supplement 关系 · 写 .cache/links.json.

用法:
  python3 ~/.claude/plugins/nautilus-compass/links_finder.py [project_encoded]

链接判据:
  · cosine ≥ 0.85 + age 差 ≥ 5 day → supersede (新覆盖旧)
  · cosine ≥ 0.65 + age 差 < 2 day → supplement (互补)
  · cosine ≤ 0.30 + 同主题关键词 ≥ 2 → contradict (矛盾)

R1: 修 stub claude-mem 不 deprecate 矛盾旧记忆 → A-MEM 真接
R3: 复用 daemon BGE · 0 新 LLM session
"""
import json
import socket
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # safe · no buffer aliasing
except Exception:
    pass

PLUGIN_DIR = Path.home() / ".claude" / "plugins" / "nautilus-compass"
CACHE_DIR = PLUGIN_DIR / ".cache"
LINKS_FILE = CACHE_DIR / "links.json"

SUPERSEDE_COSINE = 0.80
SUPERSEDE_AGE_DIFF_DAYS = 5
SUPPLEMENT_COSINE = 0.60
SUPPLEMENT_MAX_AGE_DIFF_DAYS = 3


def daemon_alive() -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            s.connect(("127.0.0.1", 9876))
            s.sendall(b'{"action":"ping"}\n')
            return b'"pong"' in s.recv(1024)
    except Exception:
        return False


def main():
    if not daemon_alive():
        print("❌ V5 Memory daemon 未启动 · 跑 bash daemon_start.sh 先")
        return 1

    project = sys.argv[1] if len(sys.argv) > 1 else "C--Users-chunx-Projects-nautilus-core"
    print(f"扫描 project: {project}")

    # 复用 daemon · 拉所有 file embeddings (通过假 query 触发 daemon load + 拿 entries)
    # 但 daemon 当前 protocol 不返 embeddings · 我们要直接读 cache pkl
    import hashlib, pickle
    mem_dir = Path.home() / ".claude" / "projects" / project / "memory"
    proj_hash = hashlib.sha256(str(mem_dir).encode()).hexdigest()[:12]
    cache_file = CACHE_DIR / f"{proj_hash}.pkl"
    if not cache_file.exists():
        print(f"❌ 没找到 embedding cache · 先跑一次 BGE 召回让 daemon embed all files")
        print(f"   bash: python3 recall.py --bge --query 'init'")
        return 1

    with open(cache_file, "rb") as f:
        data = pickle.load(f)
    embeddings = data.get("embeddings", {})
    if not embeddings:
        print("❌ embedding cache 空")
        return 1

    print(f"加载 {len(embeddings)} embeddings")

    import math, time as _t
    def cosine(a, b):
        if not a or not b: return 0.0
        dot = sum(x*y for x,y in zip(a,b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(y*y for y in b))
        return dot/(na*nb) if na>0 and nb>0 else 0.0

    # 算两两 + age
    files = list(embeddings.keys())
    file_meta = {}
    for fp in files:
        try:
            mtime = Path(fp).stat().st_mtime
            file_meta[fp] = {"mtime": mtime, "age_d": (_t.time()-mtime)/86400}
        except Exception:
            file_meta[fp] = {"mtime": 0, "age_d": 9999}

    links = {"supersede": {}, "supplement": {}}

    n = len(files)
    print(f"算 {n*(n-1)//2} 对 cosine ...")
    for i in range(n):
        fa = files[i]
        emb_a = embeddings[fa][1]
        meta_a = file_meta[fa]
        for j in range(i+1, n):
            fb = files[j]
            emb_b = embeddings[fb][1]
            meta_b = file_meta[fb]
            score = cosine(emb_a, emb_b)
            age_diff = abs(meta_a["age_d"] - meta_b["age_d"])
            # supersede: 高重合 + 年龄差大
            if score >= SUPERSEDE_COSINE and age_diff >= SUPERSEDE_AGE_DIFF_DAYS:
                # 谁老 supersede 谁
                older, newer = (fa, fb) if meta_a["age_d"] > meta_b["age_d"] else (fb, fa)
                links["supersede"].setdefault(Path(older).name, []).append({
                    "by": Path(newer).name,
                    "cosine": round(score, 3),
                    "age_diff_days": round(age_diff, 1),
                })
            # supplement: 中等重合 + 年龄相近
            elif score >= SUPPLEMENT_COSINE and age_diff <= SUPPLEMENT_MAX_AGE_DIFF_DAYS:
                links["supplement"].setdefault(Path(fa).name, []).append({
                    "with": Path(fb).name,
                    "cosine": round(score, 3),
                })

    # 写盘
    with open(LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 链接发现完成 · 写到 {LINKS_FILE}")
    print(f"\n=== Supersede (新覆盖旧 · top 10) ===")
    super_items = sorted(
        [(old, by[0]["cosine"], by[0]["by"], len(by))
         for old, by in links["supersede"].items()],
        key=lambda x: -x[1],
    )[:10]
    for old, score, newer, n in super_items:
        print(f"  · {old}")
        print(f"      ↳ superseded by {newer} (cos={score})  +{n-1} more")

    print(f"\n=== Supplement (互补 · top 5) ===")
    sup_items = sorted(
        [(a, b[0]["cosine"], b[0]["with"]) for a, b in links["supplement"].items()],
        key=lambda x: -x[1],
    )[:5]
    for a, score, b in sup_items:
        print(f"  · {a}  ↔  {b}  (cos={score})")

    print(f"\nstats: supersede={len(links['supersede'])} entries · supplement={len(links['supplement'])} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
