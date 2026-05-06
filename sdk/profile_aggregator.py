"""compass v1.0 · client-side profile aggregator · v1.0 §5.

Downloads all user observations · aggregates into profile facts · encrypts ·
uploads encrypted_facts to server. Server cannot read facts · only stores blob.

Usage:
  client = CompassClient(user_id="u_x", agent_id="ag_x", encrypt_payload=True)
  client.set_master_key(master_key)
  from profile_aggregator import compute_and_upload
  compute_and_upload(client, master_key)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PLUGIN_DIR))


def aggregate_facts(observations: list[dict]) -> list[str]:
    """From a list of decrypted observations · derive 5-15 facts about the user.

    Returns a list of natural-language facts:
      "User most often works on type=feature observations (47%)"
      "Top agent type: claude-code (62 obs)"
      "Drift trend: 88% green · 9% yellow · 3% red"
    """
    if not observations:
        return ["No observations yet · profile is empty"]

    facts = []

    # Top types
    types = Counter(o.get("meta", {}).get("type", "?") for o in observations)
    if types:
        top_type, n = types.most_common(1)[0]
        pct = round(100 * n / len(observations))
        facts.append(f"Most frequent observation type: {top_type} ({pct}%)")

    # Top concepts
    concepts = Counter(o.get("meta", {}).get("concept", "?") for o in observations)
    if concepts:
        top_concept, n = concepts.most_common(1)[0]
        pct = round(100 * n / len(observations))
        facts.append(f"Most frequent concept: {top_concept} ({pct}%)")

    # Top agents
    agents = Counter(o.get("agent_type", "?") for o in observations)
    if agents:
        top_agent, n = agents.most_common(1)[0]
        facts.append(f"Top agent type: {top_agent} ({n} observations)")
        if len(agents) >= 2:
            facts.append(f"Cross-agent user · {len(agents)} different agent types used")

    # Drift distribution
    drift = Counter(o.get("meta", {}).get("drift", "?") for o in observations)
    n = sum(drift.values())
    if n:
        green_pct = round(100 * drift.get("green", 0) / n)
        yellow_pct = round(100 * drift.get("yellow", 0) / n)
        red_pct = round(100 * drift.get("red", 0) / n)
        facts.append(f"Drift: green={green_pct}% · yellow={yellow_pct}% · red={red_pct}%")

    # Recency
    if observations:
        latest_ts = max(o.get("ts", "") for o in observations)
        try:
            latest_dt = datetime.fromisoformat(latest_ts.rstrip("Z"))
            facts.append(f"Last observation: {latest_dt.strftime('%Y-%m-%d')}")
        except Exception:
            pass

    # Volume tier
    n = len(observations)
    if n < 10:
        facts.append(f"Light user · {n} observations")
    elif n < 100:
        facts.append(f"Regular user · {n} observations")
    elif n < 1000:
        facts.append(f"Heavy user · {n} observations")
    else:
        facts.append(f"Power user · {n}+ observations")

    return facts


def compute_and_upload(client, master_key: bytes, max_obs: int = 1000):
    """Full client-side profile pipeline:
      1. GET /v1/observations · pull recent obs
      2. Decrypt encrypted_body using master_key (skip if plaintext)
      3. aggregate_facts(decrypted) → list of strings
      4. encrypt facts using master_key + obs_id="profile_facts"
      5. POST /v1/profile/derive with encrypted_facts blob
    """
    sys.path.insert(0, str(PLUGIN_DIR))
    from compass_crypto import encrypt_obs

    # Step 1: pull observations (server will return encrypted_body for Pro+)
    res = client._get("/v1/observations", {"limit": max_obs})
    raw = res.get("observations", []) if isinstance(res, dict) else []

    # Step 2: decrypt as needed
    decrypted = []
    for o in raw:
        if o.get("encrypted_body"):
            try:
                from compass_crypto import decrypt_obs
                content = decrypt_obs(master_key, o["obs_id"], o["encrypted_body"])
                decrypted.append({**o, "content": content})
            except Exception as e:
                sys.stderr.write(f"[profile] decrypt fail for {o.get('obs_id')}: {e}\n")
        else:
            decrypted.append(o)

    # Step 3: aggregate
    facts = aggregate_facts(decrypted)

    # Step 4: encrypt facts list
    facts_blob = encrypt_obs(
        master_key,
        "profile_facts",
        {"facts": facts, "n": len(decrypted)},
    )

    # Step 5: upload
    payload = {
        "encrypted_facts": facts_blob,
        "encryption_version": "v1",
        "derived_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_obs_count": len(decrypted),
    }
    return client._post("/v1/profile/derive", payload)


def selftest():
    """Standalone test · doesn't need a real client."""
    sample_obs = [
        {"agent_type": "claude-code", "meta": {"type": "feature", "drift": "green", "concept": "pattern"}, "ts": "2026-05-05T10:00:00Z"},
        {"agent_type": "claude-code", "meta": {"type": "bugfix", "drift": "yellow", "concept": "gotcha"}, "ts": "2026-05-04T10:00:00Z"},
        {"agent_type": "openclaw", "meta": {"type": "decision", "drift": "green", "concept": "trade-off"}, "ts": "2026-05-03T10:00:00Z"},
        {"agent_type": "cursor", "meta": {"type": "feature", "drift": "green", "concept": "how-it-works"}, "ts": "2026-05-02T10:00:00Z"},
        {"agent_type": "claude-code", "meta": {"type": "feature", "drift": "red", "concept": "gotcha"}, "ts": "2026-05-01T10:00:00Z"},
    ]
    facts = aggregate_facts(sample_obs)
    print("=== aggregate_facts selftest ===")
    for f in facts:
        print(f"  · {f}")
    assert any("feature" in f for f in facts)
    assert any("claude-code" in f for f in facts)
    assert any("Cross-agent" in f for f in facts)
    print("\n[PASS] aggregate_facts works · 5 sample obs → cross-agent profile")


if __name__ == "__main__":
    selftest()
