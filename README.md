# Canaan

Sistema automatizado de busca e extração de dados (web scraping) de portais imobiliários (ex: OLX, Zap Imóveis, Chaves na Mão, entre outros).

---

## 📌 Visão Geral

O objetivo do projeto é monitorar ofertas de imóveis na web de forma automatizada, coletando detalhes aprofundados de cada anúncio e armazenando-os de forma estruturada para consulta e análise.

Os imóveis são persistidos na tabela PostgreSQL `properties`. O contrato possui campos tipados para os dados comuns e campos `JSONB` para endereço, anunciante, geolocalização, comodidades, imagens e o payload original. A chave única `(portal, url)` permite atualizar anúncios já conhecidos sem criar duplicatas.

## 🛠️ Subir o projeto localmente

### Pré-requisitos

- Python 3.14 ou superior;
- [`uv`](https://docs.astral.sh/uv/);
- Node.js e npm;
- Docker e Docker Compose.

### Subida rápida

Na raiz do projeto, execute:

```bash
make setup
make dev
```

O `make setup` cria os arquivos `.env` quando necessário, instala as dependências, inicia o PostgreSQL, sincroniza os filtros e prepara o frontend. O `make dev` sobe API, cron e frontend juntos.

URLs locais:

- Frontend: `http://localhost:5188`;
- API: `http://localhost:8088`;
- OpenAPI: `http://localhost:8088/docs`.

Para subir somente a API:

```bash
make api
```

O `.env` da raiz configura banco, API, CORS, cron e geocoding. O padrão do cron é uma execução diária às 02:00 no fuso `America/Sao_Paulo`. O `frontend/.env` configura a URL da API. Para liberar mais origens, informe-as em `CORS_ORIGINS` separadas por vírgula.

Para executar uma coleta manual diretamente:

```bash
make scrape
```

Verifique a API em `http://localhost:8088/health` e a documentação OpenAPI em `http://localhost:8088/docs`.

Para parar o banco local:

```bash
make db-down
```

---

## 🔎 Metodologia de coleta

Cada scraper acessa uma URL de busca configurada usando Playwright em navegador headless, percorre as páginas definidas, identifica os anúncios disponíveis e extrai seus dados visíveis — como título, preço, área, quartos, vagas, localização, imagens e descrição — usando seletores específicos de cada portal e funções de normalização para valores monetários e numéricos; ao final, os registros são padronizados no mesmo formato e salvos em arquivos JSON para posterior consulta, análise ou persistência em banco de dados.

---

## 🚀 Funcionalidades

### Busca unificada por filtros

Os filtros da busca ficam em [`config/search_filters.toml`](config/search_filters.toml). Para consultar todos os sources configurados, execute `make scrape`; para consultar apenas uma fonte, use `make scrape SOURCE=olx` ou `make scrape SOURCE=rotina`. O sistema coleta os anúncios, aplica os filtros comuns, remove duplicidades por URL e salva o resultado consolidado em `imoveis_filtrados.json`.

Os filtros são armazenados na tabela PostgreSQL `search_filters` e a configuração `default` é a fonte usada pelo scrape. Depois de alterar o TOML, use `make sync-filters`; se o PostgreSQL estiver indisponível, o TOML é usado como fallback.

Antes da coleta, suba o banco com `make db-up`. A conexão pode ser sobrescrita pela variável `DATABASE_URL`; por padrão, usa o PostgreSQL definido no `docker-compose.yml`.

### API e execução agendada

Copie `.env.example` para `.env` e ajuste `SCRAPE_CRON` conforme necessário. Inicie a API com `make api` e o processo agendador separado com `make cron`.

- `POST /api/v1/scrape-runs` inicia uma coleta manual. Corpo opcional: `{ "source": "olx" }`.
- `GET /api/v1/scrape-runs/{run_id}` consulta o estado da coleta.
- `GET /health` verifica se a API está disponível.

API e cron chamam o mesmo serviço de aplicação e compartilham um lock advisory do PostgreSQL, evitando duas coletas simultâneas.

Durante a coleta, os endereços sem coordenadas são enviados ao geocoder configurado em `GEOCODING_URL`. O resultado é salvo em `geo` e também em `data/geocode_cache.json`. O padrão usa Nominatim com limite conservador de requisições; para produção ou volume maior, configure um provedor próprio/comercial compatível com sua demanda. O mapa deverá exibir a atribuição exigida pelo provedor.

### 1. Coleta e Scraping Automatizado
- **Parâmetros pré-configurados**: filtros de busca definidos (localização, faixa de preço, tipo de imóvel, número de quartos, etc.).
- **Execução agendada**: rotinas diárias executadas em horários definidos para verificar novos imóveis e atualizações.
- **Browser Headless**: navegação automatizada utilizando navegador em modo headless para lidar com páginas dinâmicas e proteções básicas.
- **Extração detalhada**: acesso a cada página de anúncio para captura de todas as informações relevantes (preço, metragem, condomínio, IPTU, endereço, fotos, descrição, etc.).

### 2. Armazenamento
- Persistência dos dados coletados em banco de dados **PostgreSQL**.

---

## 🔮 Próximos Passos (Roadmap)

- [ ] **Interface Gráfica (UI)**:
  - Gerenciamento e configuração visual dos parâmetros de busca.
  - Painel de listagem, filtros e visualização dos imóveis capturados.
  - Monitoramento e status das execuções dos bots.
