#!/bin/bash
# Full demo setup: reset database and seed demo data
# Usage: ./scripts/setup-demo.sh

set -e

echo "============================================================"
echo "DentalPin Full Demo Setup"
echo "============================================================"
echo ""

# Reset database (migrations)
echo "[1/2] Resetting database..."
./scripts/reset-db.sh

# Seed demo data
echo ""
echo "[2/2] Seeding demo data..."
./scripts/seed-demo.sh

echo ""
echo "============================================================"
echo "Setup complete! Open http://localhost:3000"
echo "============================================================"
