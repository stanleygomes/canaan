# Portas customizadas para evitar conflito com outros servicos na maquina:
# Postgres: 5435
# Backend API: 8088
# Frontend: 5188

.PHONY: help install db-up db-down db-logs scrape-chaves scrape-vivareal scrape-zap scrape-olx scrape-imovelweb scrape-quintoandar scrape-mercadolivre scrape-loft scrape-rotina scrape-multi scrape-objetiva scrape-alianca scrape-delta scrape-arantes scrape-ivan scrape-lider scrape-uberlandia-imobiliarias scrape-all backend frontend

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
	@echo "  make scrape-imovelweb  - Executa o scraper do Imovelweb"
	@echo "  make scrape-quintoandar - Executa o scraper do QuintoAndar"
	@echo "  make scrape-mercadolivre - Executa o scraper do Mercado Livre Imóveis"
	@echo "  make scrape-loft       - Executa o scraper da Loft"
	@echo "  make scrape-uberlandia-imobiliarias - Executa scrapers das imobiliarias de Uberlandia"
	@echo "  make scrape-rotina      - Executa o scraper da Rotina Imóveis"
	@echo "  make scrape-multi       - Executa o scraper da Multi Imóveis"
	@echo "  make scrape-objetiva    - Executa o scraper da Objetiva Imóveis"
	@echo "  make scrape-alianca     - Executa o scraper da Aliança Imóveis"
	@echo "  make scrape-delta       - Executa o scraper da Delta Imóveis"
	@echo "  make scrape-arantes     - Executa o scraper da Arantes Imóveis"
	@echo "  make scrape-ivan        - Executa o scraper da Ivan Imóveis"
	@echo "  make scrape-lider       - Executa o scraper da Líder Imóveis"
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

scrape-imovelweb:
	uv run python -m src.scrapers.imovelweb

scrape-quintoandar:
	uv run python -m src.scrapers.quintoandar

scrape-mercadolivre:
	uv run python -m src.scrapers.mercadolivre

scrape-loft:
	uv run python -m src.scrapers.loft

scrape-uberlandia-imobiliarias:
	uv run python -m src.scrapers.imobiliarias_uberlandia

scrape-rotina:
	uv run python -m src.scrapers.imobiliarias_uberlandia rotina

scrape-multi:
	uv run python -m src.scrapers.imobiliarias_uberlandia multi

scrape-objetiva:
	uv run python -m src.scrapers.imobiliarias_uberlandia objetiva

scrape-alianca:
	uv run python -m src.scrapers.imobiliarias_uberlandia alianca

scrape-delta:
	uv run python -m src.scrapers.imobiliarias_uberlandia delta

scrape-arantes:
	uv run python -m src.scrapers.imobiliarias_uberlandia arantes

scrape-ivan:
	uv run python -m src.scrapers.imobiliarias_uberlandia ivan

scrape-lider:
	uv run python -m src.scrapers.imobiliarias_uberlandia lider

scrape-all: scrape-chaves scrape-vivareal scrape-zap scrape-olx scrape-imovelweb scrape-quintoandar scrape-mercadolivre scrape-loft

backend:
	uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8088

frontend:
	cd frontend && npm run dev -- --port 5188 --host 0.0.0.0
