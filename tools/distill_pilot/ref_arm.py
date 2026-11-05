#!/usr/bin/env python3
"""D3 参考臂:同一批会话用 API 强模型(glm-5.3 经 api.chunxiao.wang newapi)蒸馏,与本地臂对拍(J3/J6)。

- 外发前 scrub 脱敏(sk-/cmp_/ghp_/Bearer 前缀截断)——红线:验证臂/参考臂只送脱敏文本
- 与 compress_arm 同 prompt/同切块/同层级汇总,输出 summaries_ref/<id>.md
- key 运行时读环境变量 COMPASS_WRITER_KEY,不落代码
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compress_arm import (  # noqa: E402
    SYSTEM_CHUNK,
    SYSTEM_ROLLUP,
    scrub,
    split_chunks,
)

API_URL = "https://api.chunxiao.wang/v1/messages"


def chat_anthropic(system: str, user: str, key: str, model: str, max_tokens: int, base_url: str | None = None, temperature: float = 0.2) -> str:
    payload = json.dumps({
        "model": model,
        "max_tokens": max(8000, max_tokens),  # 思考型模型:reasoning 先吃预算,地板 8000(8/31 doubao 陷阱同款)
        "system": system,
        "messages": [{"role": "user", "content": user}],
        "temperature": temperature,
        "thinking": {"type": "disabled"},
    }).encode("utf-8")
    req = urllib.request.Request(
        base_url or API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": key,
            "Authorization": f"Bearer {key}",
            "anthropic-version": "2023-06-01",
        },
    )
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = "".join(
                block.get("text", "")
                for block in data.get("content", [])
                if block.get("type") == "text"
            )
            if not text:
                last_err = RuntimeError(f"empty text, stop={data.get('stop_reason')}")
                time.sleep(3)
                continue
            return text
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
            last_err = exc
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"anthropic chat failed: {last_err}")


def compress_ref(src: Path, out_path: Path, key: str, model: str, chunk_chars: int) -> dict:
    started = time.time()
    text = scrub(src.read_text(encoding="utf-8", errors="replace"))
    chunks = split_chunks(text, chunk_chars)
    parts = [
        chat_anthropic(SYSTEM_CHUNK, f"【片段 {i}/{len(chunks)}】\n{c}", key, model, 2000)
        for i, c in enumerate(chunks, 1)
    ]
    if len(parts) == 1:
        final = parts[0]
    else:
        # 参考臂只跑 ≤3 块小会话,一层汇总足够
        final = chat_anthropic(
            SYSTEM_ROLLUP, "\n\n---\n\n".join(parts), key, model, 3000
        )
    body = (
        f"# 参考臂纪要 · {src.stem}\n\n"
        f"- 源: extracted/{src.name} ({src.stat().st_size:,}B, {len(chunks)} 块, 脱敏后)\n"
        f"- 生成: {time.strftime('%Y-%m-%dT%H:%M:%S')} · {model} 参考臂\n\n"
        f"{final}\n\n## 附: 分段纪要\n\n" + "\n\n---\n\n".join(parts)
    )
    out_path.write_text(body, encoding="utf-8")
    return {
        "session_id": src.stem,
        "n_chunks": len(chunks),
        "summary_bytes": len(body.encode("utf-8")),
        "seconds": round(time.time() - started, 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model", default="glm-5.3")
    parser.add_argument("--n", type=int, default=10, help="参考臂会话数(选最小的)")
    parser.add_argument("--max-chunks", type=int, default=3, help="只选 ≤N 块的会话控成本")
    parser.add_argument("--chunk-chars", type=int, default=14000)
    args = parser.parse_args()

    key = os.environ.get("COMPASS_WRITER_KEY", "")
    if not key:
        print("缺 COMPASS_WRITER_KEY 环境变量", file=sys.stderr)
        return 2

    out_dir = Path(args.out).expanduser()
    ref_dir = out_dir / "summaries_ref"
    ref_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    cands = []
    for group, entries in manifest["groups"].items():
        if group == "C_patrol_control":
            continue
        for e in entries:
            p = out_dir / "extracted" / f"{e['session_id']}.txt"
            if p.exists() and not (ref_dir / f"{e['session_id']}.md").exists():
                est = p.stat().st_size // args.chunk_chars + 1
                if est <= args.max_chunks:
                    cands.append((p.stat().st_size, group, p))
    cands.sort()
    todo = cands[: args.n]
    print(f"参考臂选样 {len(todo)}: {[(g, p.stem[:8]) for _, g, p in todo]}", file=sys.stderr)

    stats = []
    for _, group, src in todo:
        stat = compress_ref(src, ref_dir / f"{src.stem}.md", key, args.model, args.chunk_chars)
        stat["group"] = group
        stats.append(stat)
        print(f"[ref] {src.stem[:8]} {stat['n_chunks']}块 {stat['seconds']}s", file=sys.stderr)
    (out_dir / "ref_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"done {len(stats)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
