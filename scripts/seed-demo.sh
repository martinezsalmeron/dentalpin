#!/bin/bash
# Seed DentalPin with demo data

set -e

echo "Seeding demo data..."
docker-compose exec -T backend bash -c "PYTHONPATH=/app python /app/scripts/seed_demo.py --lang es"
