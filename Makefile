# Makefile for Modular Agentic Monolith
# Python 3.12 + FastAPI + LangGraph

.PHONY: help install dev-install clean test test-unit test-e2e lint format typecheck quality run dev docker-up docker-down docker-restart migrate db-shell redis-cli logs smoke-test coverage pre-commit

# Default target
.DEFAULT_GOAL := help

# Color output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ Help

help: ## Display this help message
	@echo "$(BLUE)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Installation

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	uv sync --no-dev

dev-install: ## Install all dependencies (including dev)
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	uv sync
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

clean: ## Clean cache files and build artifacts
	@echo "$(BLUE)Cleaning cache files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	@echo "$(GREEN)✓ Cleaned$(NC)"

##@ Testing

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	uv run pytest -v

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	uv run pytest tests/unit -v

test-e2e: ## Run E2E tests (requires running server)
	@echo "$(BLUE)Running E2E tests...$(NC)"
	uv run python tests/e2e_full_cycle.py

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	uv run pytest-watch

coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/index.html$(NC)"

smoke-test: dev docker-up ## Run smoke test against local server
	@echo "$(BLUE)Waiting for server to start...$(NC)"
	@sleep 5
	@echo "$(BLUE)Running smoke test...$(NC)"
	curl -f http://localhost:8000/docs || (echo "$(RED)✗ Server not responding$(NC)" && exit 1)
	@echo "$(GREEN)✓ Smoke test passed$(NC)"

##@ Code Quality

lint: ## Run linter (Ruff)
	@echo "$(BLUE)Running Ruff linter...$(NC)"
	uv run ruff check src tests

lint-fix: ## Run linter with auto-fix
	@echo "$(BLUE)Running Ruff with auto-fix...$(NC)"
	uv run ruff check --fix src tests

format: ## Format code with Ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	uv run ruff format src tests

format-check: ## Check code formatting (CI)
	@echo "$(BLUE)Checking code format...$(NC)"
	uv run ruff format --check src tests

typecheck: ## Run type checker (Mypy)
	@echo "$(BLUE)Running Mypy type checker...$(NC)"
	uv run mypy src

quality: lint typecheck test-unit ## Run all quality checks (lint + typecheck + tests)
	@echo "$(GREEN)✓ All quality checks passed$(NC)"

pre-commit: format-check lint typecheck test-unit ## Pre-commit checks (run before committing)
	@echo "$(GREEN)✓ Pre-commit checks passed - safe to commit$(NC)"

##@ Development

dev: ## Run development server with auto-reload
	@echo "$(BLUE)Starting development server...$(NC)"
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run: ## Run production server
	@echo "$(BLUE)Starting production server...$(NC)"
	uv run python -m src.main

run-bg: ## Run server in background (logs to server.log)
	@echo "$(BLUE)Starting server in background...$(NC)"
	uv run python -m src.main > server.log 2>&1 &
	@echo "$(GREEN)✓ Server running (PID: $$!)$(NC)"
	@echo "$(YELLOW)Logs: tail -f server.log$(NC)"

stop: ## Stop background server
	@echo "$(BLUE)Stopping server...$(NC)"
	@-pkill -f "python -m src.main" 2>/dev/null || true
	@echo "$(GREEN)✓ Server stopped$(NC)"

logs: ## Tail development logs
	tail -f server.log

##@ Docker & Infrastructure

docker-up: ## Start all infrastructure services (Postgres, Redis, LangFuse)
	@echo "$(BLUE)Starting Docker services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "$(YELLOW)Postgres: localhost:5432$(NC)"
	@echo "$(YELLOW)Redis: localhost:6379$(NC)"
	@echo "$(YELLOW)LangFuse: http://localhost:3000$(NC)"

docker-down: ## Stop all infrastructure services
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	docker-compose down

docker-restart: docker-down docker-up ## Restart all infrastructure services

docker-logs: ## View Docker service logs
	docker-compose logs -f

docker-ps: ## Show running Docker containers
	docker-compose ps

docker-clean: ## Remove all Docker volumes (WARNING: deletes data)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "$(GREEN)✓ Volumes removed$(NC)"; \
	fi

##@ Database

migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	uv run alembic upgrade head
	@echo "$(GREEN)✓ Migrations applied$(NC)"

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	@echo "$(BLUE)Creating migration: $(MSG)$(NC)"
	uv run alembic revision --autogenerate -m "$(MSG)"

migrate-downgrade: ## Rollback last migration
	@echo "$(BLUE)Rolling back last migration...$(NC)"
	uv run alembic downgrade -1

migrate-history: ## Show migration history
	uv run alembic history

db-shell: ## Open PostgreSQL shell
	docker exec -it $$(docker-compose ps -q postgres) psql -U user -d interview_db

db-reset: docker-down ## Reset database (WARNING: deletes all data)
	@echo "$(RED)Resetting database...$(NC)"
	docker volume rm interview_postgres_data 2>/dev/null || true
	$(MAKE) docker-up
	sleep 3
	$(MAKE) migrate
	@echo "$(GREEN)✓ Database reset complete$(NC)"

