#!/bin/bash
# Reset database and run migrations
# Usage: ./scripts/reset-db.sh
#
# Note: This only resets the schema. To seed demo data, run:
#   ./scripts/seed-demo.sh

set -e

echo "Resetting database..."

# Reset alembic version
docker-compose exec -T db psql -U dental -d dental_clinic -c "DELETE FROM alembic_version;" 2>/dev/null || true

# Drop all tables (in correct order to handle foreign keys)
docker-compose exec -T db psql -U dental -d dental_clinic << 'EOF'
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'alembic_version')
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;
EOF

# Run migrations
docker-compose exec -T backend alembic upgrade head

echo ""
echo "Database reset complete!"
echo "Run ./scripts/seed-demo.sh to create demo data."
