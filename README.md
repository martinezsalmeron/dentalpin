# DentalPin

Open source dental clinic management software. Built with modular architecture for extensibility.

## Quick Start

```bash
docker-compose up
```

Open http://localhost:3000

**Demo credentials:** `admin@demo.clinic` / `demo1234`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11+) |
| Frontend | Nuxt 3 + Nuxt UI |
| Database | PostgreSQL 15 |
| Auth | JWT with refresh tokens |

## Features (MVP)

- Patient management (create, search, view, edit)
- Appointment calendar (weekly view, conflict detection)
- Single clinic, admin role
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

### Running tests

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm run test
```

## Architecture

DentalPin uses a modular plugin architecture. Each feature is a self-contained module that:
- Declares its SQLAlchemy models
- Provides a FastAPI router
- Can subscribe to events from other modules

See [docs/architecture.md](docs/docs/architecture.md) for details.

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
