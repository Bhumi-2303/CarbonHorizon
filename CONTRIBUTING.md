# Contributing to Carbon Horizon

We welcome contributions of all kinds to Carbon Horizon! Whether you are fixing bugs, optimizing carbon logic, enhancing UI accessibility, or adding new features, this guide will help you get started.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

1. **Fork the Repository:** Create a personal copy of the project on GitHub.
2. **Setup Local Environment:**
   - Follow the [README.md](README.md) instructions to setup local Postgres, Python virtualenv for the backend, and Node modules for the frontend.
3. **Create a Branch:** Create a branch for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Backend (Python/FastAPI)
- Standardize on PostgreSQL compatibility.
- Ensure validation schemas are structured using Pydantic.
- Run tests and enforce code quality:
  ```bash
  cd backend
  pytest --cov=app --cov-fail-under=90
  flake8 app tests
  ```

### Frontend (React/TypeScript)
- Maintain semantic markup and WCAG 2.1 AA accessibility guidelines.
- Always run a type check before proposing changes:
  ```bash
  cd frontend
  npm run type-check
  ```

## Submitting Pull Requests

1. **Commit Guidelines:** Use logical, granular commits. Add meaningful messages following conventional commits (e.g. `feat(auth): ...`, `fix(ui): ...`, `refactor(db): ...`).
2. **Push Branch:** Push your branch to your remote fork:
   ```bash
   git push origin feature/your-feature-name
   ```
3. **Open a PR:** Open a Pull Request targeting the `main` branch. Ensure the description outlines the changes and links to relevant issues.
4. **CI/CD Validation:** All PRs must pass linting and the 90%+ test coverage gate in GitHub Actions.
