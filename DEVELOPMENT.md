# Development Guide

This guide covers setting up a fast development environment for kGPT.

## Quick Start (TL;DR)

```bash
# One-time setup
make install

# Start developing (runs backend + frontend with hot-reload)
make dev

# Access:
#   Frontend: http://localhost:5173
#   Backend:  http://localhost:8000
#   API Docs: http://localhost:8000/docs
```

## Prerequisites

- Python 3.11 or 3.12
- Node.js 20+ (for frontend)
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker (for Qdrant vector database)
- Make (usually pre-installed on macOS/Linux)

## Development vs Production

| Mode | Backend | Frontend | Speed | Use Case |
|------|---------|----------|-------|----------|
| **Development** | Local with hot-reload | Local with hot-reload | Fast (instant changes) | Day-to-day coding |
| **Production** | Docker container | Docker container | Slower (rebuild needed) | Final testing, deployment |

**Always use development mode when iterating on code.** Only use Docker for final testing before deploying.

## Setup

### 1. Install Dependencies

```bash
make install
# This runs: uv sync --dev && cd frontend && npm install
```

Or manually:

```bash
# Backend
uv sync --dev
source .venv/bin/activate  # or activate.fish for fish shell

# Frontend
cd frontend && npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, etc.)
```

## Development Workflow

### Start Everything (Recommended)

```bash
make dev
```

This command:

1. Starts Qdrant in Docker (vector database)
2. Starts the FastAPI backend with hot-reload on port 8000
3. Starts the SvelteKit frontend with hot-reload on port 5173

Any code changes automatically reload - no rebuild needed!

### Start Individual Services

If you prefer running things separately:

```bash
# Terminal 1: Infrastructure
make dev-infra

# Terminal 2: Backend
make dev-backend

# Terminal 3: Frontend
make dev-frontend
```

### With Demo Kafka Cluster

```bash
# Start infrastructure including Kafka
make dev-infra-kafka

# Then start backend and frontend normally
make dev-backend  # in one terminal
make dev-frontend # in another terminal
```

## Code Quality Commands

```bash
# Lint code
make lint

# Lint and auto-fix
make lint-fix

# Format code
make format

# Run tests
make test

# Run tests with coverage
make test-cov

# Run all checks
make check
```

## Testing Changes

### Fast Iteration (No Docker Rebuild)

1. Make your code changes
2. The running dev servers automatically reload
3. Test in browser at <http://localhost:5173>
4. Check API at <http://localhost:8000/docs>

### Backend-Only Testing

```bash
# Run the backend with hot-reload
make dev-backend

# Test API endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/settings

# Or use the Swagger UI
open http://localhost:8000/docs
```

### Frontend-Only Testing

```bash
# Run frontend with hot-reload
make dev-frontend

# Open browser
open http://localhost:5173
```

Changes to `.svelte` files, TypeScript, and CSS all hot-reload instantly.

## Docker (Production Testing)

Only use Docker when you need to test the production build:

```bash
# Build images
make build

# Start production stack
make docker-up

# View logs
make docker-logs

# Stop
make docker-down
```

### When to Rebuild Docker Images

You need to rebuild Docker images (`make build`) when:

- Adding new Python dependencies to `pyproject.toml`
- Adding new npm packages to `frontend/package.json`
- Modifying Dockerfile or docker-compose.yml
- Testing final production build before deployment

You do NOT need to rebuild when:

- Making code changes (use dev mode instead)
- Updating configuration
- Testing features

### Speed Tips

1. **Use `make build` not `make build-no-cache`** - incremental builds are much faster
2. **Build specific services**: `docker compose build backend` instead of all
3. **Use development mode for iteration** - instant changes vs minutes for rebuild

## Troubleshooting

### Qdrant Connection Error

```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Start it if not
make dev-infra
```

### Port Already in Use

```bash
# Find what's using the port
lsof -i :8000  # backend
lsof -i :5173  # frontend
lsof -i :6333  # qdrant

# Kill the process or change ports
```

### Import Errors

Make sure you're in the virtual environment:

```bash
source .venv/bin/activate  # bash/zsh
source .venv/bin/activate.fish  # fish

# Reinstall if needed
make install
```

### Frontend API Errors (CORS, 404)

The Vite dev server proxies `/api` to `localhost:8000`. Make sure:

1. Backend is running on port 8000
2. Check `frontend/vite.config.ts` if you need to change the proxy

### Slow Docker Builds

1. Make sure you're not using `--no-cache` unnecessarily
2. Docker layer caching should make subsequent builds faster
3. For development, just use `make dev` instead of Docker

## Project Structure

```
kgpt/
├── Makefile                 # Development commands (make help)
├── docker-compose.yml       # Production Docker stack
├── docker-compose.dev.yml   # Development infrastructure only
├── pyproject.toml           # Backend dependencies
├── uv.lock                  # Locked dependencies
├── .env.example             # Environment template
├── frontend/                # Svelte 5 frontend
│   ├── src/
│   │   ├── routes/          # Pages (chat, documents, cluster, settings)
│   │   └── lib/api.ts       # Backend API client
│   ├── vite.config.ts       # Dev server config (API proxy)
│   └── svelte.config.js     # Build config
└── src/kgpt/
    ├── api/                 # FastAPI application
    │   ├── main.py          # App entry point
    │   ├── schemas.py       # Request/response models
    │   └── routes/          # API endpoints
    ├── agents/              # LangGraph multi-agent system
    ├── ingestion/           # Document loaders (sitemap, github)
    ├── vectorstore/         # Qdrant integration
    ├── llm/                 # LLM providers (OpenAI, Anthropic, Ollama)
    └── db/                  # SQLite persistence
```

## Adding Dependencies

### Backend

```bash
# Add runtime dependency
uv add some-package

# Add dev dependency
uv add --dev some-tool

# Sync after changes
uv sync --dev
```

### Frontend

```bash
cd frontend
npm install some-package
```

## Available Make Commands

Run `make help` for the full list:

```
Quick Start (Development):
  make install        Install all dependencies (backend + frontend)
  make dev            Start full dev environment (recommended)
  make dev-infra      Start only infrastructure (Qdrant)

Individual Services:
  make dev-backend    Start backend with hot-reload
  make dev-frontend   Start frontend with hot-reload
  make stop           Stop all dev services

Code Quality:
  make lint           Run linters (ruff)
  make lint-fix       Run linters and auto-fix
  make format         Format code
  make test           Run tests
  make check          Run all checks (lint + test)

Docker (Production):
  make build          Build Docker images
  make docker-up      Start production Docker stack
  make docker-down    Stop production Docker stack
  make docker-logs    View Docker logs

Cleanup:
  make clean          Remove build artifacts and caches
  make clean-docker   Remove Docker volumes (WARNING: deletes data)
```
