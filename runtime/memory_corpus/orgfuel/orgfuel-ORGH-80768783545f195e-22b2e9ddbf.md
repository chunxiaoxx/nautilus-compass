---
name: orgfuel-ORGH-80768783545f195e-22b2e9ddbf
description: "commit 66df3e2fa214 2026-04-30 feat: k8s manifests · daemon "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-80768783545f195e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 66df3e2fa214 2026-04-30
feat: k8s manifests · daemon StatefulSet + gateway Deployment + HPA
ops/k8s/:
· daemon.yaml — StatefulSet (replicas=1 · 4Gi RAM · 2 PVCs: model cache + .cache)
  · headless Service for stable DNS
  · ClusterIP Service for in-cluster TCP 9876 access
  · PDB maxUnavailable=0 (don't drain during voluntary disruptions)
  · TCP startup probe with 150 s grace for m3 cold-load
· gateway.yaml — Deployment (replicas=2) + ClusterIP Service + HPA
  · HPA 1-10 replicas · target CPU 70%
  · stateless · reads tenants.json from Secret · anchors from ConfigMap
  · /readyz wired to readinessProbe (probes daemon TCP)
· config.yaml — compass-tenants Secret + compass-anchors ConfigMap
  · placeholder REPLACE_WITH_GENERATED_KEY for live keys
· ingress.yaml — TLS Ingress (nginx + 
