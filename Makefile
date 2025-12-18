# kGPT Makefile
# Run `make help` to see all available commands

.PHONY: help install dev dev-infra dev-backend dev-frontend stop clean lint test build docker-up docker-down check-venv check-prerequisites check-docker

# Default target
help:
	@echo "kGPT Development Commands"
	@echo ""
	@echo "Quick Start (Development):"
	@echo "  make install        Install all dependencies (backend + frontend)"
	@echo "  make dev            Start full dev environment with Kafka (recommended)"
	@echo "  make dev-infra      Start only infrastructure (Qdrant)"
	@echo "  make dev-infra-kafka  Start infrastructure with Kafka demo cluster"
	@echo ""
	@echo "Individual Services:"
	@echo "  make dev-backend    Start backend with hot-reload"
	@echo "  make dev-frontend   Start frontend with hot-reload"
	@echo "  make stop           Stop all dev services"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           Run linters (ruff)"
	@echo "  make lint-fix       Run linters and auto-fix"
	@echo "  make format         Format code"
	@echo "  make test           Run tests"
	@echo "  make check          Run all checks (lint + test)"
	@echo ""
	@echo "Docker (Production):"
	@echo "  make build          Build Docker images"
	@echo "  make docker-up      Start production Docker stack"
	@echo "  make docker-down    Stop production Docker stack"
	@echo "  make docker-logs    View Docker logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          Remove build artifacts and caches"
	@echo "  make clean-docker   Remove Docker volumes (WARNING: deletes data)"
	@echo ""
	@echo "Prerequisites:"
	@echo "  Python 3.11+, Node.js 20+, uv, Docker, Make"
	@echo "  See DEVELOPMENT.md for installation instructions"

# ============================================================================
# PREREQUISITE CHECKS
# ============================================================================

# Check all prerequisites before installation
check-prerequisites:
	@echo "Checking prerequisites..."
	@# Check Python
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "❌ Python 3 not found. Please install Python 3.11 or 3.12."; \
		echo "   Visit: https://www.python.org/downloads/"; \
		exit 1; \
	fi
	@PYTHON_VERSION=$$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))'); \
	PYTHON_MAJOR=$$(echo $$PYTHON_VERSION | cut -d. -f1); \
	PYTHON_MINOR=$$(echo $$PYTHON_VERSION | cut -d. -f2); \
	if [ $$PYTHON_MAJOR -lt 3 ] || [ $$PYTHON_MAJOR -eq 3 -a $$PYTHON_MINOR -lt 11 ]; then \
		echo "❌ Python 3.11+ required. Found Python $$PYTHON_VERSION"; \
		echo "   Visit: https://www.python.org/downloads/"; \
		exit 1; \
	fi
	@# Check Node.js
	@if ! command -v node >/dev/null 2>&1; then \
		echo "❌ Node.js not found. Please install Node.js 20 or higher."; \
		echo "   Visit: https://nodejs.org/"; \
		exit 1; \
	fi
	@NODE_VERSION=$$(node -v | sed 's/v//'); \
	NODE_MAJOR=$$(echo $$NODE_VERSION | cut -d. -f1); \
	if [ $$NODE_MAJOR -lt 20 ]; then \
		echo "❌ Node.js 20+ required. Found Node.js $$NODE_VERSION"; \
		echo "   Visit: https://nodejs.org/"; \
		exit 1; \
	fi
	@# Check npm
	@if ! command -v npm >/dev/null 2>&1; then \
		echo "❌ npm not found. npm should come with Node.js."; \
		exit 1; \
	fi
	@# Check uv
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "❌ uv not found. Please install uv:"; \
		echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		echo "   Then restart your terminal or run: source \$$HOME/.cargo/env"; \
		echo "   Or visit: https://docs.astral.sh/uv/"; \
		exit 1; \
	fi
	@# Check Docker (warn but don't fail - needed for infrastructure)
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "⚠️  Docker not found. Infrastructure commands will fail."; \
		echo "   Install: https://docs.docker.com/get-docker/"; \
	elif ! docker info >/dev/null 2>&1; then \
		echo "⚠️  Docker is installed but not running. Start Docker Desktop."; \
	fi
	@echo "✓ All prerequisites met"

# Check Docker is available and running
check-docker:
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "❌ Docker not found. Please install Docker:"; \
		echo "   https://docs.docker.com/get-docker/"; \
		exit 1; \
	fi
	@if ! docker info >/dev/null 2>&1; then \
		echo "❌ Docker is not running. Please start Docker Desktop."; \
		exit 1; \
	fi

