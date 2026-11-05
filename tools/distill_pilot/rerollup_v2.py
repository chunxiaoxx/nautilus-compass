#!/usr/bin/env python3
"""D5-A: 从存量分段纪要重做 rollup,验证召回修复(不重磨块层)。

三变体对拍(同源分段纪要,只变 rollup 层):
  v1     = 原版(已在 summaries_9b,基线,不重跑)
  v2prompt = 新 rollup prompt: 去字数硬顶 + 强制第五节"锚点索引"(模型侧保全)
  hybrid = v1 叙事不动 + 机械锚点索引追加(零模型参与,构造性保全)
产出: <sum-dir>/<id>.md(总纪要+锚点索引,无附录——附录在源文件)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from anchor_check import CJK_RE, collect_anchors  # noqa: E402
from compress_arm import SYSTEM_ROLLUP, hierarchical_rollup  # noqa: E402

SYSTEM_ROLLUP_V2 = (
    "把同一会话的多段纪要合并为一份总纪要。铁律: 只保留各段中有依据的内容,"
    "不添加段外信息。"
    "输出 markdown 五节: ## 事实与决策 / ## 命令与坐标 / ## 教训与异常 / ## 未决问题(没有则写: 无) / "
    "## 锚点索引——把各段纪要中出现过的**全部**文件路径/命令/日期/编号逐条原样列出,"
    "不得遗漏、不得改写、不得合并;宁多勿少。前四节务求精炼,锚点索引务求完整。"
)

APPENDIX_MARK = "## 附: 分段纪要"


def parse_chunks(summary_text: str) -> list[str]:
    idx = summary_text.find(APPENDIX_MARK)
    if idx < 0:
        return []
    body = summary_text[idx + len(APPENDIX_MARK):].strip()
    return [p.strip() for p in body.split("\n\n---\n\n") if p.strip()]


def mech_anchor_index(chunk_summaries: list[str], source_text: str) -> list[str]:
    """机械保全: 分段纪要锚点 ∩ 可回溯源文,去重排序——零模型,零幻觉。"""
    seen: dict[str, str] = {}
    for cs in chunk_summaries:
        for a in collect_anchors(cs):
            v = a["value"]
            if a["type"] == "path" and CJK_RE.search(v):
                continue
            if len(v) >= 6 and v in source_text:
                seen.setdefault(v, a["type"])
    return [f"- [{t}] {v}" for v, t in sorted(seen.items(), key=lambda x: x[1])]


def rerollup_one(src_md: Path, out_md: Path, api: str, model: str, variant: str) -> dict:
    started = time.time()
    text = src_md.read_text(encoding="utf-8", errors="replace")
    parts = parse_chunks(text)
    if not parts:
        return {"session_id": src_md.stem, "skip": "no-appendix"}
    src_txt = (src_md.parent.parent / "extracted" / f"{src_md.stem}.txt").read_text(encoding="utf-8", errors="replace")
    if variant == "v2prompt":
        final = hierarchical_rollup(parts, api, model, batch=6, system=SYSTEM_ROLLUP_V2)
        idx_lines = [l for l in final.splitlines() if l.strip().startswith("-") and "锚点索引" not in l]
        mech = mech_anchor_index(parts, src_txt)
        body = f"# D5 纪要(v2prompt) · {src_md.stem}\n\n{final}\n\n<!-- mech_n={len(mech)} -->"
    else:  # hybrid
        final = hierarchical_rollup(parts, api, model, batch=6, system=SYSTEM_ROLLUP)
        mech = mech_anchor_index(parts, src_txt)
        body = (
            f"# D5 纪要(hybrid) · {src_md.stem}\n\n{final}\n\n"
            f"## 锚点索引(机械保全,{len(mech)} 条)\n" + "\n".join(mech)
        )
    out_md.write_text(body, encoding="utf-8")
    return {
        "session_id": src_md.stem, "variant": variant, "n_chunks": len(parts),
        "mech_anchors": len(mech), "summary_bytes": len(body.encode()),
        "seconds": round(time.time() - started, 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--src-dir", default="summaries_9b")
    parser.add_argument("--sum-dir", required=True)
    parser.add_argument("--variant", choices=["v2prompt", "hybrid"], required=True)
    parser.add_argument("--api", default="http://127.0.0.1:8765/v1")
    parser.add_argument("--model", default="local")
    args = parser.parse_args()

    out = Path(args.out).expanduser()
    src_dir = out / args.src_dir
    dst = out / args.sum_dir
    dst.mkdir(parents=True, exist_ok=True)
    stats_path = out / f"rerollup_stats_{args.variant}.jsonl"

    todo = [p for p in sorted(src_dir.glob("*.md")) if not (dst / p.name).exists()]
    print(f"[{args.variant}] to rollup: {len(todo)}", file=sys.stderr)
    ok = 0
    for p in todo:
        try:
            stat = rerollup_one(p, dst / p.name, args.api, args.model, args.variant)
        except RuntimeError as exc:
            print(f"ERROR {p.stem}: {exc}", file=sys.stderr)
            continue
        with stats_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(stat, ensure_ascii=False) + "\n")
        ok += 1
        print(f"[{args.variant} {ok}/{len(todo)}] {p.stem[:8]} {stat.get('n_chunks',0)}块 "
              f"mech={stat.get('mech_anchors','?')} {stat.get('seconds','?')}s", file=sys.stderr)
    print(f"done {ok}/{len(todo)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
