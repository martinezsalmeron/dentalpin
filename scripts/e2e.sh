#!/bin/bash
# Run the Playwright browser E2E suite against the live dev stack.
#
# Requirements:
#   - docker-compose is up (backend, frontend, db)
#   - demo data is seeded (./scripts/seed-demo.sh)
#   - Playwright browsers installed on host:
#       (cd frontend && npx playwright install chromium)
#
# Usage:
#   ./scripts/e2e.sh                # full suite
#   ./scripts/e2e.sh rbac           # single file (filter passes to playwright)
#   ./scripts/e2e.sh --ui           # open the Playwright UI
#
# Runs on the host (not inside the frontend container) because the
# container is Alpine and Playwright's precompiled Chromium expects
# glibc. The suite targets http://localhost:3000 / :8000 by default.

set -e

cd "$(dirname "$0")/.."

echo "Waiting for http://localhost:3000 to respond..."
until [ "$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/login)" = "200" ]; do
  sleep 2
done

echo "Running Playwright E2E..."
cd frontend && npx playwright test "$@"
