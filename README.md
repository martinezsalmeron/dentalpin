# DentalPin

Open source dental clinic management software. Built with modular architecture for extensibility.

## Quick Start

```bash
# Start services
docker-compose up -d

# Seed demo data
./scripts/seed-demo.sh
```

Open http://localhost:3000

### Demo Credentials

All users have password: `demo1234`

| Email | Role | Name |
|-------|------|------|
| admin@demo.clinic | admin | Admin Demo |
| dentist@demo.clinic | dentist | Dra. María García López |
| hygienist@demo.clinic | hygienist | Carlos López Martínez |
| assistant@demo.clinic | assistant | Ana Martínez Ruiz |
| receptionist@demo.clinic | receptionist | Laura Sánchez Pérez |

See [docs/DEMO.md](docs/DEMO.md) for full details on demo data.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11+) |
| Frontend | Nuxt 3 + Nuxt UI |
| Database | PostgreSQL 15 |
| Auth | JWT with refresh tokens |

## Features (MVP)

- Patient management (create, search, view, edit)
- Appointment calendar (weekly/daily view, drag & drop, conflict detection)
- Multi-role support (admin, dentist, hygienist, assistant, receptionist)
- Spanish localization

## Development

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local backend development)
- Node.js 18+ (for local frontend development)

### Running locally

```bash
# Start all services
docker-compose up

# Or run backend separately
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Or run frontend separately
cd frontend
npm install
npm run dev
```

### Database Management

```bash
# Reset database and run migrations
./scripts/reset-db.sh

# Seed demo data (after reset or fresh install)
./scripts/seed-demo.sh

# Full setup (reset + seed in one command)
./scripts/setup-demo.sh
```

### Running tests

```bash
# Backend (in Docker)
docker-compose exec backend python -m pytest -v

# Frontend
cd frontend
npm run test
```

## Architecture

DentalPin uses a modular plugin architecture. Each feature is a self-contained module that:
- Declares its SQLAlchemy models
- Provides a FastAPI router
- Can subscribe to events from other modules

See [docs/architecture.md](docs/architecture.md) for details.

## License

Business Source License 1.1 (BSL 1.1)

**Use Limitation:** You may not offer DentalPin as a commercial SaaS for dental clinic management.

**Change Date:** 4 years from release

**Change License:** Apache 2.0

See [LICENSE](LICENSE) for full terms.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Backed by

[Dentaltix](https://dentaltix.com) - Dental supplies distributor
