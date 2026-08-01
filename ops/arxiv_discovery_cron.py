"""arxiv discovery · 每 6h 真扫 new papers in agent memory / drift / safety · INSERT outreach-discovery bounty into raid.

Cron (cloud):
  0 */6 * * * /home/ubuntu/nautilus-compass/ops/arxiv_discovery_cron.sh \
              >> /home/ubuntu/.cache/compass/arxiv-discovery.log 2>&1

Flow:
  1. arxiv API query 8 keywords (cs.CL / cs.AI · past 7d)
  2. dedupe via state file (~/.cache/compass/arxiv-discovery-state.json)
  3. INSERT bounty into platform_bounties:
     - task_type='outreach-discovery'
     - source='compass-outreach-arxiv-discovery'
     - assigned_to='hr-agent-web'  (web-research capability)
     - asset_path='inline-text' (payload in description)
     - channel='arxiv'
  4. raid: kairos picks up → score relevance → if pass, nautilus-prime-001 generates personalized outreach
  5. anchors_outreach_quality drift gate applied at publish time

No human review.
"""
from __future__ import annotations
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    import psycopg
except ImportError:
    sys.stderr.write("psycopg not installed · pip install psycopg\n")
    sys.exit(1)


DSN = os.environ.get("NAUTILUS_DSN", "").strip()
STATE_FILE = Path(os.environ.get(
    "ARXIV_DISCOVERY_STATE",
    str(Path.home() / ".cache" / "compass" / "arxiv-discovery-state.json"),
))
ARXIV_API = "http://export.arxiv.org/api/query"

# 8 keywords · compass 相邻领域
KEYWORDS = [
    "agent memory layer",
    "LLM persona drift detection",
    "LLM safety monitor",
    "multi-turn jailbreak",
    "agent behavioral monitoring",
    "RAG memory benchmark",
    "LLM agent self-correction",
    "behavioral anchor detection",
]
LOOKBACK_DAYS = int(os.environ.get("ARXIV_DISCOVERY_LOOKBACK_DAYS", "7"))
MAX_PER_KEYWORD = int(os.environ.get("ARXIV_DISCOVERY_MAX_PER_KW", "5"))
MAX_BOUNTIES_PER_RUN = int(os.environ.get("ARXIV_DISCOVERY_MAX_BOUNTIES", "8"))


def _require_dsn(value: str, variable_name: str) -> str:
    if not value:
        raise RuntimeError(f"{variable_name} is required")
    return value


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {"seen_arxiv_ids": [], "dispatched_count": 0, "last_run_ts": 0}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"seen_arxiv_ids": [], "dispatched_count": 0, "last_run_ts": 0}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["seen_arxiv_ids"] = state.get("seen_arxiv_ids", [])[-2000:]
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _query_arxiv(keyword: str, max_results: int = 5) -> list[dict]:
    """Return list of {arxiv_id, title, authors, summary, published, pdf_url}."""
    q = urllib.parse.quote_plus(f'all:"{keyword}"')
    url = (
        f"{ARXIV_API}?search_query={q}"
        f"&start=0&max_results={max_results}"
        f"&sortBy=submittedDate&sortOrder=descending"
    )
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            xml = resp.read().decode("utf-8")
    except Exception as e:
        sys.stderr.write(f"arxiv query fail {keyword!r}: {e!r}\n")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml)
    out = []
    for entry in root.findall("atom:entry", ns):
        eid = entry.findtext("atom:id", default="", namespaces=ns)
        arxiv_id = eid.rsplit("/", 1)[-1].replace("v", "_v")
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
        published = entry.findtext("atom:published", default="", namespaces=ns) or ""
        authors = []
        for a in entry.findall("atom:author/atom:name", ns):
            if a.text:
                authors.append(a.text.strip())
        pdf_url = ""
        for link in entry.findall("atom:link", ns):
            if link.get("type") == "application/pdf":
                pdf_url = link.get("href", "")
                break
        out.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "summary": summary[:1500],
            "published": published,
            "pdf_url": pdf_url,
            "abs_url": eid,
            "keyword": keyword,
        })
    return out


