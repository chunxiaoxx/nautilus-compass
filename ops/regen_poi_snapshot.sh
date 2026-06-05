#!/bin/bash
# Regenerate the PoI credit snapshot from the central table (source of truth).
# Atomic write (tmp+mv) · the cloud v14 boost (_v14_poi_boost) mtime-reloads it.
# Deployed on cloud at /home/ubuntu/compass/regen_poi_snapshot.sh · cron every 10min:
#   */10 * * * * /home/ubuntu/compass/regen_poi_snapshot.sh >/dev/null 2>&1
# Snapshot path = /var/lib/compass/poi (systemd ReadWritePaths whitelist · NOT
# /home/ubuntu/compass which is read-only under ProtectHome).
set -e
OUT=/var/lib/compass/poi/poi_credit_snapshot.json
sudo -u postgres psql -tAc \
  "SELECT coalesce(json_object_agg(memory_key, cumulative_impact)::text,'{}') FROM compass.poi_credit" \
  nautilus_production > ${OUT}.tmp
mv ${OUT}.tmp $OUT
