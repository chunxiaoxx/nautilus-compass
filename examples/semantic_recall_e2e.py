#!/usr/bin/env python3
"""End-to-end verification: compass cross-agent semantic recall (bge-m3) beats keyword baseline.

WHAT THIS PROVES
----------------
compass serving (compass_http_v09.py) exposes a "memory capsule" across agents under one
user: agent A writes an observation, agent B can recall it cross-agent. After the v0.9.5
upgrade, GET /v1/recall ranks hits by bge-m3 cosine similarity (semantic) and degrades to
a keyword baseline only when the scoring daemon is unreachable.

This script demonstrates the *value* of the semantic upgrade:

    * agent A writes obs with wording  X = "retry with exponential backoff on 429 rate limit errors"
    * agent B queries with wording      Y = "handle too-many-requests throttling"
      (Y is semantically near X but shares ~zero surface tokens with it)
    * a distractor obs with wording     Z = "parse a CSV file into rows" (unrelated)

  Under the bge-m3 ranker (ranker == "bge-m3"):
      A's obs ranks FIRST, with score noticeably above the distractor.

  Under the keyword baseline (ranker == "keyword", daemon stopped):
      `q.lower() in content.lower()` is False for both A and Z because Y shares no
      surface tokens with either -> both collapse to the flat 0.5 keyword score and the
      ranker cannot separate the relevant obs from the distractor. THAT failure to rank
      is exactly the gap the bge-m3 upgrade closes.

HOW TO RUN
----------
    COMPASS_BASE_URL=http://localhost:8770 python examples/semantic_recall_e2e.py

  (BASE_URL defaults to http://localhost:8770; override via COMPASS_BASE_URL.)

PREREQUISITES (why a naive run will fail)
-----------------------------------------
    1. compass serving (compass_http_v09:app) is running and reachable at BASE_URL.
    2. The bge-m3 scoring daemon is up AND speaks the {"action":"score", ...} protocol
       that compass_http_v09._daemon_score() calls. On the server, the serving process
       must have env COMPASS_DAEMON_HOST pointed at the right daemon tunnel port
       (default 127.0.0.1:9876).
    3. The serving build deployed actually does semantic recall (v0.9.5+: the recall route
       calls _daemon_score and returns ranker=="bge-m3"). On an older build recall always
       returns ranker=="keyword" and the semantic assertions below will FAIL loudly --
       which is the correct signal that the upgrade is not deployed yet.

  NOTE: This is a VERIFICATION SCRIPT (one live round-trip with fail-loud assertions),
  NOT a unit/pytest suite. It writes a few rows to whatever DB BASE_URL points at, so
  run it against a staging/dev serving instance -- do NOT point it at production.

  Re-runnable: uses fixed obs_ids (ob_capsule_*) so a second run just hits the duplicate
  guard (409) on the writes, which this script treats as "already present" and proceeds.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# Windows GBK consoles choke on non-ASCII glyphs -> force UTF-8 like the other examples.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

BASE_URL = os.environ.get("COMPASS_BASE_URL", "http://localhost:8770").rstrip("/")

# Fixed, reproducible identities (cleanable by user_id/agent_id). The email is suffixed
# with a coarse run-bucket so re-running after a signup 409 still lands a fresh user when
# desired, while obs_ids stay fixed so duplicate writes are idempotent within a user.
TEST_EMAIL = os.environ.get("COMPASS_TEST_EMAIL", "capsule_e2e@compass.test")
TEST_PASSPHRASE = os.environ.get("COMPASS_TEST_PASSPHRASE", "capsule-e2e-verify-pw")
REGION = os.environ.get("COMPASS_REGION", "cn-shanghai")

AGENT_A = "ag_capsule_a"   # writer  (matches ObservationIn pattern ^ag_[a-zA-Z0-9_]+$)
AGENT_B = "ag_capsule_b"   # reader  (cross-agent recall)

# Wording triplet -- X and Y are semantically near with ~zero surface-token overlap.
WORDING_X = "retry with exponential backoff on 429 rate limit errors"
WORDING_Y = "handle too-many-requests throttling"
WORDING_Z = "parse a CSV file into rows"

OBS_X_ID = "ob_capsule_x_backoff"
OBS_Z_ID = "ob_capsule_z_csv"


# ---------------------------------------------------------------------------
# Tiny stdlib HTTP helper (no requests dependency)
# ---------------------------------------------------------------------------

class HttpError(RuntimeError):
    def __init__(self, status: int, body: str, url: str):
        super().__init__(f"HTTP {status} on {url}: {body[:500]}")
        self.status = status
        self.body = body
        self.url = url


def _request(method: str, path: str, *, token: str | None = None,
             json_body: dict | None = None, query: dict | None = None,
             timeout: float = 30.0) -> dict:
    url = BASE_URL + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = None
    headers = {"Accept": "application/json"}
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")
        except Exception:
            pass
        raise HttpError(e.code, body, url) from None
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"cannot reach compass serving at {url}: {e.reason}. "
            f"Is compass_http_v09:app running and is COMPASS_BASE_URL correct?"
        ) from None


# ---------------------------------------------------------------------------
# Flow steps (mirroring the real compass_http_v09 contract)
# ---------------------------------------------------------------------------

def signup_or_login() -> tuple[str, str]:
    """Return (user_id, jwt). Tries signup; falls back to login on 409 (email taken)."""
    try:
        resp = _request("POST", "/v1/auth/signup", json_body={
            "email": TEST_EMAIL,
            "passphrase": TEST_PASSPHRASE,
            "region": REGION,
        })
        return resp["user_id"], resp["token"]
    except HttpError as e:
        if e.status != 409:
            raise
        # email already registered -> login to recover the same user_id + a fresh JWT
        resp = _request("POST", "/v1/auth/login", json_body={
            "email": TEST_EMAIL,
            "passphrase": TEST_PASSPHRASE,
        })
        return resp["user_id"], resp["token"]


def write_obs(token: str, user_id: str, agent_id: str, obs_id: str, text: str) -> None:
    """POST /v1/observations. content is a dict; serving stores its JSON in content_plain,
    which is what both the bge-m3 daemon and the keyword path score against."""
    body = {
        "obs_id": obs_id,
        "user_id": user_id,           # MUST equal the authed user_id (server enforces 403 otherwise)
        "agent_id": agent_id,
        "agent_type": "capsule_e2e",
        "ts": datetime.now(timezone.utc).isoformat(),
        "meta": {"type": "learning", "concept": "rate_limit", "drift": "green"},
        "content": {"text": text},
    }
    try:
        _request("POST", "/v1/observations", token=token, json_body=body)
        print(f"  wrote {obs_id} (agent={agent_id}): {text!r}")
    except HttpError as e:
        if e.status == 409:
            print(f"  {obs_id} already present (409) -> reusing existing row")
        else:
            raise


def recall(token: str, q: str, *, top_k: int = 5, cross_agent: bool = True) -> dict:
    """GET /v1/recall -> {user_id, query, hits:[{obs_id,agent_id,score,...}], ranker}."""
    return _request("GET", "/v1/recall", token=token, query={
        "q": q,
        "top_k": top_k,
        "cross_agent": "true" if cross_agent else "false",
    })


def _hit_index(hits: list[dict], obs_id: str) -> int:
    for i, h in enumerate(hits):
        if h.get("obs_id") == obs_id:
            return i
    return -1


# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------

class VerifyFailure(AssertionError):
    pass


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise VerifyFailure(msg)


def main() -> int:
    print(f"== compass cross-agent semantic recall E2E ==")
    print(f"BASE_URL = {BASE_URL}")
    print(f"X (writer wording) = {WORDING_X!r}")
    print(f"Y (reader query)   = {WORDING_Y!r}")
    print(f"Z (distractor)     = {WORDING_Z!r}")
    print()

    # 1. auth
    user_id, token = signup_or_login()
    print(f"authed user_id = {user_id}")

    # 2. agent A writes the relevant obs (wording X)
    print("\n-- writes --")
    write_obs(token, user_id, AGENT_A, OBS_X_ID, WORDING_X)
    # ... and an unrelated distractor obs (wording Z), also under agent A
    write_obs(token, user_id, AGENT_A, OBS_Z_ID, WORDING_Z)

    # give async indexing (if any) a beat; recall reads sqlite synchronously so this is
    # just defensive against an indexing pipeline being inserted later.
    time.sleep(0.5)

    # 3. agent B recalls cross-agent with the semantically-near wording Y
    print("\n-- recall (cross_agent=true, q = Y) --")
    res = recall(token, WORDING_Y, top_k=5, cross_agent=True)
    ranker = res.get("ranker")
    hits = res.get("hits", [])
    print(f"ranker = {ranker}")
    for h in hits:
        print(f"  hit obs_id={h.get('obs_id')} agent={h.get('agent_id')} "
              f"score={h.get('score')} content={h.get('content_or_encrypted')}")

    idx_x = _hit_index(hits, OBS_X_ID)
    idx_z = _hit_index(hits, OBS_Z_ID)

    # Cross-agent capsule must work regardless of ranker: B (reader) must be able to see
    # an obs written by A (writer) under the same user.
    require(idx_x != -1,
            f"capsule broken: agent B did not recall A's obs {OBS_X_ID} cross-agent "
            f"(hits={[h.get('obs_id') for h in hits]})")
    print(f"\n[capsule OK] agent B recalled agent A's obs cross-agent (idx={idx_x}).")

    keyword_overlap = WORDING_Y.lower() in WORDING_X.lower()
    print(f"[surface check] '{WORDING_Y}' substring-in '{WORDING_X}' = {keyword_overlap} "
          f"(False => keyword baseline cannot rank this)")

    if ranker == "bge-m3":
        # Semantic path: A's obs must rank FIRST and beat the distractor.
        score_x = float(hits[idx_x]["score"])
        require(idx_x == 0,
                f"semantic ranker did not rank relevant obs first: "
                f"{OBS_X_ID} at idx {idx_x}, hits={[h.get('obs_id') for h in hits]}")
        if idx_z != -1:
            score_z = float(hits[idx_z]["score"])
            require(score_x > score_z,
                    f"semantic ranker failed to separate relevant from distractor: "
                    f"score({OBS_X_ID})={score_x} <= score({OBS_Z_ID})={score_z}")
            print(f"[semantic OK] score(X)={score_x:.4f} > score(Z)={score_z:.4f}; "
                  f"relevant obs ranked first.")
        else:
            print(f"[semantic OK] relevant obs ranked first (score={score_x:.4f}); "
                  f"distractor not in top_k.")

        print("\n=== PASS (ranker=bge-m3) ===")
        print("Semantic recall ranked the semantically-near obs first across agents, "
              "with zero surface-token overlap between query Y and stored wording X.")
        _print_ranker_contrast(observed="bge-m3")
        return 0

    elif ranker == "keyword":
        # Keyword baseline path. This is NOT the upgrade we want to verify; the daemon is
        # down (or the deployed build predates v0.9.5). Show concretely why keyword cannot
        # win here, then FAIL so the verification surfaces the missing semantic deployment.
        scores = {h.get("obs_id"): h.get("score") for h in hits}
        print(f"[keyword baseline] flat scores = {scores}")
        print("Under the keyword ranker, score = 1.0 if q is a substring of content else 0.5.")
        print(f"Query Y shares ~zero surface tokens with X (substring match = {keyword_overlap}),")
        print("so the relevant obs gets the same 0.5 as the distractor -> ranker cannot")
        print("distinguish them. THIS is the gap the bge-m3 upgrade closes.")
        _print_ranker_contrast(observed="keyword")
        raise VerifyFailure(
            "recall returned ranker='keyword' -> bge-m3 semantic recall is NOT active. "
            "Verify the bge-m3 daemon is up (action 'score') and COMPASS_DAEMON_HOST on "
            "the serving process points at it, and that a v0.9.5+ serving build is deployed."
        )

    else:
        raise VerifyFailure(f"unexpected ranker value: {ranker!r} (expected 'bge-m3' or 'keyword')")


def _print_ranker_contrast(observed: str) -> None:
    print("\n--- ranker contrast ---")
    print("  bge-m3   : cosine(query, content) -> can rank semantically-near obs first")
    print("             even when query and content share no surface tokens.")
    print("  keyword  : 1.0 if q substring-of content else 0.5 -> zero-overlap relevant")
    print("             obs gets flat 0.5, indistinguishable from distractors.")
    print(f"  observed : {observed}")


if __name__ == "__main__":
    try:
        rc = main()
    except VerifyFailure as e:
        print(f"\n=== FAIL ===\n{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001 -- fail loud with context
        print(f"\n=== ERROR ===\n{type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
    sys.exit(rc)
