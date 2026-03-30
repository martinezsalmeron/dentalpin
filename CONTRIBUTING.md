# Contributing to DentalPin

Thank you for your interest in contributing to DentalPin!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/dentalpin.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest backend/tests/ -v` and `cd frontend && npm test`
6. Commit with a descriptive message
7. Push and create a Pull Request

## Development Setup

```bash
# Start development environment
docker-compose up

# Backend only (with hot reload)
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend only
cd frontend
npm install
npm run dev
```

## Code Style

### Python (Backend)
- Use `ruff` for linting and formatting
- Type hints required for all functions
- Follow PEP 8 naming conventions
- Docstrings for public functions

### TypeScript (Frontend)
- ESLint + Prettier for formatting
- Strict TypeScript mode
- Vue 3 Composition API with `<script setup>`

## Pull Request Guidelines

1. **One feature per PR** - Keep PRs focused and reviewable
2. **Tests required** - Add tests for new functionality
3. **Update docs** - Update README or docs if behavior changes
4. **Descriptive commits** - Use clear commit messages

## Reporting Issues

- Use GitHub Issues
- Include steps to reproduce
- Include expected vs actual behavior
- Include browser/OS/version if relevant

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Questions?

Open an issue with the "question" label.
