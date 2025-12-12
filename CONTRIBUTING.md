# Contributing to SafeChild

Thank you for your interest in contributing to SafeChild! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We are committed to providing a welcoming and harassment-free experience for everyone.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- MongoDB 7.0+

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/QaziMuhammedKochgiri/safety.git
   cd safety
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services with Docker**
   ```bash
   docker-compose up -d
   ```

4. **Or run locally**
   ```bash
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   uvicorn server:app --reload

   # Frontend
   cd frontend
   yarn install
   yarn start
   ```

## Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commits:
```
type: short description

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Requests

1. Create a branch from `main`
2. Make your changes
3. Run tests: `pytest` (backend) and `yarn test` (frontend)
4. Push and create a PR
5. Wait for CI to pass
6. Request review

## Code Style

### Python (Backend)
- Follow PEP 8
- Use type hints
- Run `black` for formatting
- Run `flake8` for linting

### JavaScript/React (Frontend)
- Use ESLint configuration
- Use Prettier for formatting
- Follow React best practices

## Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=.
```

### Frontend Tests
```bash
cd frontend
yarn test
```

## Security

- Never commit secrets or credentials
- Report security issues privately
- Follow OWASP guidelines

## Questions?

Open an issue or contact the maintainers.
