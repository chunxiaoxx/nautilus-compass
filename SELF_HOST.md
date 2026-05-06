# compass · self-host guide

> Status: 2026-05-05 · enterprise / privacy-conscious users
> Time to deploy: ~30 minutes

## Why self-host

```
+ Data 100% in your infrastructure (PIPL · GDPR · CCPA · HIPAA)
+ No external dependencies (after initial model download)
+ No Pro tier billing (it's MIT · forever free)
+ Full audit log + monitoring
+ Custom anchor packs for your domain
- You operate the GPU + sqlite + scaling
- You handle backup + rotation + uptime
- v1.0 features may need 30 days behind hosted (we patch hosted first)
```

## Prerequisites

- Docker 20.10+
- docker-compose 1.29+
- (Optional) NVIDIA GPU + nvidia-container-toolkit (for bge-m3 inference at full speed)
- (Optional) Domain name + Let's Encrypt cert (for HTTPS)

## Quick start (CPU mode · 30 min)

```bash
# 1. Clone
git clone https://github.com/chunxiaoxx/nautilus-compass
cd nautilus-compass

# 2. Configure
cp .env.example .env
# Edit .env · at minimum set NAUTILUS_JWT_SECRET (random 32 bytes)
nano .env

# 3. Build + start (~ 5 min on first build)
docker-compose up -d --build

# 4. Wait for daemon to load bge-m3 (60-90s on cold start · CPU mode)
docker-compose logs -f compass-daemon
# Look for: "[daemon] BGE-m3 ready · listening on :9876"

# 5. Verify
curl http://localhost:8765/healthz
# {"status":"ok","service":"compass-gateway","version":"0.9.0-dev",...}

# 6. (Optional) Migrate existing memory/*.md
docker-compose exec compass-api python tools/migrate_to_sqlite.py \
  --user-id u_admin --db /data/compass.db
```

## With GPU (5-10× faster · recommended)

```bash
# Verify nvidia-container-toolkit installed:
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi

# Set GPU mode in .env
# ZMM_DEVICE=cuda

# Restart
docker-compose down
docker-compose up -d
```

## With nginx + HTTPS (production)

```bash
# Get certs first
sudo certbot certonly --standalone -d compass.yourdomain.com

# Edit nginx_v10.conf · adjust server_name + cert paths

# Start with nginx (port 443 binding)
docker-compose up -d
# Already includes nginx service

# Verify
curl https://compass.yourdomain.com/healthz
```

## With RAID-2 reviewer (Team / Enterprise plan)

```bash
# Enable the org profile
docker-compose --profile org up -d

# This adds compass-raid worker that polls ~/.compass/raid_queue/
# RAID-2 means writer-reviewer separation · obs need approval before persisting

# Verify
docker-compose exec compass-raid python compass_raid.py status
```

## With Nautilus stake integration

```bash
# Set stake URL in .env
# NAUTILUS_STAKE_URL=https://a2a-registry.nautilus.social/a2a/messages
# NAUTILUS_API_TOKEN=...

# Enable nautilus profile
docker-compose --profile nautilus up -d

# Verify
docker-compose exec compass-stake python stake_publisher.py status
```

## With Postgres (v1.1+ · large scale)

```bash
# Add scale profile
docker-compose --profile scale up -d

# Migrate sqlite → postgres
docker-compose exec compass-api python tools/migrate_sqlite_to_postgres.py
# (script not yet shipped · v1.1)
```

## Backup

```bash
# Daily backup (cron)
0 3 * * * docker-compose -f /opt/compass/docker-compose.yml exec -T compass-api \
          sqlite3 /data/compass.db ".backup /data/backup-$(date +\%F).db"

# Test restore
docker-compose down
cp /data/backup-2026-05-05.db /var/lib/compass-volume/compass.db
docker-compose up -d
```

## Monitoring (recommended)

```bash
# Health endpoint exposes basic metrics
curl http://localhost:8765/healthz | jq

# Prometheus scrape (planned v0.9.5)
curl http://localhost:8765/metrics
# v0.9.0 placeholder · not implemented · open issue if you want it now
```

## Update

```bash
cd /opt/compass
git pull
docker-compose down
docker-compose up -d --build
```

## Troubleshoot

### Daemon stuck on "BGE-m3 loading"

```bash
# Cold start = 60-90s on CPU · 15s on GPU · be patient
# Check disk: model weights need ~2.5GB free
df -h /var/lib/docker

# Check HF mirror reachable
docker-compose exec compass-daemon curl -I https://hf-mirror.com
```

### "JWT verification failed"

```bash
# NAUTILUS_JWT_SECRET must match across all services
docker-compose config | grep JWT
# All references to NAUTILUS_JWT_SECRET should resolve to same value
```

### Port 8765 / 443 busy

```bash
# Override in .env
echo "COMPASS_API_PORT=8770" >> .env
docker-compose up -d
```

### High memory usage

```bash
# bge-m3 + reranker uses 5GB minimum
# In CPU mode · reduce worker count
echo "COMPASS_API_WORKERS=2" >> .env
docker-compose restart compass-api
```

## Security hardening

- ✅ Use random 32-byte `NAUTILUS_JWT_SECRET` (not the example)
- ✅ Run as non-root user (Dockerfile already does this)
- ✅ Keep `.env` out of git (`.gitignore` already covers)
- ✅ Run nginx with TLS termination (don't expose 8765 public)
- ✅ Rotate JWT secret every 90 days (invalidates all tokens · users re-login)
- ✅ Monitor `/v1/audit_log` (v0.9.6+) for suspicious access
- ✅ Limit `compass-api` workers to your CPU count (default 4 fine for most)
- ✅ Use Postgres if MAU > 10K (sqlite locks become a bottleneck)

## Compliance audit

- Backup encryption: Use `cryptsetup` on Docker volume · keys rotation
- Access log: nginx logs to `/var/log/nginx/compass-access.log`
- Right to delete: `DELETE /v1/users/me` cascades to observations · 30d soft-delete
- PII isolation: encrypted_body never exits the user's region · meta is encrypted at rest

## Migration from hosted (compass.nautilus.social)

```bash
# 1. Export your hosted data
curl -H "Authorization: Bearer $token" \
  https://compass.nautilus.social/v1/observations?since=2026-01-01 \
  > my-observations.json

# 2. Import to self-host
docker-compose exec compass-api python tools/import_observations.py \
  --user-id u_admin --file /tmp/my-observations.json
# (script not yet shipped · v0.9.5)
```

## Get help

- Issues: https://github.com/chunxiaoxx/nautilus-compass/issues
- Docs: paper/V10_FINAL_SPEC.md · paper/V09_API_SPEC.md
- Security: SECURITY.md · responsibly disclose

---

**TL;DR**: `cp .env.example .env && docker-compose up -d` · 30 min to a working
self-hosted compass · works on any server with Docker.
