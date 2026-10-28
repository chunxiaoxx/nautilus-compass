#!/usr/bin/env python3
"""
V7 LLM Judge Daemon · 短板 6.a 修复

每天 9:00 cron 触发:
  - 取昨天 24h helix_blocks (block_type='left') 随机 50 个
  - Anthropic Sonnet 4.6 评 quality_score (0-10) + reasoning + improvement_hint
  - 写入 platform_judge_scores 表
  - 高频 hint -> strategy_store JSON · 注入未来 selector prompt

降级: 没 ANTHROPIC_API_KEY -> MiniMax M2.7 (弱判但有信号)
"""
import json
import os
import os as _os
for _l in open("/etc/nautilus/secrets.env"):
    _k, _, _v = _l.strip().partition("=")
    if _k: _os.environ.setdefault(_k, _v)

import random
import re
import sys
import time
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import psycopg2.extras

# ---- env ----
ENV_PATH = "/home/ubuntu/nautilus-mvp/phase3/backend/.env"
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://nautilus_user@localhost:5432/nautilus_production",
)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "").strip()

SAMPLE_N = int(os.environ.get("V7_JUDGE_SAMPLE", "50"))
STRATEGY_STORE_DIR = Path(
    "/home/ubuntu/nautilus-v5/nautilus_v5/runtime/strategy_store"
)
STRATEGY_STORE_DIR.mkdir(parents=True, exist_ok=True)

# ---- judge prompt ----
JUDGE_SYSTEM = """You are an objective quality judge for AI agent decisions in the Nautilus platform.

For each agent decision (helix block · 'left' phase = think/plan/feel),
respond with ONE JSON object only — no <think> tags, no markdown, no prose, no code fences:
{"quality_score": <float 0-10>, "reasoning": "<1-2 sentence why>", "improvement_hint": "<short actionable hint ≤15 words>"}

10=excellent strategic move · 5=mediocre/repetitive · 0=clearly bad/wasteful."""


_JSON_RE = re.compile(r"\{[^{}]*\"quality_score\"[\s\S]*?\}", re.MULTILINE)


def extract_json(raw: str) -> dict:
    """Robustly pull the first JSON object out of an LLM response.

    Handles: ```json fences, <think>...</think> wrappers, plain prose around JSON.
    """
    if not raw:
        raise ValueError("empty response")
    # strip <think>...</think>
    raw = re.sub(r"<think>[\s\S]*?</think>", "", raw, flags=re.IGNORECASE).strip()
    # strip code fences
    if "```" in raw:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if m:
            raw = m.group(1).strip()
    # try direct
    raw = raw.strip()
    if raw.startswith("{"):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    # find first {...} block containing quality_score
    m = _JSON_RE.search(raw)
    if m:
        return json.loads(m.group(0))
    # last resort: any {...}
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        return json.loads(m.group(0))
    raise ValueError(f"no JSON found in response: {raw[:200]!r}")


def judge_anthropic(client, payload_text: str) -> dict:
    """Call Anthropic Sonnet 4.6 for one judgment."""
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": payload_text}],
    )
    return extract_json(msg.content[0].text)


def judge_minimax(payload_text: str) -> dict:
    """Fallback: MiniMax M2.7 (weak signal · TODO replace with real Anthropic)."""
    import urllib.request

    base = os.environ.get("OPENAI_BASE_URL", "https://api.minimaxi.com/v1").rstrip("/")
    url = f"{base}/chat/completions"
    body = json.dumps(
        {
            "model": os.environ.get("OPENAI_MODEL", "MiniMax-M2.7-highspeed"),
            "messages": [
                {"role": "system", "content": JUDGE_SYSTEM},
                {"role": "user", "content": payload_text},
            ],
            "temperature": 0.3,
            "max_tokens": 800,
        }
    ).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        out = json.loads(resp.read())
    return extract_json(out["choices"][0]["message"]["content"])


