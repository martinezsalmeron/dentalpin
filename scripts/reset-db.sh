#!/bin/bash
# Reset database and create demo data
# Usage: ./scripts/reset-db.sh

set -e

echo "Resetting database..."

# Reset alembic version
docker-compose exec -T db psql -U dental -d dental_clinic -c "DELETE FROM alembic_version;" 2>/dev/null || true

# Run migrations
docker-compose exec -T backend alembic upgrade head

# Generate password hash
HASH=$(docker-compose exec -T backend python -c "
from app.core.auth.service import hash_password
print(hash_password('demo1234'))
")

# Create demo data
docker-compose exec -T db psql -U dental -d dental_clinic << EOF
-- Create demo clinic (if not exists)
INSERT INTO clinics (id, name, tax_id, settings, cabinets, created_at, updated_at)
VALUES (
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'Demo Clinic',
    'B12345678',
    '{"slot_duration_min": 30, "currency": "EUR", "timezone": "Europe/Madrid"}',
    '[{"name": "Gabinete 1", "color": "#3B82F6"}, {"name": "Gabinete 2", "color": "#10B981"}]',
    NOW(), NOW()
) ON CONFLICT (id) DO NOTHING;

-- Create demo admin user (password: demo1234)
INSERT INTO users (id, email, password_hash, first_name, last_name, is_active, token_version, created_at, updated_at)
VALUES (
    'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22',
    'admin@demo.clinic',
    '${HASH}',
    'Admin',
    'Demo',
    true,
    0,
    NOW(), NOW()
) ON CONFLICT (id) DO UPDATE SET password_hash = EXCLUDED.password_hash;

-- Create clinic membership
INSERT INTO clinic_memberships (id, user_id, clinic_id, role, created_at, updated_at)
VALUES (
    'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33',
    'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22',
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'admin',
    NOW(), NOW()
) ON CONFLICT (id) DO NOTHING;
EOF

echo ""
echo "Database reset complete!"
echo "Demo credentials: admin@demo.clinic / demo1234"
