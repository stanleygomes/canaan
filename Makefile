# Portas customizadas para evitar conflito com outros servicos na maquina:
# Postgres: 5435
# Backend API: 8088
# Frontend: 5188

.PHONY: help install db-up db-down db-logs scrape-chaves scrape-vivareal scrape-zap scrape-olx scrape-all backend frontend

help:
	@echo "Comandos disponiveis:"
	@echo "  make install           - Instala dependencias com uv e browsers do Playwright"
	@echo "  make db-up             - Sobe o banco PostgreSQL na porta 5435 via Docker"
	@echo "  make db-down           - Para o container do PostgreSQL"
	@echo "  make db-logs           - Acompanha os logs do banco"
	@echo "  make scrape-chaves     - Executa o scraper do Chaves na Mao"
	@echo "  make scrape-vivareal   - Executa o scraper do Viva Real"
	@echo "  make scrape-zap        - Executa o scraper do ZAP Imoveis"
	@echo "  make scrape-olx        - Executa o scraper da OLX"
	@echo "  make scrape-all        - Executa todos os scrapers sequencialmente"
	@echo "  make backend           - Inicia o backend FastAPI na porta 8088 (futuro)"
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

scrape-chaves:
	uv run python -m src.scrapers.chavesnamao

scrape-vivareal:
	uv run python -m src.scrapers.vivareal

scrape-zap:
	uv run python -m src.scrapers.zapimoveis

scrape-olx:
	uv run python -m src.scrapers.olx

scrape-all: scrape-chaves scrape-vivareal scrape-zap scrape-olx

backend:
	uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8088

frontend:
	cd frontend && npm run dev -- --port 5188 --host 0.0.0.0
