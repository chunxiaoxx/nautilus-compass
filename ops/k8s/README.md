# Nautilus Compass · Kubernetes Deploy

Production-grade k8s manifests for the Compass platform: daemon as singleton (model resident in RAM), gateway as horizontally autoscaled Deployment, with TLS Ingress and per-tenant secrets.

## Architecture

```
                     ┌──────────────────────────┐
   external traffic  │  Ingress (TLS · nginx)   │
        ▼            │  compass.example.com     │
                     └──────────────────────────┘
                                 │
                                 ▼
                  ┌────────────────────────────────┐
                  │  compass-gateway (Deployment)  │
                  │  N replicas · HPA on CPU 70%   │
                  │  reads tenants.json from Secret│
                  │  reads anchors from ConfigMap  │
                  └────────────────────────────────┘
                                 │
                          ClusterIP DNS
                                 │
                                 ▼
                  ┌────────────────────────────────┐
                  │  compass-daemon (StatefulSet)  │
                  │  1 replica · 4 GiB RAM         │
                  │  PVC: 5 GiB ModelScope cache   │
                  │  PVC: 2 GiB .cache (anchors.pkl)│
                  │  PDB: maxUnavailable=0          │
                  └────────────────────────────────┘
```

Why daemon = StatefulSet replica=1?

The daemon holds an in-memory anchor cache keyed by anchor-file path. The cache is currently NOT shared across pods. Two daemons would each cold-load m3 (60 s) and rebuild anchor embeddings independently → 2× memory and stale-cache divergence. To horizontally scale the daemon, either:

1. Shard by tenant (consistent-hash routing in gateway)
2. Move anchor-embedding cache to Redis (planned v0.8)

Until then, treat daemon as singleton. Gateway scales freely (it's stateless).

## Files

| File | Purpose |
|---|---|
| `daemon.yaml`    | StatefulSet · Service · PDB · 2× PVC |
| `gateway.yaml`   | Deployment · Service · HPA |
| `config.yaml`    | Tenants Secret + Anchors ConfigMap |
| `ingress.yaml`   | TLS Ingress (nginx · cert-manager) — optional |
| `kustomization.yaml` | one-shot apply via `kubectl apply -k` |

## Deploy

```bash
# 1. Build + push image (or use the published one)
docker build -f ops/Dockerfile -t ghcr.io/<you>/nautilus-compass:0.7.2 .
docker push ghcr.io/<you>/nautilus-compass:0.7.2

# 2. Edit config.yaml — replace REPLACE_WITH_GENERATED_KEY values
openssl rand -base64 32   # paste the output as api_key for each tenant

# 3. (Optional) edit ingress.yaml host + cert-manager issuer

# 4. Apply
kubectl create namespace nautilus
kubectl apply -k ops/k8s -n nautilus

# 5. Wait for daemon cold-load (≈90 s including m3 download from ModelScope)
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/component=daemon \
    -n nautilus --timeout=180s

# 6. Verify
kubectl exec -n nautilus deploy/compass-gateway -- curl -fs http://compass-gateway:8765/healthz
kubectl exec -n nautilus deploy/compass-gateway -- curl -fs http://compass-gateway:8765/readyz

# 7. From outside cluster (assumes Ingress)
curl -X POST https://compass.example.com/v1/drift_check \
     -H "Content-Type: application/json" \
     -H "X-Tenant-ID: caishen" \
     -H "X-API-Key: <your-generated-key>" \
     -d '{"prompt":"rm -rf production database"}'
```

## Resource budget

| Component | replicas | CPU req | CPU lim | Mem req | Mem lim | Storage |
|---|---|---|---|---|---|---|
| daemon  | 1 (fixed)        | 1   | 2     | 3 Gi  | 4 Gi  | 7 Gi PVC |
| gateway | 1–10 (HPA)       | 100m| 500m  | 256 Mi| 512 Mi | — |

Minimum cluster footprint: ≈3.3 Gi RAM + 1.1 vCPU + 7 Gi PVC at 1 gateway replica. At 10 gateway replicas under load: ≈8 Gi RAM + 6 vCPU.

## TLS / Auth in front of gateway

The gateway itself does header-based API-key auth (`X-API-Key` per tenant). For external exposure:

- Terminate TLS at the Ingress (cert-manager + Let's Encrypt is the default config).
- Optionally add an oauth2-proxy in front for human users (machine traffic uses X-API-Key directly).
- Rate-limit at Ingress nginx OR at gateway (both supported simultaneously).

## Operations

- **Per-tenant key rotation**: kubectl edit secret compass-tenants → new key → gateway pods reload automatically (mtime polling on file backend).
- **Add new tenant**: same edit pattern. No restart needed.
- **Scale daemon vertically**: kubectl edit statefulset compass-daemon → bump resources.
- **Update model**: bake new model into image, kubectl set image statefulset/compass-daemon daemon=...:0.7.3 → graceful restart with rolling update (single replica means brief unavailability; PDB allows it because maxUnavailable=0 only applies to voluntary disruptions, not deployment rollouts).
- **Backup feedback logs**: gateway writes to ephemeral `.cache/feedback_<tenant>.jsonl`. For persistence in k8s, mount a PVC at `/opt/compass/.cache` on gateway pods OR ship logs to centralized log store (Loki/CloudWatch).

## Known limitations

- **In-memory rate limit** is per-pod, not cluster-wide. Under N gateway replicas, effective limit is N × `rate_limit_per_min`. Use Redis-backed rate limit (planned v0.8) for true cluster quota.
- **Single daemon pod** is the throughput bottleneck (~5 RPS sustained per BGE-m3 worker on CPU). For >50 RPS, run gateway with backpressure or upgrade to GPU embedding.
- **Anchor ConfigMap size** caps at 1 MB. Each `anchors_*.json` is ~30 KB so this fits 30+ profiles; shard into multiple ConfigMaps if needed.
