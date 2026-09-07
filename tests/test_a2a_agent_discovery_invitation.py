from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AGENT_JSON = ROOT / "landing" / ".well-known" / "agent.json"


def test_a2a_discovery_advertises_invitation_onboarding():
    data = json.loads(AGENT_JSON.read_text(encoding="utf-8"))
    acquisition = data["agent"]["auth"]["acquisition"].lower()
    note = data["agent"]["mcp_alternative"]["note"].lower()

    assert "invitation-only" in acquisition
    assert "issue or pr" in acquisition
    assert "a2a endpoint url" in acquisition
    assert "invitation-only" in note