def ensure_table(conn):
    """Create platform_judge_scores if absent."""
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS platform_judge_scores (
                id           BIGSERIAL PRIMARY KEY,
                helix_id     BIGINT NOT NULL,
                agent_id     TEXT NOT NULL,
                cycle_n      INTEGER,
                score        REAL NOT NULL,
                reasoning    TEXT,
                hint         TEXT,
                judge_model  TEXT NOT NULL,
                created_at   TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (helix_id, judge_model)
            );
            CREATE INDEX IF NOT EXISTS idx_pjs_agent_created
                ON platform_judge_scores (agent_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_pjs_score
                ON platform_judge_scores (score);
            """
        )
    conn.commit()


def fetch_sample(conn, n: int):
    """Random sample of last 24h left blocks · prefer self_modify or rich-think."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, agent_id, cycle_n, payload, ts
            FROM helix_blocks
            WHERE block_type = 'left'
              AND ts >= NOW() - INTERVAL '24 hours'
              AND payload->>'think' IS NOT NULL
              AND id NOT IN (
                  SELECT helix_id FROM platform_judge_scores
                  WHERE created_at >= NOW() - INTERVAL '24 hours'
              )
            ORDER BY
              CASE WHEN payload->>'self_modify' = 'true' THEN 0 ELSE 1 END,
              random()
            LIMIT %s;
            """,
            (n,),
        )
        return cur.fetchall()


def block_to_judge_input(row) -> str:
    p = row["payload"] or {}
    return json.dumps(
        {
            "agent_id": row["agent_id"],
            "cycle_n": row["cycle_n"],
            "feel": (p.get("feel") or "")[:600],
            "think": (p.get("think") or "")[:1200],
            "tension": p.get("tension"),
            "act_count": p.get("act_count"),
            "act_summary": (p.get("act_summary") or [])[:6],
            "self_modify": p.get("self_modify", False),
        },
        ensure_ascii=False,
    )


def write_strategy_store(hints: list, model_name: str):
    """High-frequency hints -> strategy_store JSON for selector prompt injection."""
    counter = Counter([h.strip().lower() for h in hints if h])
    top = [
        {"hint": h, "freq": c}
        for h, c in counter.most_common(10)
        if c >= 2  # only keep hints that appeared >=2 times
    ]
    if not top:
        return None
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "judge_model": model_name,
        "sample_size": len(hints),
        "top_hints": top,
        "selector_prompt_inject": (
            "Recent platform-wide judgment hints (apply when relevant):\n"
            + "\n".join(f"- {h['hint']} (×{h['freq']})" for h in top)
        ),
    }
    path = STRATEGY_STORE_DIR / "judge_hints.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    return path


def main():
    print(f"[v7-judge] start {datetime.now(timezone.utc).isoformat()}")
    conn = psycopg2.connect(DATABASE_URL)
    try:
        ensure_table(conn)
        rows = fetch_sample(conn, SAMPLE_N)
        print(f"[v7-judge] sampled {len(rows)} blocks (target {SAMPLE_N})")
        if not rows:
            print("[v7-judge] no eligible rows · exit 0")
            return 0

        use_anthropic = bool(ANTHROPIC_API_KEY) and ANTHROPIC_API_KEY.startswith(
            "sk-ant-"
        )
        client = None
        if use_anthropic:
            try:
                import anthropic

                client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                # probe once to detect dead credit / proxy
                client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "ok"}],
                )
                model_name = "claude-sonnet-4-5"
                print(f"[v7-judge] judge LLM = Anthropic {model_name}")
            except Exception as e:
                print(
                    f"[v7-judge] anthropic probe failed: {type(e).__name__}: "
                    f"{str(e)[:160]} · fallback MiniMax"
                )
                use_anthropic = False
                client = None
        if not use_anthropic:
            model_name = "minimax-m2.7-highspeed"
            print(
                f"[v7-judge] judge LLM = MiniMax {model_name} "
                "(TODO: top up Anthropic credit for real Sonnet judge)"
            )

        ok = 0
        fail = 0
        scores = []
        hints = []
        with conn.cursor() as cur:
            for row in rows:
                inp = block_to_judge_input(row)
                try:
                    if use_anthropic:
                        verdict = judge_anthropic(client, inp)
                    else:
                        verdict = judge_minimax(inp)
                    score = float(verdict.get("quality_score", 0))
                    score = max(0.0, min(10.0, score))
                    reasoning = str(verdict.get("reasoning", ""))[:1000]
                    hint = str(verdict.get("improvement_hint", ""))[:300]
                    cur.execute(
                        """
                        INSERT INTO platform_judge_scores
                          (helix_id, agent_id, cycle_n, score, reasoning, hint, judge_model)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (helix_id, judge_model) DO NOTHING;
                        """,
                        (
                            row["id"],
                            row["agent_id"],
                            row["cycle_n"],
                            score,
                            reasoning,
                            hint,
                            model_name,
                        ),
                    )
                    ok += 1
                    scores.append(score)
                    hints.append(hint)
                    if ok % 5 == 0:
                        conn.commit()
                        print(
                            f"[v7-judge] progress {ok}/{len(rows)} · "
                            f"last score={score:.1f} reason={reasoning[:60]!r}"
                        )
                    time.sleep(0.4)  # gentle rate limit
                except Exception as e:
                    fail += 1
                    print(f"[v7-judge] block id={row['id']} fail: {e}")
                    if fail >= 5 and ok == 0:
                        # fail-fast only when nothing has worked yet
                        raise
        conn.commit()

        if scores:
            print(
                f"[v7-judge] DONE ok={ok} fail={fail} "
                f"score min={min(scores):.1f} max={max(scores):.1f} "
                f"avg={sum(scores)/len(scores):.2f}"
            )
        path = write_strategy_store(hints, model_name)
        if path:
            print(f"[v7-judge] strategy_store wrote {path}")
        else:
            print("[v7-judge] strategy_store skipped (no hint freq>=2)")
        return 0
    finally:
        conn.close()


# --- W2 Gate 2 · marketing mode ---------------------------------
MARKETING_JUDGE_SYSTEM_BASE = """You are a quality judge for Nautilus platform marketing drafts.

You score on 4 dimensions (each 0-10) for the draft sent to a specific channel.

ANCHORS:
- good (avg 8-10): "V5 platform cycle 28065 · 326 real agents · 533 bounties live · NAU 1884 actual on Base · A2A protocol open-source." (factual + verifiable + channel-fit)
- mediocre (avg 5-7): "V5 is a powerful AI platform helping agents collaborate." (vague but not wrong)
- bad (avg 0-4): "Revolutionary AI breakthrough! 100x productivity gains! Buy NAU now!" (overhyped + generic + spammy)

DIMENSIONS:
- technical_truth (0-10): factual claims verifiable against platform state? specific cycle/agent/USDC numbers preferred over vague claims
- not_overhyped (0-10): avoids "revolutionary/breakthrough/100x/game-changer/disrupt"; honest about scope
- aligns_platform_goals (0-10): supports W3 goals (real customers, real USDC, HR/VC verticals, A2A protocol adoption); not pure hype
- channel_fit (0-10): tone+length+format right for the channel. X=concise+link, dev.to=technical+code, Reddit=discussion+humble, LinkedIn=professional+case-study

Respond with ONE JSON object only — no <think> tags, no markdown, no code fences:
{"technical_truth": <0-10>, "not_overhyped": <0-10>, "aligns_platform_goals": <0-10>, "channel_fit": <0-10>, "feedback": "<2-3 sentence actionable feedback>"}
"""

# BP4 · GitHub-specific anchors · activated when channel LIKE 'github_%'
GITHUB_QUALITY_ANCHORS = """

GITHUB_QUALITY_ANCHORS (activate because channel starts with 'github_'):
- good (avg 8-10): issue contains real error stacktrace + reproduction steps + what was tried + expected behavior (true technical content). Or release notes with diff highlights + breaking changes + migration path. Or discussion with a concrete question + context + minimal repro.
- mediocre (avg 5-7): title is short but body is long, gives concrete repro steps but no stacktrace; or release notes that just list commits without categorization.
- bad (avg 0-4): comment is generic encouragement like "great work · keep it up" or "+1" or "looking forward to it" with no information; spam-like cross-posting; "please add feature X" without rationale.

GITHUB-SPECIFIC channel_fit guidance:
- github_issue: needs title <80c + body with stacktrace/repro/expected; labels appropriate
- github_pr: needs description of WHY (not just WHAT) + test plan + linked issue
- github_release: needs version + summary of changes + breaking changes flagged
- github_discussion: needs concrete question + context + relevant code/links
- github_comment: must add information; reject pure encouragement
- github_star: only for repos where we have real interaction (not drive-by)
"""

# BP6 · domain anchor pack lookup from platform_anchor_packs · superseded hard-code
_ANCHOR_PACK_CACHE: dict = {}
_ANCHOR_PACK_CACHE_TS: float = 0.0


def _load_anchor_packs_from_db():
    """Pull active anchor packs · 5min TTL cache · soft-fails to legacy hard-code."""
    import time as _t
    global _ANCHOR_PACK_CACHE, _ANCHOR_PACK_CACHE_TS
    now = _t.time()
    if _ANCHOR_PACK_CACHE and (now - _ANCHOR_PACK_CACHE_TS) < 300:
        return _ANCHOR_PACK_CACHE
    try:
        conn = psycopg2.connect(DATABASE_URL)
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT name, content, channels_applicable "
                    "FROM platform_anchor_packs WHERE status='active'"
                )
                rows = cur.fetchall()
        finally:
            conn.close()
        _ANCHOR_PACK_CACHE = {r['name']: dict(r) for r in rows}
        _ANCHOR_PACK_CACHE_TS = now
    except Exception as e:
        print(f'[bp6] anchor pack DB lookup fail · {e} · falling back to hard-code')
    return _ANCHOR_PACK_CACHE


def _format_pack_as_anchor_text(pack: dict) -> str:
    """Render a platform_anchor_packs row's content JSONB as system-prompt text."""
    try:
        c = pack.get('content') or {}
        if isinstance(c, str):
            c = json.loads(c)
        name = pack.get('name', 'unknown')
        anchors = c.get('anchors') or {}
        cf = c.get('channel_fit_guidance') or {}
        out = [f'\n\n{name.upper()}_ANCHORS (from platform_anchor_packs):']
        if anchors.get('good'):
            out.append(f'- good (avg 8-10): {anchors["good"]}')
        if anchors.get('mediocre'):
            out.append(f'- mediocre (avg 5-7): {anchors["mediocre"]}')
        if anchors.get('bad'):
            out.append(f'- bad (avg 0-4): {anchors["bad"]}')
        if cf:
            out.append('\nCHANNEL_FIT guidance:')
            for ch_key, txt in cf.items():
                out.append(f'- {ch_key}: {txt}')
        return '\n'.join(out)
    except Exception as e:
        print(f'[bp6] format pack fail · {e}')
        return ''


def _build_marketing_system(channel: str) -> str:
    """BP6 · build judge prompt by looking up applicable anchor packs from DB.

    Logic:
      - always start with MARKETING_JUDGE_SYSTEM_BASE
      - find any active pack whose channels_applicable contains channel or '*'
        → append its anchor text to the prompt (skip 'general' since it's BASE,
        skip 'stub' status packs)
      - falls back to hard-coded GITHUB_QUALITY_ANCHORS for github_* if no DB match
    """
    ch = (channel or '').lower()
    packs = _load_anchor_packs_from_db()
    if not packs:
        if ch.startswith('github_'):
            return MARKETING_JUDGE_SYSTEM_BASE + GITHUB_QUALITY_ANCHORS
        return MARKETING_JUDGE_SYSTEM_BASE
    prompt = MARKETING_JUDGE_SYSTEM_BASE
    seen_packs = set()
    for pname, pack in packs.items():
        if pname == 'general':
            continue
        applicable = pack.get('channels_applicable') or []
        if ch in applicable or '*' in applicable:
            content = pack.get('content') or {}
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except Exception:
                    content = {}
            if content.get('status') == 'stub':
                continue
            txt = _format_pack_as_anchor_text(pack)
            if txt and pname not in seen_packs:
                prompt += txt
                seen_packs.add(pname)
    if ch.startswith('github_') and 'github_quality' not in seen_packs:
        prompt += GITHUB_QUALITY_ANCHORS
    return prompt

# back-compat alias for any external import
MARKETING_JUDGE_SYSTEM = MARKETING_JUDGE_SYSTEM_BASE


def fetch_marketing_drafts(conn, n: int, review_id: int = None):
    """Fetch pending marketing drafts. If review_id given, fetch only that row
    (regardless of score state · idempotent: ON CONFLICT in UPDATE handles dup)."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if review_id is not None:
            cur.execute(
                """
                SELECT id, post_id, draft_text, channel, writer_agent, reviewer_agent
                FROM platform_marketing_review
                WHERE id = %s
                  AND score IS NULL
                """,
                (review_id,),
            )
        else:
            cur.execute(
                """
                SELECT id, post_id, draft_text, channel, writer_agent, reviewer_agent
                FROM platform_marketing_review
                WHERE score IS NULL
                  AND created_at >= NOW() - INTERVAL '7 days'
                ORDER BY created_at ASC
                LIMIT %s;
                """,
                (n,),
            )
        return cur.fetchall()


def _extract_marketing_json(raw: str) -> dict:
    raw = re.sub(r"<think>[\s\S]*?</think>", "", raw, flags=re.IGNORECASE).strip()
    if "```" in raw:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if m:
            raw = m.group(1).strip()
    if raw.startswith("{"):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        return json.loads(m.group(0))
    raise ValueError(f"no JSON: {raw[:200]!r}")


def judge_marketing_anthropic(client, payload_text: str, channel: str = "") -> dict:
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=600,
        system=_build_marketing_system(channel),
        messages=[{"role": "user", "content": payload_text}],
    )
    return _extract_marketing_json(msg.content[0].text)


def judge_marketing_minimax(payload_text: str, channel: str = "") -> dict:
    import urllib.request
    base = os.environ.get("OPENAI_BASE_URL", "https://api.minimaxi.com/v1").rstrip("/")
    body = json.dumps({
        "model": os.environ.get("OPENAI_MODEL", "MiniMax-M2.7-highspeed"),
        "messages": [
            {"role": "system", "content": _build_marketing_system(channel)},
            {"role": "user", "content": payload_text},
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }).encode()
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {MINIMAX_API_KEY}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        out = json.loads(resp.read())
    return _extract_marketing_json(out["choices"][0]["message"]["content"])


def notify_writer_a2a(conn, writer_agent: str, review_id: int,
                      score: float, feedback: str):
    """Stub: insert a2a message to writer_agent for retry."""
    try:
        import uuid
        msg_id = f"mkt-rej-{review_id}-{uuid.uuid4().hex[:8]}"
        content = (f"[marketing reject · review_id={review_id} · "
                   f"score={score:.2f}] {feedback[:400]}")
        meta = {
            "review_id": review_id, "score": round(score, 2),
            "action": "revise_and_resubmit",
        }
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO platform_agent_messages
                  (message_id, from_agent, to_agent, content, msg_type,
                   metadata, sent_at)
                VALUES (%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT (message_id) DO NOTHING
                """,
                (msg_id, "v7-llm-judge-marketing",
                 writer_agent, content,
                 "marketing_review_reject",
                 json.dumps(meta)),
            )
        conn.commit()
    except Exception as e:
        print(f"[v7-judge-mkt] notify_writer_a2a fail: {e}")


