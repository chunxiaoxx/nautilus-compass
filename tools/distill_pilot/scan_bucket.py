#!/usr/bin/env python3
"""D1 选样扫描:扫 compass 会话桶,产出 bucket_stats.json + sample_manifest.json。

分组(SESSION_DISTILL_PILOT_20261104 §二):
  A 20 = 近 30 天活跃(mtime 倒序,>10KB,排除最近 10 分钟仍在写的会话)
  B 20 = 历史高价值(handoff-*.md 的 originSessionId 优先,>20MB 大会话补足)
  C 10 = 值守轮负对照(首条用户消息含值守/round 签名优先,>1MB 最低正文比补足)
只读原始 jsonl,产物只写 out 目录。纯 stdlib。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

PATROL_RE = re.compile(r"值守|轮值|loop 轮|R\d{3}|patrol", re.IGNORECASE)
FRESH_WINDOW_SEC = 600          # 正在写入的会话不选
MIN_SIZE = 10_000               # <10KB 琐碎会话不进 A/B
BIG_SIZE = 20_000_000           # B 组大会话线
C_MIN_SIZE = 1_000_000          # C 组体积线
THIRTY_DAYS = 30 * 86400


@dataclass
class SessionStat:
    path: str
    session_id: str
    size: int
    mtime_epoch: float
    n_lines: int = 0
    n_user_text: int = 0
    n_asst_text: int = 0
    user_text_bytes: int = 0
    asst_text_bytes: int = 0
    first_user_snippet: str = ""
    n_anchors_hint: int = 0


def iter_text(content: object) -> list[str]:
    """取消息 content 里的纯文本块(跳过 tool_use/tool_result/image/thinking)。"""
    if isinstance(content, str):
        return [content] if content else []
    out: list[str] = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    out.append(text)
    return out


def scan_file(path: Path) -> SessionStat:
    stat = SessionStat(
        path=str(path),
        session_id=path.stem,
        size=path.stat().st_size,
        mtime_epoch=path.stat().st_mtime,
    )
    first_user: list[str] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                stat.n_lines += 1
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg_type = obj.get("type")
                if msg_type not in ("user", "assistant"):
                    continue
                message = obj.get("message") or {}
                texts = iter_text(message.get("content"))
                nbytes = sum(len(t.encode("utf-8")) for t in texts)
                if msg_type == "user":
                    if texts:
                        stat.n_user_text += 1
                        stat.user_text_bytes += nbytes
                        if len(first_user) < 3 and not obj.get("isMeta"):
                            first_user.append(" ".join(t.strip() for t in texts)[:200])
                elif texts:
                    stat.n_asst_text += 1
                    stat.asst_text_bytes += nbytes
    except OSError as exc:
        print(f"warn: {path.name}: {exc}", file=sys.stderr)
    stat.first_user_snippet = " | ".join(first_user)[:300]
    return stat


def handoff_session_ids(memory_dir: Path) -> set[str]:
    """从 memory/handoff-*.md frontmatter 提取 originSessionId。"""
    ids: set[str] = set()
    if not memory_dir.is_dir():
        return ids
    pattern = re.compile(r"originSessionId:\s*([0-9a-zA-Z-]{8,})")
    for md in memory_dir.glob("handoff-*.md"):
        try:
            head = md.read_text(encoding="utf-8", errors="replace")[:2500]
        except OSError:
            continue
        ids.update(pattern.findall(head))
    return ids


def text_ratio(stat: SessionStat) -> float:
    if stat.size <= 0:
        return 0.0
    return (stat.user_text_bytes + stat.asst_text_bytes) / stat.size


def select_sample(
    stats: list[SessionStat], handoff_ids: set[str], now: float
) -> dict[str, list[dict]]:
    pool = [
        s for s in stats
        if s.size >= MIN_SIZE and now - s.mtime_epoch > FRESH_WINDOW_SEC
    ]
    fresh_cut = now - THIRTY_DAYS

    group_a = sorted(
        (s for s in pool if s.mtime_epoch >= fresh_cut),
        key=lambda s: s.mtime_epoch,
        reverse=True,
    )[:20]
    used = {s.session_id for s in group_a}

    b_linked = [
        s for s in pool
        if s.session_id in handoff_ids and s.session_id not in used
    ]
    b_big = sorted(
        (s for s in pool if s.size > BIG_SIZE and s.session_id not in used),
        key=lambda s: s.size,
        reverse=True,
    )
    b_mid = sorted(
        (s for s in pool if 5_000_000 < s.size <= BIG_SIZE and s.session_id not in used),
        key=lambda s: s.size,
        reverse=True,
    )
    group_b: list[SessionStat] = []
    seen: set[str] = set()
    for stat, reason in [
        *((s, "handoff-linked") for s in b_linked),
        *((s, "big>20MB") for s in b_big),
        *((s, "mid5-20MB") for s in b_mid),
    ]:
        if stat.session_id in seen or stat.session_id in used:
            continue
        seen.add(stat.session_id)
        group_b.append(stat)
        stat.n_anchors_hint = 0
        if len(group_b) == 20:
            break
    used |= {s.session_id for s in group_b}

    c_patrol = [
        s for s in pool
        if s.session_id not in used and PATROL_RE.search(s.first_user_snippet)
    ]
    c_low = sorted(
        (s for s in pool if s.session_id not in used and s.size > C_MIN_SIZE),
        key=text_ratio,
    )
    group_c: list[SessionStat] = []
    seen_c: set[str] = set()
    for stat, reason in [
        *((s, "patrol-signature") for s in c_patrol),
        *((s, "lowest-text-ratio") for s in c_low),
    ]:
        if stat.session_id in seen_c or stat.session_id in used:
            continue
        seen_c.add(stat.session_id)
        group_c.append(stat)
        if len(group_c) == 10:
            break

    def entry(stat: SessionStat, reason: str) -> dict:
        d = asdict(stat)
        d["reason"] = reason
        d["text_ratio"] = round(text_ratio(stat), 4)
        return d

    return {
        "A_recent_active": [entry(s, "mtime-top20-30d") for s in group_a],
        "B_high_value": [
            entry(
                s,
                "handoff-linked"
                if s.session_id in handoff_ids
                else ("big>20MB" if s.size > BIG_SIZE else "mid5-20MB"),
            )
            for s in group_b
        ],
        "C_patrol_control": [
            entry(
                s,
                "patrol-signature"
                if PATROL_RE.search(s.first_user_snippet)
                else "lowest-text-ratio",
            )
            for s in group_c
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", required=True, help="会话桶目录(只读)")
    parser.add_argument("--memory-dir", required=True, help="memory 目录(读 handoff 映射)")
    parser.add_argument("--out", required=True, help="产物目录")
    args = parser.parse_args()

    bucket = Path(args.bucket).expanduser()
    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(bucket.glob("*.jsonl"))
    print(f"scanning {len(files)} jsonl in {bucket} ...", file=sys.stderr)
    stats = [scan_file(p) for p in files]

    handoff_ids = handoff_session_ids(Path(args.memory_dir).expanduser())
    print(f"handoff-linked session ids: {len(handoff_ids)}", file=sys.stderr)

    stats_path = out_dir / "bucket_stats.json"
    stats_path.write_text(
        json.dumps([asdict(s) for s in stats], ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    groups = select_sample(stats, handoff_ids, time.time())
    manifest = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "bucket": str(bucket),
        "group_sizes": {k: len(v) for k, v in groups.items()},
        "groups": groups,
    }
    manifest_path = out_dir / "sample_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(
        f"stats -> {stats_path}\nmanifest -> {manifest_path} "
        f"({manifest['group_sizes']})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
