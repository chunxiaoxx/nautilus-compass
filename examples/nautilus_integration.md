# Nautilus Platform Integration Guide

How agents on the **Nautilus open agent platform** (Kairos · V5 · SuperAgent · or any custom runtime) call **Nautilus Compass** for drift telemetry and memory recall.

The gateway is a stateless FastAPI service in front of a single shared BGE-m3 daemon. Agents send HTTP/JSON. No SDK needed in the agent — just `requests` (Python), `net/http` (Go), `reqwest` (Rust), `fetch` (Node).

---

## Architecture in one picture

```
[ Nautilus Platform ]
   │
   │   POST /v1/drift_check       (per-turn · ~200 ms)
   │   POST /v1/recall              (per-turn · ~200 ms)
   │   POST /v1/feedback_log        (after user reaction)
   ▼
[ compass-gateway:8765 ]  ─ N replicas (stateless · HPA on QPS)
   │
   ▼
[ compass-daemon:9876 ]   ─ 1 pod (stateful · BGE-m3 in RAM · 2.3 GB)
```

Tenant isolation is via the `X-Tenant-ID` header. Feedback is logged per-tenant (`feedback_<tenant>.jsonl`); future iterations route per-tenant `anchors_<tenant>.json` to switch drift profiles.

---

## Endpoint reference

| Endpoint | Purpose | Latency (warm) |
|---|---|---|
| `POST /v1/drift_check`   | Score current prompt vs anchor profile | ~150–300 ms |
| `POST /v1/recall`        | Top-k memory hits over project notes | ~200 ms |
| `POST /v1/feedback_log`  | Log good/bad signal for adaptive retrain | <50 ms |
| `POST /mcp/tools/call`   | Same as above but via MCP-over-HTTP envelope | same |
| `GET  /healthz` `/readyz` | k8s probes | <5 ms |

All endpoints accept optional `X-Tenant-ID: <tenant>` header. Defaults to `default`.

---

## Python (V5 SuperAgent / Kairos / generic)

```python
import os
import requests

COMPASS_URL = os.environ.get("COMPASS_URL", "http://compass-gateway:8765")
TENANT_ID   = os.environ.get("NAUTILUS_TENANT_ID", "default")

class CompassClient:
    def __init__(self, base_url=COMPASS_URL, tenant=TENANT_ID, timeout=2.0):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-Tenant-ID": tenant, "Content-Type": "application/json"}
        self.timeout = timeout

    def drift_check(self, prompt, project=None):
        r = requests.post(f"{self.base_url}/v1/drift_check",
                          json={"prompt": prompt, "project": project},
                          headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()   # {score, alignment, deviation, should_alert, top_neg_hits, ...}

    def recall(self, query, project=None, top_k=5):
        r = requests.post(f"{self.base_url}/v1/recall",
                          json={"query": query, "project": project, "top_k": top_k},
                          headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def feedback(self, direction, reason=""):
        r = requests.post(f"{self.base_url}/v1/feedback_log",
                          json={"direction": direction, "reason": reason},
                          headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()


# === Usage in an agent's per-turn handler ===
compass = CompassClient(tenant="caishen")

def handle_user_turn(user_prompt, agent_state):
    # Step 1 · drift gate · L2 BLOCK / L3 ESCALATE / L5 INJECT
    drift = compass.drift_check(user_prompt)
    if drift["should_alert"]:
        # L5 inject mode (default) · prepend warning context
        agent_state.system_context.append(
            f"[drift alert · score={drift['score']:.3f} · "
            f"matched: {[h[1] for h in drift['top_neg_hits'][:2]]}]"
        )
        # alternatively L2 block: refuse to proceed
        # alternatively L3 escalate: route to human review queue

    # Step 2 · pull relevant memory
    memories = compass.recall(user_prompt, top_k=3)
    for hit in memories["hits"]:
        agent_state.system_context.append(
            f"[memory · score={hit['score']:.2f} · age={hit['age_str']}] {hit['description']}"
        )

    # Step 3 · run LLM (your usual call) ...
    response = your_llm_runtime.complete(user_prompt, agent_state)

    # Step 4 · log a feedback signal if the user reacts
    if user_says("that was wrong"):
        compass.feedback("good", reason="caught real drift on previous turn")

    return response
```

---

## Go (Hermes / custom Go agents)

