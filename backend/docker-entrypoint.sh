#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "[entrypoint] Running alembic upgrade head..."
  alembic upgrade head
fi

if [ "${SEED_ON_STARTUP:-0}" = "1" ]; then
  (
    SEED_LANG_ARG="${SEED_LANG:-es}"
    for i in $(seq 1 60); do
      if python -c "import urllib.request,sys
try:
    sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=1).status == 200 else 1)
except Exception:
    sys.exit(1)" 2>/dev/null; then
        echo "[entrypoint] Backend healthy — running seed (lang=$SEED_LANG_ARG)"
        PYTHONPATH=/app python /app/scripts/seed_demo.py --lang "$SEED_LANG_ARG" || echo "[entrypoint] Seed failed (non-fatal)"
        exit 0
      fi
      sleep 1
    done
    echo "[entrypoint] Backend never became healthy — seed skipped"
  ) &
fi

exec "$@"
