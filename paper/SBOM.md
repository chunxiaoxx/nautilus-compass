# compass · Software Bill of Materials (SBOM)

> Status: 2026-05-05 · v0.9.0-dev · SLSA-style declaration
> Format: simplified · run-time deps + build-time + transitive (top 20)
> Standard: complies with EO 14028 SBOM minimum elements

## Project info

```
name:         nautilus-compass
version:      0.9.0-dev
license:      MIT
homepage:     https://github.com/chunxiaoxx/nautilus-compass
publisher:    chunxiaoxx (individual · transitioning to Nautilus Platform)
verified:     2026-05-05
```

## Direct dependencies (declared in pyproject.toml)

| Package | Version constraint | License | Purpose | Trust |
|---|---|---|---|---|
| sentence-transformers | ≥2.7 | Apache-2.0 | bge-m3 embeddings · cross-encoder | high (HuggingFace) |
| modelscope | ≥1.10 (optional) | Apache-2.0 | China model mirror | medium |
| hf_transfer | ≥0.1 (optional) | Apache-2.0 | fast HF download | medium |
| pynacl | ≥1.5 (optional · e2ee) | Apache-2.0 | E2EE fallback (libsodium) | high |
| nautilus-agent | ≥0.5 (optional · platform) | (planned MIT) | Nautilus runtime SDK | high (own) |

## v0.9 server runtime

| Package | Version | License | Purpose |
|---|---|---|---|
| fastapi | ≥0.110 | MIT | HTTP server framework |
| uvicorn[standard] | ≥0.27 | BSD-3 | ASGI server |
| python-jose[cryptography] | ≥3.3 | MIT | JWT signing/verification |
| cryptography | ≥41 | Apache-2.0 / BSD | AES-256-GCM · TLS |

## v0.9 server transitive (top 20 only · full list via `pip freeze`)

```
torch                 ~2.6.0 cu124      BSD-3       (sentence-transformers backbone · GPU)
transformers          ~5.7.x            Apache-2.0  (HF · for bge-m3 + reranker)
tokenizers            ~0.20             Apache-2.0  (HF · fast tokenization)
huggingface-hub       ~0.27             Apache-2.0  (model download)
numpy                 ~1.26             BSD-3       (vector ops)
scipy                 ~1.13             BSD-3       (cosine · linalg)
scikit-learn          ~1.5              BSD-3       (TF-IDF · auxiliary)
pydantic              ~2.6              MIT         (FastAPI validation)
starlette             ~0.36             BSD-3       (FastAPI base)
typing_extensions     ~4.10             PSF-2       (Python typing)
anyio                 ~4.3              MIT         (async)
sniffio               ~1.3              MIT/Apache  (async detection)
ecdsa                 ~0.18             MIT         (jose · alt signing)
rsa                   ~4.9              Apache-2.0  (jose · RSA)
pyasn1                ~0.5              BSD-2       (ASN.1)
six                   ~1.16             MIT         (compat shim)
filelock              ~3.13             Unlicense   (HF download lock)
fsspec                ~2024.x           BSD-3       (file system abstraction)
packaging             ~24.0             Apache-2.0/BSD  (version parsing)
regex                 ~2024.x           Apache-2.0  (tokenizers)
```

## Frontend / npm

```
@nautilus/compass-mcp   0.9.0-dev   MIT
  · No runtime deps (pure Node 18 stdlib + spawn)
  · Calls into Python compass-mcp via subprocess

cursor-extension/       0.9.0-dev   MIT
  · @types/node                ~20      MIT
  · @types/vscode              ~1.85    MIT
  · typescript                 ~5.3     Apache-2.0
  · vsce                       ~3       MIT  (build only · not runtime)
  · No production runtime deps
```

## Models (downloaded at runtime · weights are not "code")

```
BAAI/bge-m3                          MIT (model · weights)
  · 1024-dim multilingual embedding
  · 1.2 GB weights · float32 · downloaded once
  · Source: HuggingFace · or hf-mirror.com (China)

BAAI/bge-reranker-v2-m3              MIT (model · weights)
  · 568M params cross-encoder
  · 1.3 GB weights
```

## External APIs (run-time · user provides keys)

| Service | Purpose | Cost (compass-typical) |
|---|---|---|
| Volc Ark coding plan | session_writer · benchmark eval | ¥0.05/session · ¥10/full-500 |
| DeepSeek 官方 API (V4) | benchmark eval (V4 series) | $14/full-500 |
| Anthropic Claude | session_writer fallback · paper subject | $1/session |
| Vertex AI Gemini | benchmark eval · cross-judge | $15/full-500 |
| OpenAI | benchmark eval | $15/full-500 |
| MiniMax | benchmark eval | ¥1/full-500 |

(Compass core is provider-neutral · these are user-configurable.)

## Vulnerability scan history

```
2026-05-05  scan  pip-audit + npm audit · 0 critical · 0 high
            (run quarterly · CI also dependabot)
```

## Provenance

- Source: https://github.com/chunxiaoxx/nautilus-compass
- Build: `pip install -e .[dev]` reproducible from pyproject.toml
- Tests: 36 unit + integration · all pass on Python 3.10/3.11/3.12 · macOS/Linux
- Benchmarks: LongMemEval-S 56.6% n=500 · raw logs in `.cache/longmemeval_acc_*.jsonl`

## Signed releases

```
v0.9.0-dev (current · pending publish)   · git tag v0.9.0-dev
v0.7.0     2026-04-29                     · git tag v0.7.0
```

(Sigstore / cosign signing planned for v1.0 GA.)

## License compatibility

```
nautilus-compass: MIT (compatible with: Apache-2.0 · BSD · MIT · CC0)

All direct deps: Apache-2.0 / MIT / BSD-3 (compatible)
All transitive deps: same family + occasional Unlicense / PSF (still compatible)

Final binary distribution: MIT
```

## EO 14028 SBOM minimum elements

- ✅ Supplier name
- ✅ Component name + version
- ✅ Component license
- ✅ Direct dependency list (above)
- ✅ Author of SBOM data: chunxiaoxx
- ✅ Timestamp: 2026-05-05
- ✅ Component hashes: see git tags + pip wheels (deferred to release time)
- 🟡 Cryptographic signing: planned for v1.0 GA (sigstore + cosign)

## Update cadence

- This file regenerated quarterly or upon any direct-dep major bump
- Dependabot alerts trigger immediate review
- Vulnerability scans automated via GitHub Actions (`pip-audit` + `npm audit`)
