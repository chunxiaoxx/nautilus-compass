#!/usr/bin/env python3
"""D2 压缩臂:分层蒸馏 extracted/*.txt -> summaries_local/*.md。

只走本地 llama-server(OpenAI 兼容 /v1/chat/completions),原文不出域。
分层: 消息块切块(不切断单条消息)→ 逐块纪要 → 汇总纪要;断点续跑(输出已存在即跳过)。
产出: summaries_local/<session_id>.md + compress_stats.jsonl(逐会话统计)。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SYSTEM_CHUNK = (
    "你是会话档案蒸馏器,把 AI agent 工作会话片段压缩成结构化纪要。"
    "铁律: 只陈述片段中有依据的事实; 文件路径/命令/日期/编号/md5 等锚点原样保留,"
    "不得改写或脑补; 不添加片段中没有的信息; 不评价。"
    "输出 markdown 四节: ## 事实与决策 / ## 命令与坐标(逐条) / ## 教训与异常 / ## 未决问题(没有则写: 无)。"
)
SYSTEM_ROLLUP = (
    "把同一会话的多段纪要合并为一份总纪要。铁律: 只保留各段中有依据的内容,"
    "所有文件路径/命令/日期/编号锚点原样保留; 去重合并; 不添加段外信息。"
    "输出 ≤1200 字 markdown,四节同上,并在节内按主题归并。"
)
SECRET_RES = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"cmp_[A-Za-z0-9_]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{16,}"),
]
MSG_SPLIT = "\n=== "


def scrub(text: str) -> str:
    """外发边界才用(本地落盘不 scrub,保锚点可回溯)。"""
    out = text
    for pattern in SECRET_RES:
        out = pattern.sub(lambda m: m.group(0)[:6] + "***", out)
    return out


def chat(api: str, model: str, system: str, user: str, max_tokens: int) -> str:
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{api.rstrip('/')}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"] or ""
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
            last_err = exc
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"chat failed after 3 attempts: {last_err}")


def split_chunks(text: str, chunk_chars: int) -> list[str]:
    """按消息边界切块,绝不切断单条消息;单条超长独占一块;拼回无损。"""
    parts = text.split(MSG_SPLIT)
    chunks: list[str] = []
    buf = ""
    for idx, part in enumerate(parts):
        piece = part if idx == 0 else MSG_SPLIT + part
        if buf and len(buf) + len(piece) > chunk_chars:
            chunks.append(buf)
            buf = piece
        else:
            buf += piece
    if buf.strip():
        chunks.append(buf)
    return chunks


def hierarchical_rollup(summaries: list[str], api: str, model: str, batch: int = 6) -> str:
    """块纪要超多时分层汇总(每 batch 份并一层),防 rollup 输入爆上下文。"""
    current = list(summaries)
    while len(current) > 1:
        nxt: list[str] = []
        for i in range(0, len(current), batch):
            group = current[i : i + batch]
            if len(group) == 1:
                nxt.append(group[0])
            else:
                joined = "\n\n---\n\n".join(group)
                nxt.append(chat(api, model, SYSTEM_ROLLUP, joined, 2500))
        current = nxt
    return current[0]


def compress_session(
    src: Path, out_path: Path, api: str, model: str, chunk_chars: int
) -> dict:
    started = time.time()
    text = src.read_text(encoding="utf-8", errors="replace")
    chunks = split_chunks(text, chunk_chars)
    part_summaries: list[str] = []
    for idx, chunk in enumerate(chunks, 1):
        user = f"【片段 {idx}/{len(chunks)}】\n{chunk}"
        part_summaries.append(chat(api, model, SYSTEM_CHUNK, user, 2000))
    if len(part_summaries) == 1:
        final = part_summaries[0]
    else:
        final = hierarchical_rollup(part_summaries, api, model)
    body = (
        f"# 蒸馏纪要 · {src.stem}\n\n"
        f"- 源: extracted/{src.name} ({src.stat().st_size:,}B, {len(chunks)} 块)\n"
        f"- 生成: {time.strftime('%Y-%m-%dT%H:%M:%S')} · 本地压缩臂(原文不出域)\n\n"
        f"{final}\n\n## 附: 分段纪要\n\n" + "\n\n---\n\n".join(part_summaries)
    )
    out_path.write_text(body, encoding="utf-8")
    return {
        "session_id": src.stem,
        "source_bytes": src.stat().st_size,
        "n_chunks": len(chunks),
        "summary_bytes": len(body.encode("utf-8")),
        "seconds": round(time.time() - started, 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:8765/v1")
    parser.add_argument("--model", default="local")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--groups", default="A_recent_active,B_high_value")
    parser.add_argument("--chunk-chars", type=int, default=18000)
    parser.add_argument("--sum-dir", default="summaries_local", help="纪要输出子目录(9B 臂用 summaries_9b)")
    parser.add_argument("--limit", type=int, default=0, help="只跑前 N 个(验证用)")
    parser.add_argument("--only", default="", help="只跑指定 session_id(逗号分隔)")
    args = parser.parse_args()

    out_dir = Path(args.out).expanduser()
    sum_dir = out_dir / args.sum_dir
    sum_dir.mkdir(parents=True, exist_ok=True)
    stats_path = out_dir / f"compress_stats_{args.sum_dir}.jsonl"

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    wanted = set(args.groups.split(","))
    only = {x for x in args.only.split(",") if x}
    todo: list[tuple[str, Path]] = []
    for group, entries in manifest["groups"].items():
        if group not in wanted:
            continue
        for entry in entries:
            sid = entry["session_id"]
            if only and sid not in only:
                continue
            out_file = sum_dir / f"{sid}.md"
            if out_file.exists():  # 断点续跑
                continue
            todo.append((group, out_dir / "extracted" / f"{sid}.txt"))

    if args.limit:
        todo = todo[: args.limit]
    print(f"to compress: {len(todo)} sessions", file=sys.stderr)

    ok = 0
    for group, src in todo:
        if not src.exists():
            print(f"warn: missing {src}", file=sys.stderr)
            continue
        try:
            stat = compress_session(src, sum_dir / f"{src.stem}.md", args.api, args.model, args.chunk_chars)
        except RuntimeError as exc:
            print(f"ERROR session {src.stem}: {exc} — 跳过继续", file=sys.stderr)
            with stats_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"session_id": src.stem, "group": group, "error": str(exc)}, ensure_ascii=False) + "\n")
            continue
        stat["group"] = group
        with stats_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(stat, ensure_ascii=False) + "\n")
        ok += 1
        print(f"[{ok}/{len(todo)}] {src.stem} {stat['n_chunks']}块 {stat['seconds']}s", file=sys.stderr)
    print(f"done: {ok}/{len(todo)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
