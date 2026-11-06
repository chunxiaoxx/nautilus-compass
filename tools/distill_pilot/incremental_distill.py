#!/usr/bin/env python3
"""增量蒸馏通道(持续模式)·9B 生产臂。

流程: 扫描桶内新落盘 jsonl(比水位新·≥10KB·非值守轮·非在写)→ 9B 蒸馏 → J1 锚点核验
     → 过门纪要入 summaries_9b/,不过门标 review → 水位推进。
服务治理: 批内有活才起 llama-server,批完即停(白天不常驻 6GB)。
门禁: runtime/scratch_distill_pilot_20261104/DISTILL_GREEN 不存在=未定谳,直接退出(--force 可越过)。
launchd: com.nautilus.distill-incremental(2h 一轮)。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from anchor_check import check  # noqa: E402
from compress_arm import compress_session  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RUNTIME = REPO / "runtime/scratch_distill_pilot_20261104"
BUCKET = Path.home() / ".claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass"
PATROL_RE = re.compile(r"值守|轮值|LOOP 轮|loop 轮指令", re.IGNORECASE)
MIN_SIZE = 10_000
WRITING_WINDOW = 1800  # 30 分钟内仍在写的会话不碰
SERVER_CMD = [
    "llama-server", "-m", str(Path.home() / "models/distill/Qwen3.5-9B-Q4_K_M.gguf"),
    "--host", "127.0.0.1", "--port", "8765", "-c", "32768", "-ngl", "99",
    "--chat-template-kwargs", '{"enable_thinking": false}',
]


def light_first_user(path: Path) -> str:
    """只读文件头部拿首条用户消息(轻量,不全量扫描)。"""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for _ in range(400):
                line = fh.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "user" or obj.get("isMeta"):
                    continue
                msg = obj.get("message") or {}
                c = msg.get("content")
                texts = [c] if isinstance(c, str) else [
                    b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"
                ] if isinstance(c, list) else []
                text = " ".join(t for t in texts if t).strip()
                if text:
                    return text[:200]
    except OSError:
        pass
    return ""


def server_up() -> bool:
    try:
        subprocess.run(["curl", "-s", "--max-time", "3", "http://127.0.0.1:8765/v1/models"],
                       capture_output=True, timeout=5)
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8765/v1/models", timeout=3)
        return True
    except Exception:
        return False


def ensure_server() -> subprocess.Popen | None:
    if server_up():
        return None
    log = open(RUNTIME / "llama_server_incr.log", "a")
    proc = subprocess.Popen(SERVER_CMD, stdout=log, stderr=log, start_new_session=True)
    for _ in range(90):
        if server_up():
            return proc
        time.sleep(2)
    raise RuntimeError("llama-server 起不来(90s)")


def stop_server() -> None:
    subprocess.run(["pkill", "-f", "llama-server.*8765"], capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="越过 GREEN 门禁(定谳前测试用)")
    args = parser.parse_args()

    green = (RUNTIME / "DISTILL_GREEN").exists()
    if not (green or args.force):
        print("GATED: DISTILL_GREEN 不在(D5 未定谳),本轮跳过", file=sys.stderr)
        return 0

    wm_path = RUNTIME / "watermark.json"
    watermark = json.loads(wm_path.read_text())["mtime"] if wm_path.exists() else 0
    now = time.time()
    done = {p.stem for p in (RUNTIME / "summaries_9b").glob("*.md")}

    queue = []
    max_mtime = watermark
    for p in sorted(BUCKET.glob("*.jsonl")):
        try:
            st = p.stat()
        except OSError:
            continue
        if st.st_size < MIN_SIZE or p.stem in done:
            continue
        if st.st_mtime <= watermark:
            continue
        if now - st.st_mtime < WRITING_WINDOW:
            continue  # 在写
        max_mtime = max(max_mtime, st.st_mtime)
        if PATROL_RE.search(light_first_user(p)):
            continue  # 值守轮定义性过滤(J5 口径)
        queue.append(p)

    print(f"水位 {time.strftime('%m-%d %H:%M', time.localtime(watermark))} → 新增待蒸馏 {len(queue)}", file=sys.stderr)
    if args.dry_run or not queue:
        if not args.dry_run and max_mtime > watermark:
            wm_path.write_text(json.dumps({"mtime": max_mtime}))
        return 0

    proc = ensure_server()
    try:
        for p in queue:
            src = RUNTIME / "extracted" / f"{p.stem}.txt"
            src.parent.mkdir(exist_ok=True)
            # 增量也走抽取器,保口径一致
            from extract_sample import extract_file
            extract_file(p, src)
            out = RUNTIME / "summaries_9b" / f"{p.stem}.md"
            stat = compress_session(src, out, "http://127.0.0.1:8765/v1", "local", 14000)
            r = check(out.read_text(encoding="utf-8", errors="replace"),
                      src.read_text(encoding="utf-8", errors="replace"))
            stat["j1"] = r["traceable_rate"]
            stat["gate"] = "ok" if (r["traceable_rate"] or 0) >= 0.95 else "review"
            if stat["gate"] == "ok":
                # 生产形态: 锚点 sidecar(源文直提) + 发布进 memory → recall 闭环
                import subprocess as _sp
                from collections import Counter as _C
                from anchor_check import collect_anchors as _ca, CJK_RE as _CJK
                s_txt = src.read_text(encoding="utf-8", errors="replace")
                _cnt = _C(a["value"] for a in _ca(s_txt)
                          if a["type"] in ("path", "date", "tag_id", "url") and not _CJK.search(a["value"]))
                (RUNTIME / "summaries_9b_prod").mkdir(exist_ok=True)
                (RUNTIME / "summaries_9b_prod" / f"{p.stem}.md").write_text(
                    out.read_text(encoding="utf-8", errors="replace").split("## 附")[0], encoding="utf-8")
                (RUNTIME / "summaries_9b_prod" / f"{p.stem}.anchors.txt").write_text(
                    "\n".join(sorted(v for v, c in _cnt.items() if c >= 3)), encoding="utf-8")
                _sp.run([sys.executable, str(Path(__file__).parent / "publish_to_memory.py"),
                         "--only", p.stem], capture_output=True)
            with (RUNTIME / "incremental_stats.jsonl").open("a") as fh:
                fh.write(json.dumps(stat, ensure_ascii=False) + "\n")
            print(f"[incr] {p.stem[:8]} j1={stat['j1']} {stat['gate']}", file=sys.stderr)
    finally:
        if proc is not None:
            stop_server()
    if max_mtime > watermark:
        wm_path.write_text(json.dumps({"mtime": max_mtime}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