def _is_recent(paper: dict, days: int) -> bool:
    try:
        pub = datetime.fromisoformat(paper["published"].replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - pub) <= timedelta(days=days)
    except Exception:
        return False


def _insert_bounty(conn, paper: dict) -> str | None:
    """INSERT outreach-discovery bounty. Returns bounty_id."""
    title = f"Outreach candidate: {paper['title'][:140]}"
    authors_str = ", ".join(paper["authors"][:5])
    description = (
        f"arxiv paper · keyword='{paper['keyword']}'\n"
        f"title: {paper['title']}\n"
        f"authors: {authors_str}\n"
        f"published: {paper['published']}\n"
        f"abs: {paper['abs_url']}\n"
        f"pdf: {paper['pdf_url']}\n\n"
        f"task: hr-agent-web · web-research the lead author + judge if a personalized outreach "
        f"makes sense (relevance to compass / persona-drift / agent-memory work). "
        f"If yes, hand off to nautilus-prime-001 with proposed angle.\n\n"
        f"abstract excerpt:\n{paper['summary'][:800]}"
    )
    metadata = {
        "arxiv_id": paper["arxiv_id"],
        "abs_url": paper["abs_url"],
        "pdf_url": paper["pdf_url"],
        "authors": paper["authors"],
        "keyword": paper["keyword"],
        "discovery_ts": datetime.now(timezone.utc).isoformat(),
    }
    bounty_id = "outreach-arxiv-" + paper["arxiv_id"][:32].replace(".", "-")
    try:
        conn.execute(
            """
            INSERT INTO platform_bounties (
                bounty_id, title, description, reward_nau,
                task_type, status, posted_by,
                channel, source, asset_path, assigned_to,
                metadata, posted_at
            ) VALUES (
                %s, %s, %s, 30,
                'outreach-discovery', 'open', 'compass-discovery-cron',
                'arxiv', 'compass-outreach-arxiv-discovery', 'inline-text', 'hr-agent-web',
                %s, NOW()
            )
            ON CONFLICT (bounty_id) DO NOTHING
            """,
            (bounty_id, title, description, json.dumps(metadata)),
        )
        return bounty_id
    except Exception as e:
        sys.stderr.write(f"INSERT fail for {paper['arxiv_id']}: {e!r}\n")
        return None


def main() -> int:
    state = _load_state()
    seen = set(state.get("seen_arxiv_ids", []))
    dispatched = 0
    skipped_seen = 0
    skipped_old = 0
    errors = 0

    try:
        conn = psycopg.connect(
            _require_dsn(DSN, "NAUTILUS_DSN"),
            autocommit=True,
        )
    except Exception as e:
        sys.stderr.write(f"PG connect fail: {type(e).__name__}\n")
        return 1

    try:
        for kw in KEYWORDS:
            if dispatched >= MAX_BOUNTIES_PER_RUN:
                break
            papers = _query_arxiv(kw, MAX_PER_KEYWORD)
            for paper in papers:
                if dispatched >= MAX_BOUNTIES_PER_RUN:
                    break
                if paper["arxiv_id"] in seen:
                    skipped_seen += 1
                    continue
                if not _is_recent(paper, LOOKBACK_DAYS):
                    skipped_old += 1
                    seen.add(paper["arxiv_id"])  # mark seen to skip next time
                    continue
                bounty_id = _insert_bounty(conn, paper)
                if bounty_id:
                    seen.add(paper["arxiv_id"])
                    dispatched += 1
                    print(f"dispatched · {bounty_id} · '{paper['title'][:80]}'")
                else:
                    errors += 1
            time.sleep(3)  # arxiv API politeness · 6h cron interval should not hit rate limit
    finally:
        conn.close()

    state["seen_arxiv_ids"] = sorted(seen)
    state["dispatched_count"] = int(state.get("dispatched_count", 0)) + dispatched
    state["last_run_ts"] = int(time.time())
    _save_state(state)

    print(
        f"{datetime.now().isoformat(timespec='seconds')} · "
        f"dispatched={dispatched} skipped_seen={skipped_seen} "
        f"skipped_old={skipped_old} errors={errors} "
        f"total_dispatched={state['dispatched_count']}"
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