```go
package compass

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
    "time"
)

type Client struct {
    BaseURL string
    Tenant  string
    HTTP    *http.Client
}

type DriftResult struct {
    Score       float64    `json:"score"`
    Alignment   float64    `json:"alignment"`
    Deviation   float64    `json:"deviation"`
    ShouldAlert bool       `json:"should_alert"`
    TopNegHits  [][]any    `json:"top_neg_hits"`
}

func (c *Client) DriftCheck(prompt string) (*DriftResult, error) {
    body, _ := json.Marshal(map[string]string{"prompt": prompt})
    req, _ := http.NewRequest("POST",
        c.BaseURL+"/v1/drift_check", bytes.NewReader(body))
    req.Header.Set("X-Tenant-ID", c.Tenant)
    req.Header.Set("Content-Type", "application/json")
    res, err := c.HTTP.Do(req)
    if err != nil { return nil, err }
    defer res.Body.Close()
    if res.StatusCode >= 400 {
        return nil, fmt.Errorf("compass: status %d", res.StatusCode)
    }
    var out DriftResult
    return &out, json.NewDecoder(res.Body).Decode(&out)
}

func New(baseURL, tenant string) *Client {
    return &Client{
        BaseURL: baseURL,
        Tenant:  tenant,
        HTTP:    &http.Client{Timeout: 2 * time.Second},
    }
}
```

---

## Node / TypeScript

```typescript
const compass = {
  base: process.env.COMPASS_URL ?? "http://compass-gateway:8765",
  tenant: process.env.NAUTILUS_TENANT_ID ?? "default",

  async driftCheck(prompt: string) {
    const r = await fetch(`${this.base}/v1/drift_check`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Tenant-ID": this.tenant },
      body: JSON.stringify({ prompt }),
    });
    if (!r.ok) throw new Error(`compass ${r.status}`);
    return r.json();
  },

  async recall(query: string, topK = 5) {
    const r = await fetch(`${this.base}/v1/recall`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Tenant-ID": this.tenant },
      body: JSON.stringify({ query, top_k: topK }),
    });
    return r.json();
  },
};
```

---

## Deployment modes (5 levels)

Compass as a platform product supports five integration depths. Pick based on how invasive you want drift handling to be.

| Mode | What happens on drift alert | Risk | Reversibility |
|---|---|---|---|
| **L1 audit**     | Log only · agent runs unchanged | none | trivial |
| **L2 block**     | Return 403 to agent · refuse turn | high (false positives kill UX) | per-request |
| **L3 escalate**  | Route conversation to human review queue | medium | per-conversation |
| **L4 reroute**   | Fall back to a more conservative model (Claude → Haiku) | low | per-turn |
| **L5 inject**    | Add warning context to system prompt · let model decide | very low | self-correcting |

Default and recommended: **L5 inject**. Move to L2/L3 only after L5 baseline metrics show acceptable false-positive rate.

---

## Custom anchor profiles (per-tenant drift policies)

Each tenant can ship a custom `anchors_<tenant>.json` (25 task-shaped positives + 35 negatives) tailored to its domain. Mount the directory:

```yaml
# docker-compose.yml
volumes:
  - ./tenant-anchors:/opt/compass/anchors:ro
```

Reference profiles ship with the repo:

| Profile | Domain | Typical use |
|---|---|---|
| `anchors.json` (default) | general coding | dev tools / AI assistants |
| `anchors_legal.json`     | legal writing  | contract review · case research |
| `anchors_medical.json`   | medical Q&A    | symptom triage · clinical notes |
| `anchors_finance.json`   | financial      | trading desks · investment notes |
| `anchors_vc.json`        | VC analyst     | dealflow · diligence |

Generate your own with `python anchor_generator.py` (see `CONTRIBUTING.md`).

---

## Production checklist

- [ ] Deploy `ops/docker-compose.yml` with persistent volume for `.cache/`
- [ ] Set `COMPASS_DEFAULT_TENANT` and `COMPASS_DEFAULT_PROJECT` env per environment
- [ ] Mount tenant anchor profiles read-only at `/opt/compass/anchors`
- [ ] Front gateway with TLS-terminating proxy (nginx/traefik) for external traffic
- [ ] Add `X-API-Key` auth at proxy layer (gateway itself is open by design)
- [ ] Wire `/healthz` to liveness · `/readyz` to readiness (k8s)
- [ ] Scrape `.cache/gateway_access.jsonl` for QPS / latency / per-tenant volume metrics
- [ ] Periodic anchor retrain: `python feedback.py retrain --tenant <id>` (cron · weekly)
- [ ] Soak test before L2/L3 modes: run 1–2 weeks at L1 audit + measure FP rate

---

## Performance budget

| Quantity | Per-call | Notes |
|---|---|---|
| Wire latency (LAN) | <1 ms |  |
| BGE-m3 embed (CPU) | ~150 ms | most of the budget |
| Anchor cosine (60 anchors) | <5 ms | precomputed embeddings |
| Memory recall (29 entries · top-5) | ~30 ms | cosine over disk-cached embeddings |
| **Total (drift_check)** | **~200 ms** | warm · daemon cached |
| **Total (recall)** | **~200 ms** | warm |

CPU-only · single daemon pod. With GPU embedder you can hit <50 ms but the cost dominates the entire architecture, so we don't recommend it. Throughput per gateway worker: ~5 RPS sustained, ~15 RPS burst.

For >100 RPS sustained: shard the daemon by tenant (consistent hashing in gateway) so each daemon pod warms only the anchor profiles it serves.
