#!/bin/bash
# Reset demo database and reseed. Daily cron + manual.
# Usage: /usr/local/bin/dentalpin-reset-demo.sh [es|en]
#
# This script lives on the demo host at /usr/local/bin/dentalpin-reset-demo.sh
# and is invoked by /etc/cron.d/dentalpin-reset-demo every night at 04:00.
# This file is the source of truth — see scripts/dentalpin-reset-demo.cron
# for the matching crontab. Deploy with:
#
#   scp scripts/dentalpin-reset-demo.sh     root@<host>:/usr/local/bin/
#   scp scripts/dentalpin-reset-demo.cron   root@<host>:/etc/cron.d/dentalpin-reset-demo
#   ssh root@<host> 'chmod +x /usr/local/bin/dentalpin-reset-demo.sh \
#                  && chmod 644 /etc/cron.d/dentalpin-reset-demo'
set -euo pipefail

COOLIFY_PROJECT="wz49q8rmlqkhh9qun1kwgge8"
LANG_ARG="${1:-es}"
LOG_TAG="dentalpin-reset"
log() { logger -t "$LOG_TAG" -- "$*"; echo "[$(date -Is)] $*"; }

find_container() {
  docker ps -q \
    --filter "label=com.docker.compose.project=$COOLIFY_PROJECT" \
    --filter "label=com.docker.compose.service=$1" \
    --filter "status=running" | head -1
}

DB=$(find_container db)
BACK=$(find_container backend)
[ -z "$DB" ] && { log "ERROR: no db container"; exit 1; }
[ -z "$BACK" ] && { log "ERROR: no backend container"; exit 1; }

log "DB=$DB BACK=$BACK lang=$LANG_ARG"

log "Step 1/4: drop schema public + recreate"
docker exec -i "$DB" psql -U dental -d dental_clinic -v ON_ERROR_STOP=1 <<'SQL'
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO dental;
GRANT ALL ON SCHEMA public TO public;
SQL

# `heads` (plural) is required: DentalPin uses one Alembic branch per
# module, so `alembic upgrade head` errors out with "Multiple head
# revisions are present" and — combined with `set -e` — aborts the
# script before Step 3 can restart the backend, leaving the running
# container pointing at a dropped schema until someone restarts it
# by hand.
log "Step 2/4: alembic upgrade heads"
docker exec "$BACK" alembic upgrade heads

log "Step 3/4: restart backend (reconcile module registry)"
docker restart "$BACK" >/dev/null

HEALTH_PY='import urllib.request,sys
try:
    sys.exit(0 if urllib.request.urlopen("http://localhost:8000/health", timeout=2).status == 200 else 1)
except Exception:
    sys.exit(1)'

for i in $(seq 1 60); do
  if docker exec "$BACK" python -c "$HEALTH_PY" 2>/dev/null; then
    log "backend healthy after ${i}s"
    break
  fi
  sleep 1
done

log "Step 4/4: seed demo data (lang=$LANG_ARG)"
docker exec "$BACK" bash -c "PYTHONPATH=/app python /app/scripts/seed_demo.py --lang $LANG_ARG"

log "Reset+seed done"
