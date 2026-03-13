# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.


## Project Overview

Full-stack web application: FastAPI backend + React frontend with PostgreSQL, Docker Compose orchestration, and Traefik reverse proxy.

## Project Structure

### Backend (`backend/app/`)

- **`api/`**: REST API endpoints (routes).
- **`core/`**: Core configuration, security, and database settings.
- **`domain/`**: Pydantic schemas and interface definitions.
- **`models/`**: SQLModel database models.
- **`repository/`**: Database access layer (CRUD operations).
- **`services/`**: Business logic layer.
- **`email-templates/`**: Email templates and build scripts.
- **`main.py`**: Application entry point.

### Frontend (`frontend/src/`)

- **`client/`**: Generated OpenAPI client code.
- **`components/`**: React components (Common, Admin, etc.).
- **`hooks/`**: Custom React hooks.
- **`routes/`**: Page components for TanStack Router.
- **`lib/`**: Utility libraries.
- **`server/`**: Server-side logic (if applicable).
- **`routeTree.gen.ts`**: Generated routing configuration.


## Common Commands

### Backend (run from `backend/`)
- **Install deps**: `uv sync`
- **Run dev server**: `fastapi run --reload app/main.py`
- **Run tests**: `bash ./scripts/test.sh` (with coverage) or `pytest` directly
- **Run single test**: `pytest tests/api/routes/test_users.py::test_create_user -v`
- **Lint**: `bash ./scripts/lint.sh` (runs ruff check)
- **Format**: `bash ./scripts/format.sh` (runs ruff format)
- **Type check**: `mypy`

### Frontend (run from `frontend/`)
- **Install deps**: `bun install`
- **Dev server**: `bun run dev` (Vite, port 5173)
- **Build**: `tsc -p tsconfig.build.json && vite build`
- **Lint/format**: `biome check --write --unsafe ./`
- **Generate API client**: `bun run generate-client` (regenerates `src/client/` from OpenAPI spec)
- **E2E tests**: `bunx playwright test`

### Docker
- **Start all with live reload**: `docker compose watch`
- **Start services**: `docker compose up -d`
- **Run backend tests in container**: `docker compose exec backend bash scripts/tests-start.sh`
- **Stop and clean volumes**: `docker compose down -v`

## Architecture

### Backend Layered Architecture (`backend/app/`)

The backend follows domain-driven design with these layers:

- **`api/routes/`** — HTTP route handlers. Use FastAPI dependency injection for DB sessions and auth.
- **`domain/`** — Pydantic schemas (DTOs) for request/response validation. Shared base classes (e.g., `UserBase`, `ItemBase`) are inherited by both domain schemas and ORM models.
- **`models/`** — SQLModel ORM classes (`table=True`). Inherit from domain base schemas. Define DB relationships and columns.
- **`repository/`** — Data access functions (CRUD). Accept `Session` parameter, return ORM models. No business logic.
- **`services/`** — Business logic layer. Orchestrates repository calls with domain rules (e.g., `auth.py` handles authentication with timing-attack prevention).
- **`core/`** — Infrastructure: `config.py` (Pydantic BaseSettings from `.env`), `db.py` (SQLAlchemy engine, init), `security.py` (JWT, password hashing with pwdlib/Argon2).

### Dependency Injection (`api/deps.py`)

Key injectable types used across all routes:
- `SessionDep` — SQLModel database session
- `CurrentUser` — Authenticated user (from JWT token)
- `TokenDep` — Raw OAuth2 bearer token string

### Database

- **ORM**: SQLModel (SQLAlchemy + Pydantic hybrid)
- **DB**: PostgreSQL 18
- **Migrations**: None (Alembic removed). Tables created via `SQLModel.metadata.create_all()` on startup.
- **IDs**: UUID primary keys with `uuid.uuid4` defaults
- **Timestamps**: UTC datetime with `created_at` fields

### Frontend (`frontend/src/`)

- **React 19** with TypeScript, **Vite** bundler
- **Routing**: TanStack Router (file-based, auto-generated `routeTree.gen.ts`)
- **State/Data**: TanStack Query (React Query)
- **UI**: shadcn/ui components (Radix primitives) in `components/ui/`
- **Styling**: Tailwind CSS
- **Forms**: React Hook Form + Zod validation
- **API Client**: Auto-generated from backend OpenAPI spec via `openapi-ts` into `src/client/`

### Config & Environment

All configuration flows through `core/config.py` (`Settings` class) reading from `.env` at project root. Access via `from app.core.config import settings`. Key computed fields: `SQLALCHEMY_DATABASE_URI`, `emails_enabled`. Non-default secrets enforced in non-local environments.

### Docker Services (compose.yml)

`db` (PostgreSQL) → `prestart` (DB init) → `backend` (FastAPI, port 8000) → `frontend` (Nginx, port 80) → `proxy` (Traefik). Local override adds hot reload, Mailcatcher (SMTP on 1025, UI on 1080), and Playwright.
