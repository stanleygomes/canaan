# Portas customizadas para evitar conflito com outros servicos na maquina:
# Postgres: 5435
# Backend API: 8088
# Frontend: 5188

.PHONY: help install db-up db-down db-logs scrape sync-filters api cron frontend

help:
	@echo "Comandos disponiveis:"
	@echo "  make install           - Instala dependencias com uv e browsers do Playwright"
	@echo "  make db-up             - Sobe o banco PostgreSQL na porta 5435 via Docker"
	@echo "  make db-down           - Para o container do PostgreSQL"
	@echo "  make db-logs           - Acompanha os logs do banco"
	@echo "  make scrape             - Busca todos os sources usando config/search_filters.toml"
	@echo "  make scrape SOURCE=olx - Busca somente um source específico"
	@echo "  make sync-filters      - Sincroniza os filtros do TOML com o PostgreSQL"
	@echo "  make api               - Inicia a API FastAPI na porta 8088"
	@echo "  make cron              - Inicia o processo de execução agendada"
	@echo "  make frontend          - Inicia o frontend React na porta 5188 (futuro)"

install:
	uv sync
	uv run playwright install chromium

db-up:
	docker compose up -d

db-down:
	docker compose down

db-logs:
	docker compose logs -f postgres

scrape:
	uv run python -m src.search

sync-filters:
	uv run python -m src.sync_filters

api:
	uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8088

cron:
	uv run python -m src.cron

frontend:
	cd frontend && npm run dev -- --port 5188 --host 0.0.0.0