def main_marketing(review_id: int = None):
    """Marketing judge main · if review_id given, score that single row only.

    Returns 0 on success (≥1 row scored), 2 if requested review_id missing/already scored.
    """
    print(f"[v7-judge-mkt] start {datetime.now(timezone.utc).isoformat()} "
          f"review_id={review_id}")
    conn = psycopg2.connect(DATABASE_URL)
    try:
        rows = fetch_marketing_drafts(conn, 20, review_id=review_id)
        print(f"[v7-judge-mkt] sampled {len(rows)} pending drafts "
              f"(targeted review_id={review_id})")
        if not rows:
            print("[v7-judge-mkt] no pending · exit 0")
            # exit 2 lets V5 caller distinguish "row already scored or vanished"
            # from a real success-with-no-work
            return 2 if review_id is not None else 0

        use_anthropic = bool(ANTHROPIC_API_KEY) and ANTHROPIC_API_KEY.startswith("sk-ant-")
        client = None
        model_name = "minimax-m2.7-highspeed"
        if use_anthropic:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                client.messages.create(model="claude-sonnet-4-5", max_tokens=10,
                                       messages=[{"role": "user", "content": "ok"}])
                model_name = "claude-sonnet-4-5"
            except Exception as e:
                print(f"[v7-judge-mkt] anthropic probe fail: "
                      f"{type(e).__name__}: {str(e)[:160]} · fallback minimax")
                use_anthropic = False
        print(f"[v7-judge-mkt] judge LLM = {model_name}")

        ok = fail = 0
        with conn.cursor() as cur:
            for row in rows:
                payload = json.dumps({
                    "channel": row["channel"],
                    "draft": (row["draft_text"] or "")[:3000],
                    "writer_agent": row["writer_agent"],
                }, ensure_ascii=False)
                try:
                    verdict = (judge_marketing_anthropic(client, payload, row["channel"])
                               if use_anthropic
                               else judge_marketing_minimax(payload, row["channel"]))
                    tt = max(0.0, min(10.0, float(verdict.get("technical_truth", 0))))
                    no = max(0.0, min(10.0, float(verdict.get("not_overhyped", 0))))
                    al = max(0.0, min(10.0, float(verdict.get("aligns_platform_goals", 0))))
                    cf = max(0.0, min(10.0, float(verdict.get("channel_fit", 0))))
                    avg = (tt + no + al + cf) / 4.0
                    feedback = str(verdict.get("feedback", ""))[:1000]
                    approved = avg >= 7.0
                    cur.execute(
                        """
                        UPDATE platform_marketing_review
                        SET score=%s, technical_truth=%s, not_overhyped=%s,
                            aligns_platform_goals=%s, channel_fit=%s,
                            feedback=%s, approved=%s,
                            judge_model=%s, reviewed_at=NOW()
                        WHERE id=%s
                        """,
                        (avg, tt, no, al, cf, feedback, approved,
                         model_name, row["id"]),
                    )
                    conn.commit()
                    ok += 1
                    print(f"[v7-judge-mkt] id={row['id']} ch={row['channel']} "
                          f"avg={avg:.1f} tt={tt:.1f} no={no:.1f} al={al:.1f} "
                          f"cf={cf:.1f} approved={approved}")
                    if not approved:
                        notify_writer_a2a(conn, row["writer_agent"],
                                          row["id"], avg, feedback)
                    time.sleep(0.4)
                except Exception as e:
                    fail += 1
                    print(f"[v7-judge-mkt] id={row['id']} fail: {e}")
                    if fail >= 5 and ok == 0:
                        raise
        conn.commit()
        print(f"[v7-judge-mkt] DONE ok={ok} fail={fail}")
        # rc=1 if specifically-requested review_id failed (silent-fail fix)
        return 1 if (review_id is not None and ok == 0) else 0
    finally:
        conn.close()
# --- /W2 Gate 2 ---------------------------------------------------


if __name__ == "__main__":
    try:
        mode = "helix"
        review_id = None
        # support both --review_id=X and --review_id X
        i = 1
        argv = sys.argv[1:]
        while i <= len(argv):
            a = argv[i-1]
            if a.startswith("--mode="):
                mode = a.split("=", 1)[1].strip()
            elif a == "--mode" and i < len(argv):
                mode = argv[i].strip()
                i += 1
            elif a.startswith("--review_id="):
                try:
                    review_id = int(a.split("=", 1)[1].strip())
                except ValueError:
                    print(f"[v7-judge] invalid --review_id value: {a}")
                    sys.exit(1)
            elif a == "--review_id" and i < len(argv):
                try:
                    review_id = int(argv[i].strip())
                except ValueError:
                    print(f"[v7-judge] invalid --review_id value: {argv[i]}")
                    sys.exit(1)
                i += 1
            i += 1
        if mode == "marketing":
            sys.exit(main_marketing(review_id=review_id))
        else:
            if review_id is not None:
                print("[v7-judge] --review_id only supported with --mode=marketing")
                sys.exit(1)
            sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
