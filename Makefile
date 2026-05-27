# TICDSS one-shot Makefile — works in WSL / Linux / macOS / Git Bash.
# For Windows-native PowerShell use `scripts/setup.ps1` instead.

.PHONY: help setup install up down logs migrate seed dev test test-live clean

API_DIR := apps/api
WEB_DIR := apps/web
ASR_DIR := apps/asr

help:
	@echo "TICDSS development commands:"
	@echo "  make setup       Install all deps + start infra + migrate + seed (first-time)"
	@echo "  make install     pnpm + uv install (deps only)"
	@echo "  make up          docker compose up -d (postgres + langfuse)"
	@echo "  make down        docker compose down"
	@echo "  make logs        Tail docker-compose logs"
	@echo "  make migrate     Run Alembic upgrade head"
	@echo "  make seed        Seed users, cases, bibliotheke"
	@echo "  make dev         Print instructions for running all 3 services"
	@echo "  make test        Run backend pytest (excludes -m live)"
	@echo "  make test-live   Run live LLM tests (requires API keys, ~\$0.10/run)"
	@echo "  make clean       Remove docker volumes (DESTRUCTIVE — DB wiped)"

setup: install up
	@echo "Waiting for Postgres to be healthy..."
	@sleep 8
	$(MAKE) migrate
	$(MAKE) seed
	@echo ""
	@echo "✓ Setup complete. Now run:"
	@echo "  Terminal A: cd $(API_DIR) && uv run uvicorn src.main:app --reload --port 8001"
	@echo "  Terminal B: pnpm dev:web"
	@echo "  Terminal C: cd $(ASR_DIR) && uv run uvicorn src.main:app --reload --port 8002"
	@echo "Then open http://localhost:3000 — login as P001 / demo1234"

install:
	cd $(API_DIR) && uv sync
	cd $(ASR_DIR) && uv sync
	pnpm install

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	cd $(API_DIR) && uv run alembic upgrade head

seed:
	cd $(API_DIR) && uv run python ../../scripts/seed_users.py
	cd $(API_DIR) && uv run python ../../scripts/import_cases.py
	cd $(API_DIR) && uv run python scripts/seed_bibliotheke.py || echo "(bibliotheke seed skipped — runs slowly first time)"

dev:
	@echo "Run these in three separate terminals:"
	@echo "  cd $(API_DIR) && uv run uvicorn src.main:app --reload --port 8001"
	@echo "  pnpm dev:web"
	@echo "  cd $(ASR_DIR) && ASR_STUB_MODE=true uv run uvicorn src.main:app --reload --port 8002"

test:
	cd $(API_DIR) && uv run pytest -v -m "not live"

test-live:
	cd $(API_DIR) && uv run pytest -v -m live

clean:
	docker compose down -v
	@echo "✗ docker volumes removed — all session data is gone."
