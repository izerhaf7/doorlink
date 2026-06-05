# Repository Guidelines

## Project Structure & Module Organization

This repository contains a FastAPI backend for DoorLink under `backend/`. Application code lives in `backend/app/`:

- `main.py` wires the FastAPI app, startup database creation, default role seeding, static files, and routers.
- `models/` contains SQLModel database models such as users, roles, and access logs.
- `schemas/` contains Pydantic/SQLModel request and response schemas.
- `routers/` contains API and dashboard route modules, named with the `_router.py` suffix.
- `services/` contains business logic and integrations, including MikroTik operations.
- `templates/` and `static/` contain the Jinja2 dashboard UI and CSS assets.

Local runtime files include `backend/.env` and `backend/doorlink.db`; avoid committing local secrets or generated databases.

## Build, Test, and Development Commands

Run commands from `backend/` unless noted otherwise.

- `python -m venv venv` creates a local virtual environment.
- `venv\Scripts\Activate.ps1` activates it on Windows PowerShell.
- `pip install -r requirements.txt` installs FastAPI, Uvicorn, SQLModel, Jinja2, dotenv, and related dependencies.
- `copy .env.example .env` creates local configuration; edit MikroTik and database values as needed.
- `uvicorn app.main:app --reload` starts the development server at `http://127.0.0.1:8000`.
- `uvicorn app.main:app --reload --port 8001` starts on an alternate port if 8000 is busy.

## Coding Style & Naming Conventions

Use Python 3.10+ and follow PEP 8 with 4-space indentation. Keep routers thin: validate HTTP inputs in `routers/`, put database and integration logic in `services/`, and keep persisted shapes in `models/`. Use `snake_case` for functions, variables, and module names. Name new route files like `feature_router.py`, models like `feature_model.py`, and schemas like `feature_schema.py`.

## Testing Guidelines

No first-party test suite is currently present. Add tests under `backend/tests/` when changing behavior, especially for services and API endpoints. Prefer `pytest` with files named `test_<feature>.py`; add `pytest` to `requirements.txt` when introducing the test suite. Run tests from `backend/` with `pytest`.

## Commit & Pull Request Guidelines

Git history currently only shows `first commit`, so no detailed convention is established. Use short, imperative commit messages such as `Add user access validation` or `Fix dashboard log filtering`. Pull requests should include a clear summary, configuration or database impacts, test results, and screenshots when dashboard templates or static assets change.

## Security & Configuration Tips

Do not hard-code MikroTik credentials, database URLs, or passwords. Keep `.env` local and update `.env.example` when adding required configuration keys. Treat `doorlink.db`, virtual environments, `__pycache__/`, and other generated files as local artifacts.