##@ Redis

redis-cli: ## Open Redis CLI
	docker exec -it $$(docker-compose ps -q redis) redis-cli

redis-flush: ## Flush all Redis data (WARNING: deletes all cached data)
	@echo "$(RED)Flushing Redis...$(NC)"
	docker exec -it $$(docker-compose ps -q redis) redis-cli FLUSHALL
	@echo "$(GREEN)✓ Redis flushed$(NC)"

redis-info: ## Show Redis info
	docker exec -it $$(docker-compose ps -q redis) redis-cli INFO

##@ API Testing

api-health: ## Check API health
	@curl -f http://localhost:8000/docs -o /dev/null -s && \
		echo "$(GREEN)✓ API is healthy$(NC)" || \
		echo "$(RED)✗ API is not responding$(NC)"

api-test-chat: ## Send test chat message
	@echo "$(BLUE)Sending test message...$(NC)"
	@curl -X POST http://localhost:8000/v1/chat/message \
		-H "Content-Type: application/json" \
		-d '{"user_id": "test_user", "message": "Hello, create a plan to learn Python", "thread_id": "test_thread"}' \
		| python -m json.tool

api-get-state: ## Get thread state (usage: make api-get-state THREAD=test_thread)
	@curl http://localhost:8000/v1/chat/debug/state/$(THREAD) | python -m json.tool

##@ Utilities

shell: ## Open Python shell with app context
	uv run python

repl: ## Open IPython REPL with app context loaded
	uv run ipython -i -c "from src.main import app; from src.settings import settings; print('App and settings loaded')"

env-check: ## Verify environment variables
	@echo "$(BLUE)Checking environment...$(NC)"
	@echo "DATABASE_URL: $${DATABASE_URL:-$(RED)NOT SET$(NC)}"
	@echo "REDIS_URL: $${REDIS_URL:-$(RED)NOT SET$(NC)}"
	@echo "OPENAI_API_KEY: $${OPENAI_API_KEY:+$(GREEN)SET$(NC)}$${OPENAI_API_KEY:-$(RED)NOT SET$(NC)}"
	@echo "ENVIRONMENT: $${ENVIRONMENT:-local}"

deps-update: ## Update dependencies to latest versions
	@echo "$(BLUE)Updating dependencies...$(NC)"
	uv sync --upgrade

deps-list: ## List installed dependencies
	uv pip list

##@ Workflows

setup: dev-install docker-up migrate ## Complete initial setup (install + docker + migrate)
	@echo "$(GREEN)✓ Setup complete! Ready to develop.$(NC)"
	@echo "$(YELLOW)Run 'make dev' to start the server$(NC)"

reset: docker-clean setup ## Complete reset (clean + setup)
	@echo "$(GREEN)✓ Project reset complete$(NC)"

ci: clean quality coverage ## CI pipeline (clean + quality + coverage)
	@echo "$(GREEN)✓ CI checks passed$(NC)"

prod-check: ## Pre-production checklist
	@echo "$(BLUE)Running pre-production checks...$(NC)"
	@make format-check
	@make lint
	@make typecheck
	@make test
	@echo "$(GREEN)✓ All pre-production checks passed$(NC)"
	@echo "$(YELLOW)Deployment checklist:$(NC)"
	@echo "  [ ] Environment variables configured"
	@echo "  [ ] Database migrations applied"
	@echo "  [ ] Redis configured"
	@echo "  [ ] Secrets rotated"
	@echo "  [ ] Monitoring configured"
	@echo "  [ ] Backup strategy in place"

##@ Documentation

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Documentation available at:$(NC)"
	@echo "  $(YELLOW)API Docs: http://localhost:8000/docs$(NC)"
	@echo "  $(YELLOW)README: README.md$(NC)"
		@echo "  $(YELLOW)Architecture: docs/architecture/DECISIONS.md$(NC)"

readme: ## Display README
	@cat README.md

todo: ## Display TODO list
	@cat TODO.md 2>/dev/null || echo "$(YELLOW)No TODO.md found$(NC)"

##@ Git Helpers

git-clean-branches: ## Clean up merged git branches
	@echo "$(BLUE)Cleaning merged branches...$(NC)"
	git branch --merged | grep -v "\*" | grep -v "main" | grep -v "master" | xargs -n 1 git branch -d 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(NC)"

git-status: ## Show git status with helpful info
	@echo "$(BLUE)Git Status:$(NC)"
	@git status -sb
	@echo ""
	@echo "$(BLUE)Untracked files:$(NC)"
	@git ls-files --others --exclude-standard | head -10

##@ Performance

benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running benchmarks...$(NC)"
	@echo "$(YELLOW)Not implemented yet$(NC)"

profile: ## Profile the application
	@echo "$(BLUE)Profiling application...$(NC)"
	uv run python -m cProfile -o profile.stats -m src.main
	@echo "$(GREEN)Profile saved to profile.stats$(NC)"
	@echo "$(YELLOW)Analyze with: uv run python -m pstats profile.stats$(NC)"
