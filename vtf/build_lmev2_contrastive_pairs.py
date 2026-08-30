"""LME-V2 刀3 · 对比微调训练对自动构造(纯本地 CPU,不碰 GPU).

从 LME-V2 evidence 与/或原始轨迹构造 bge-m3 域适配训练对:
- query   = 题干(question_text)
- 正例    = 含 answer_gold 的 state 段(优先原始轨迹源,全轨迹可匹配;
            否则退到检回窗口内 evidence 源)
- 难负例  = 相关轨迹中与题干词面重叠最高但不含 gold 的 state 段
           (对偶"检回正确轨迹、错误片段"病灶:负例长得像答案段却不是)

state 文本构造与 lmev2_compass_memory.py 部署栈同款(url/action/thought +
a11y 剪枝 500 截断 + state 1200 截断),防 train/serve skew。

过滤规则(两模式同):
- abstention 题(is_abstention_problem=True)跳过——gold 是解释性元文本
- bool gold(true/false 字面)跳过——段级 substring 匹配假阳性高
- gold 归一后 < min_gold_len 跳过(轨迹模式相关轨迹仅数条,短 gold 假阳性
  可控,可用 --min-gold-len 3 放开)

输出 JSONL: {"question_id","domain","traj_id","query","pos","neg_hard":[...],
"gold_len","pos_source"} — 兼容 sentence-transformers MNRL(query,positive)
与加难负例的三列变体(训练侧自行选用 neg_hard)。

用法(轨迹源优先,evidence 兜底):
  python vtf/build_lmev2_contrastive_pairs.py \
    --evidence vtf/_compass_lmev2_out/compass_web_small/per_question.jsonl:web \
               vtf/_compass_lmev2_out/compass_enterprise_small/per_question.jsonl:enterprise \
    --trajectories vtf/_compass_lmev2_out/lmev2_traj_subset.jsonl \
    --out vtf/_compass_lmev2_out/contrastive_pairs_v2.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_BOOL_GOLDS = {"true", "false"}
_TRAJ_RE = re.compile(r"\[trajectory ([0-9a-f]+)")
_STATE_RE = re.compile(r"(?:^|\n)state (\d+): ")
_WORD_RE = re.compile(r"[\w]+")
# 与 lmev2_compass_memory.py 部署栈同款(UI 树空结构行剪枝)
_A11Y_NOISE_RE = re.compile(r"\[\d+\] \w+ ''")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _prune_a11y(a11y: str, max_chars: int) -> str:
    lines = [ln for ln in a11y.splitlines() if not _A11Y_NOISE_RE.search(ln)]
    return "\n".join(lines)[:max_chars]


def _state_text(state: dict, max_a11y_chars: int, max_chars: int) -> str:
    url = str(state.get("url") or "")
    action = str(state.get("action") or "")
    thought = str(state.get("thought") or "")
    a11y = _prune_a11y(str(state.get("accessibility_tree") or ""), max_a11y_chars)
    parts = []
    if url:
        parts.append(f"url: {url}")
    if action:
        parts.append(f"action: {action}")
    if thought:
        parts.append(f"thought: {thought}")
    if a11y:
        parts.append(f"page: {a11y}")
    return " | ".join(parts).strip()[:max_chars]


def _lexical_overlap(query_tokens: set[str], text: str) -> int:
    return len(query_tokens & set(_WORD_RE.findall(text.lower())))


def _split_blocks(memory_context: list) -> list[tuple[str, str, list[str]]]:
    """memory_context(list of {type,value}) -> [(traj_id, header, [state_texts])]."""
    out: list[tuple[str, str, list[str]]] = []
    for item in memory_context:
        if not isinstance(item, dict) or item.get("type") != "text":
            continue
        value = str(item.get("value", ""))
        m = _TRAJ_RE.search(value)
        if not m:
            continue
        traj_id = m.group(1)
        hits = list(_STATE_RE.finditer(value))
        if not hits:
            out.append((traj_id, value, []))
            continue
        header = value[: hits[0].start()].strip()
        states = [
            value[h.end() : (hits[i + 1].start() if i + 1 < len(hits) else len(value))].strip()
            for i, h in enumerate(hits)
        ]
        out.append((traj_id, header, states))
    return out


def _match_pair(
    query: str,
    gold: str,
    scope: list[tuple[str, str, bool]],
    max_neg: int,
    pos_max_chars: int,
    drop: dict[str, int] | None = None,
) -> dict | None:
    """scope = [(traj_id, state_text, in_scope)]; 命中即组对,否则 None."""

    def _bump(reason: str) -> None:
        if drop is not None:
            drop[reason] = drop.get(reason, 0) + 1

    gold_n = _norm(gold)
    q_tokens = set(_WORD_RE.findall(query.lower()))
    pos_seen: set[str] = set()
    best: tuple[str, str, str] | None = None  # (traj_id, pos_text, source)
    negs: list[tuple[int, str, str]] = []  # (overlap, traj_id, state_text)

    for traj_id, text, in_scope in scope:
        text_n = _norm(text)
        if not text_n or text_n in pos_seen:
            continue
        if gold_n in text_n:
            pos_seen.add(text_n)
            if best is None or len(text) < len(best[1]):
                best = (traj_id, text[:pos_max_chars], "traj" if in_scope else "adjacent")
        elif in_scope:
            negs.append((_lexical_overlap(q_tokens, text), traj_id, text))

    if best is None:
        _bump("gold_not_found")
        return None
    if not negs:
        _bump("no_neg_available")
        return None
    negs.sort(key=lambda t: -t[0])
    hard = [st[:pos_max_chars] for _, _, st in negs[:max_neg]]
    return {
        "traj_id": best[0],
        "query": query,
        "pos": best[1],
        "neg_hard": hard,
        "gold_len": len(gold_n),
        "pos_source": best[2],
    }


def _pair_from_row(
    row: dict,
    domain: str,
    trajs: dict[str, list[str]] | None,
    args,
    drop: dict[str, int],
) -> dict | None:
    if row.get("is_abstention_problem"):
        drop["abstention"] = drop.get("abstention", 0) + 1
        return None
    gold_raw = row.get("answer_gold")
    if gold_raw is None:
        drop["gold_none"] = drop.get("gold_none", 0) + 1
        return None
    gold = str(gold_raw)
    if _norm(gold) in _BOOL_GOLDS:
        drop["bool_gold"] = drop.get("bool_gold", 0) + 1
        return None
    if len(_norm(gold)) < args.min_gold_len:
        drop["gold_too_short"] = drop.get("gold_too_short", 0) + 1
        return None
    query = str(row.get("question_text") or "").strip()
    if not query:
        drop["no_query"] = drop.get("no_query", 0) + 1
        return None

    haystack = set(row.get("haystack_ids") or [])
    scope: list[tuple[str, str, bool]] = []

    if trajs:
        # 轨迹源:相关轨迹(haystack 内)全 state + 邻近轨迹排除
        for traj_id in haystack:
            for st in trajs.get(traj_id, []):
                scope.append((traj_id, st, True))
        if not scope:
            drop["traj_missing"] = drop.get("traj_missing", 0) + 1
    else:
        # evidence 源:检回窗口内切块
        for traj_id, _header, states in _split_blocks(row.get("memory_context") or []):
            in_scope = not haystack or traj_id in haystack
            for st in states:
                if st:
                    scope.append((traj_id, st, in_scope))

    pair = _match_pair(query, gold, scope, args.max_neg, args.pos_max_chars, drop)
    if pair:
        pair["question_id"] = row.get("question_id")
        pair["domain"] = domain
        pair = {
            "question_id": pair["question_id"],
            "domain": domain,
            **pair,
        }
    return pair


def _load_trajectories(path: Path) -> dict[str, list[str]]:
    """subset jsonl -> {traj_id: [state_texts]}(与部署栈同款文本构造)."""
    trajs: dict[str, list[str]] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            texts = [
                _state_text(st, max_a11y_chars=500, max_chars=1200)
                for st in (d.get("states") or [])
                if isinstance(st, dict)
            ]
            trajs[str(d.get("id"))] = [t for t in texts if t]
    return trajs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--evidence", nargs="+", required=True,
        help="per_question.jsonl 路径[:域名] 可多份",
    )
    ap.add_argument(
        "--trajectories",
        help="轨迹 subset jsonl(由 lmev2_traj_ids.json 过滤生成);给了则优先轨迹源",
    )
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-neg", type=int, default=3)
    ap.add_argument("--pos-max-chars", type=int, default=1200)
    ap.add_argument("--min-gold-len", type=int, default=5)
    args = ap.parse_args()

    trajs = _load_trajectories(Path(args.trajectories)) if args.trajectories else None
    if trajs:
        print(f"trajectories loaded: {len(trajs)} trajs")

    pairs: list[dict] = []
    stats: dict[str, dict] = {}
    for spec in args.evidence:
        path, _, domain = spec.rpartition(":")
        path = path or spec
        domain = domain or Path(path).stem
        total = kept = 0
        drop: dict[str, int] = {}
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            total += 1
            p = _pair_from_row(json.loads(line), domain, trajs, args, drop)
            if p:
                kept += 1
                pairs.append(p)
        stats[domain] = {"rows": total, "pairs": kept, "skipped": drop}

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(json.dumps({"out": str(out), "total_pairs": len(pairs), "by_domain": stats}, indent=2))
    if pairs:
        lens = [len(p["neg_hard"]) for p in pairs]
        print(f"neg_hard: avg {sum(lens)/len(lens):.2f} max {max(lens)}")


if __name__ == "__main__":
    main()
