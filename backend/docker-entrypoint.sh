#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "[entrypoint] Running alembic upgrade head..."
  alembic upgrade head
fi

exec "$@"
