"""齿轮⑤ 记忆并库·第一刀:把飞轮 sqlite learning 沉淀成胶囊并入文件语义库(治 split-brain)。

split-brain 根因(本 session 实测·见 docs/plans/2026-06-22-flywheel-convergence-design.md §4):
  Store A = sqlite observations(飞轮 W1 写 /v1/observations·W2 读 /v1/recall)
  Store B = 文件语义库 ~/.claude/projects/*/memory/*.md(/v1/v14/recall BGE 语义召回)
  两库无桥接 → 飞轮 learning 永远进不了语义大库·conductor/跨 agent 语义召回看不到。

本模块 = 单向桥:飞轮 obs(过晋升门)→ v14_ingest_obs body(写文件语义库为胶囊)。
复用现有机制(anchor#5·不重造):
  - 晋升门 = compass_fleet_memory 的 reward≥PROMOTE 逻辑(错经验不沉淀·防退化 keystone)
  - revoke = tombstone 不沉淀
  - 写入走 v14_ingest_obs body 契约(content/name/description/tags/project)

纯逻辑 + 注入 ingest_fn(live=POST /v1/v14/ingest_obs)→ 可本地 TDD。
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

# 晋升门:与 compass_fleet_memory W1 一致(reward≥此才沉淀·缺 reward=兼容旧=视作已验 1.0)。
PROMOTE_MIN_REWARD: float = 1.0

# 胶囊统一落的 project(语义库里聚一起·与 per-cycle 碎片区隔·便于 conductor/跨 agent 召回)。
CAPSULE_PROJECT: str = "fleet-capsules"


def _reward_of(obs: dict) -> float:
    r = obs.get("reward")
    if r is None:
        return 1.0  # 兼容旧写法(无 reward 字段)= 视作已验证
    try:
        return float(r)
    except (TypeError, ValueError):
        return 0.0


def should_bridge(obs: dict) -> bool:
    """过晋升门才沉淀:reward≥PROMOTE 且非 revoked tombstone。错/低质/撤销经验不入语义库。"""
    if obs.get("revoked"):
        return False
    return _reward_of(obs) >= PROMOTE_MIN_REWARD


def capsule_key(obs: dict) -> str:
    """去重键:obs_id 优先·否则 family+learning 文本哈希位。"""
    oid = str(obs.get("obs_id") or obs.get("id") or "").strip()
    if oid:
        return oid
    fam = str(obs.get("family") or obs.get("task_family") or "")
    txt = str(obs.get("learning") or obs.get("reason") or obs.get("content") or "")
    return f"{fam}::{txt[:80]}"


def obs_to_ingest_body(obs: dict) -> dict:
    """飞轮 obs → v14_ingest_obs body(写文件语义库为胶囊)。

    reward/family/source/verdict 进 tags + description(recall 端可据此过滤/排序)·
    content = learning 正文(BGE 语义召回的主体)。
    """
    family = str(obs.get("family") or obs.get("task_family") or "unknown")
    learning = str(
        obs.get("learning") or obs.get("reason") or obs.get("content") or ""
    ).strip()
    reward = _reward_of(obs)
    source = str(obs.get("source") or obs.get("agent_id") or "fleet")
    verdict = obs.get("verdict")

    tags = [f"family:{family}", f"reward:{reward:g}", f"source:{source}", "fleet-capsule"]
    if verdict:
        tags.append(f"verdict:{str(verdict)[:40]}")

    name = f"capsule:{family}"[:80]
    desc = f"[fleet-capsule family={family} reward={reward:g} src={source}] {learning}"[:200]

    return {
        "content": learning,
        "name": name,
        "description": desc,
        "project": CAPSULE_PROJECT,
        "tags": tags,
        "drift": "green",
    }


def consolidate(
    observations: Iterable[dict],
    ingest_fn: Callable[[dict], Any],
    *,
    seen: set | None = None,
) -> dict:
    """把飞轮 observations 中过门的沉淀成胶囊写进语义库。

    ingest_fn(body) 注入(live=POST /v1/v14/ingest_obs)·单测注 fake。
    seen=已沉淀键(幂等·跨轮去重)·会被原地更新。
    返回 {"written","skipped_gate","skipped_dup","keys"}。
    """
    if seen is None:
        seen = set()
    written = skipped_gate = skipped_dup = 0
    keys: list[str] = []
    for obs in observations:
        if not should_bridge(obs):
            skipped_gate += 1
            continue
        k = capsule_key(obs)
        if k in seen:
            skipped_dup += 1
            continue
        ingest_fn(obs_to_ingest_body(obs))
        seen.add(k)
        keys.append(k)
        written += 1
    return {
        "written": written,
        "skipped_gate": skipped_gate,
        "skipped_dup": skipped_dup,
        "keys": keys,
    }