# ============================================================================
# INSTALLATION
# ============================================================================

install: check-prerequisites install-backend install-frontend
	@echo ""
	@echo "✓ All dependencies installed"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Copy .env.example to .env (optional - settings can be configured in UI)"
	@echo "  2. Run 'make dev' to start the development environment"

install-backend:
	@echo "Installing backend dependencies..."
	@uv sync --dev || (echo "❌ Backend installation failed. Make sure uv is installed: https://docs.astral.sh/uv/" && exit 1)
	@echo "✓ Backend ready"

install-frontend:
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install || (echo "❌ Frontend installation failed. Make sure Node.js 20+ is installed: https://nodejs.org/" && exit 1)
	@echo "✓ Frontend ready"

# ============================================================================
# DEVELOPMENT (Fast iteration with hot-reload)
# ============================================================================

# Start everything for development (with Kafka demo cluster)
dev: check-venv dev-infra-kafka
	@echo ""
	@echo "Starting development servers..."
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Kafka:    localhost:9094"
	@echo ""
	@# Run backend and frontend in parallel
	@# --reload-dir src/ ensures source changes are detected
	@trap 'kill 0' INT; \
		(cd $(CURDIR) && .venv/bin/python -m uvicorn kgpt.api.main:app --reload --reload-dir src/ --port 8000) & \
		(cd $(CURDIR)/frontend && npm run dev) & \
		wait

# Check that venv exists and has uvicorn
check-venv:
	@if [ ! -f .venv/bin/python ]; then \
		echo "❌ Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@if ! .venv/bin/python -c "import uvicorn" 2>/dev/null; then \
		echo "❌ Dependencies not installed. Run 'make install' first."; \
		exit 1; \
	fi

# Start only infrastructure (Qdrant)
dev-infra: check-docker
	@echo "Starting infrastructure (Qdrant)..."
	docker compose -f docker-compose.dev.yml up -d qdrant
	@echo "Waiting for Qdrant to be ready..."
	@until docker compose -f docker-compose.dev.yml exec -T qdrant bash -c 'exec 3<>/dev/tcp/localhost/6333' 2>/dev/null; do \
		sleep 1; \
	done
	@echo "✓ Qdrant ready at http://localhost:6333"

# Start infrastructure + Kafka demo
dev-infra-kafka: check-docker
	@echo "Starting infrastructure with Kafka..."
	docker compose -f docker-compose.dev.yml --profile kafka up -d
	@echo "✓ Qdrant ready at http://localhost:6333"
	@echo "✓ Kafka ready at localhost:9094"

# Start just the backend
dev-backend: check-venv
	.venv/bin/python -m uvicorn kgpt.api.main:app --reload --reload-dir src/ --port 8000

# Start just the frontend
dev-frontend:
	cd frontend && npm run dev

# Stop all dev services
stop: check-docker
	docker compose -f docker-compose.dev.yml down
	@echo "✓ Infrastructure stopped"
	@echo "Note: To stop backend/frontend, use Ctrl+C in their terminals"

# ============================================================================
# CODE QUALITY
# ============================================================================

lint:
	.venv/bin/ruff check src/

lint-fix:
	.venv/bin/ruff check src/ --fix

format:
	.venv/bin/ruff format src/

test:
	.venv/bin/pytest

test-cov:
	.venv/bin/pytest --cov=kgpt --cov-report=term-missing

check: lint test
	@echo "✓ All checks passed"

# ============================================================================
# DOCKER (Production builds)
# ============================================================================

build: check-docker
	docker compose build

build-no-cache: check-docker
	docker compose build --no-cache

docker-up: check-docker
	docker compose up -d
	@echo ""
	@echo "✓ kGPT is running!"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API:      http://localhost:8000"
	@echo "  Docs:     http://localhost:8000/docs"

docker-down: check-docker
	docker compose down

docker-logs: check-docker
	docker compose logs -f

docker-logs-backend: check-docker
	docker compose logs -f backend

# ============================================================================
# CLEANUP
# ============================================================================

clean:
	rm -rf .ruff_cache
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf __pycache__
	rm -rf src/**/__pycache__
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf frontend/.svelte-kit
	rm -rf frontend/build
	@echo "✓ Cleaned build artifacts"

clean-docker: check-docker
	@echo "WARNING: This will delete all Docker volumes including indexed documents!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	docker compose down -v
	docker compose -f docker-compose.dev.yml down -v
	@echo "✓ Docker volumes removed"
