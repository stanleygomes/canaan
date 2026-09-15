# AGENTS.md

## Overview

O Canaan coleta anúncios imobiliários em portais, normaliza os dados, geocodifica endereços, persiste os imóveis no PostgreSQL e expõe uma API FastAPI para consulta e disparo de novas coletas. O frontend é uma aplicação React/TypeScript criada com Vite e consumirá a API; as telas ainda estão em construção.

## Stack

| Área | Tecnologia |
| --- | --- |
| Scraping | Python, Playwright, Playwright Stealth |
| API | FastAPI, Uvicorn |
| Persistência | PostgreSQL, psycopg |
| Agendamento | APScheduler |
| Frontend | React, TypeScript, Vite |
| Dados no frontend | TanStack Query |
| Roteamento | React Router |
| Estilo | Tailwind CSS |
| Mapas | MapLibre GL |

## Commands

| Command | Description |
| --- | --- |
| `make install` | Instala dependências Python e o Chromium do Playwright. |
| `make db-up` | Inicia o PostgreSQL via Docker. |
| `make db-down` | Para o PostgreSQL. |
| `make db-logs` | Acompanha os logs do PostgreSQL. |
| `make scrape` | Executa a coleta de todos os sources configurados. |
| `make scrape SOURCE=olx` | Executa a coleta de um source específico. |
| `make sync-filters` | Sincroniza os filtros do TOML com o PostgreSQL. |
| `make api` | Inicia a API FastAPI na porta 8088. |
| `make cron` | Inicia o processo de execução agendada. |
| `make frontend` | Inicia o frontend Vite na porta 5188. |
| `cd frontend && npm run typecheck` | Valida os tipos TypeScript. |
| `cd frontend && npm run build` | Gera o build de produção do frontend. |

## Architecture

O projeto é um monólito modular com processos separados para API, cron e frontend.

| Module | Responsibility |
| --- | --- |
| `src/scrapers/` | Scrapers específicos e abstrações comuns dos portais. |
| `src/search.py` | Orquestra fontes, filtros carregados do banco, deduplicação, geocoding e persistência. |
| `src/geocoding.py` | Enriquece os imóveis com latitude e longitude e mantém cache local. |
| `src/db.py` | Schema PostgreSQL, filtros, upsert e consultas de imóveis. |
| `src/sync_filters.py` | Sincroniza a configuração TOML com a tabela de filtros. |
| `src/application/` | Serviços de aplicação compartilhados pela API e pelo cron. |
| `src/api/` | Rotas HTTP, contratos e modelos de resposta. |
| `src/cron.py` | Worker que agenda a execução do serviço de aplicação. |
| `frontend/src/lib/api/` | Cliente HTTP e tipos dos contratos consumidos pelo frontend. |
| `frontend/src/app/` | Providers e composição da aplicação React. |
| `frontend/src/features/` | Futuras funcionalidades de imóveis, mapa e execuções. |

## Module Routing

- Scraping ou extração específica de um portal → `src/scrapers/`.
- Regras de filtro, deduplicação e pipeline → `src/search.py`.
- Persistência ou consultas SQL → `src/db.py`.
- Coordenação de uma execução manual/agendada → `src/application/`.
- Rota ou contrato HTTP → `src/api/`.
- Integração com endpoint no frontend → `frontend/src/lib/api/`.
- Componente visual ou fluxo de produto → `frontend/src/features/`.

## Dependency Direction

```text
frontend ──HTTP──> src/api ──> src/application ──> src/search
                                      │                 ├──> src/scrapers
                                      │                 ├──> src/geocoding
                                      │                 └──> src/db ──> PostgreSQL
src/cron ────────────────────────────┘
```

O frontend não acessa o banco diretamente. API e cron devem reutilizar o serviço de aplicação; não duplicar o pipeline de scraping nos adaptadores de entrada.

## Frontend Design Direction

O frontend deve seguir uma linguagem visual inspirada no Airbnb Design Language System (DLS), adaptada ao contexto de busca imobiliária. A referência é de princípios e composição, não de cópia de marca, logo, textos ou identidade proprietária.

### Visual language

- Usar **minimalismo editorial de marketplace premium**: o imóvel e sua fotografia são o foco principal.
- Priorizar fundos claros, bastante espaço em branco e hierarquia tipográfica evidente.
- Usar cards limpos, com bordas arredondadas moderadas, separação por espaço e bordas sutis; evitar sombras pesadas e excesso de contêineres.
- Usar imagens em destaque, com proporção consistente e `object-fit: cover`; não distorcer fotos.
- Reservar a cor de destaque para ações, seleção, preço e estados importantes. Não transformar toda a interface em uma superfície colorida.
- Manter textos auxiliares menores e neutros; preço, localização e atributos essenciais devem ter leitura imediata.
- Evitar gradientes decorativos, glassmorphism, excesso de ícones e ornamentos que disputem atenção com as fotos.

### Property cards and map

- Cada card deve comunicar rapidamente: imagem, localização, tipo, preço, quartos, área e origem do anúncio.
- O card inteiro deve ter área de interação clara e estados visíveis de hover, foco e selecionado.
- A lista e o mapa devem permanecer sincronizados: selecionar um card destaca o marcador correspondente e selecionar um marcador destaca o card.
- O mapa deve suportar carregamento incremental e não deve renderizar propriedades sem coordenadas como se tivessem localização precisa.
- Exibir a precisão da localização quando ela for aproximada; não revelar endereço exato quando os dados não tiverem essa precisão.
- Manter atribuição e requisitos do provedor de mapas visíveis.

### Interaction and accessibility

- Filtros devem ser fáceis de encontrar, limpar e compartilhar por URL.
- Estados de carregamento, vazio, erro e atualização devem ser explícitos.
- Toda interação deve funcionar com teclado e ter foco visível.
- Contraste, tamanho de texto, `alt` de imagens e labels de campos são obrigatórios.
- O layout deve funcionar primeiro em telas menores e adaptar a composição lista/mapa em telas maiores.

## Anti-Patterns

- O frontend não deve acessar PostgreSQL ou arquivos JSON diretamente.
- Não criar chamadas `fetch` espalhadas em componentes; centralizar em `frontend/src/lib/api/` e usar TanStack Query para estado remoto.
- Não colocar regras de scraping dentro da API ou do cron.
- Não adicionar uma tela com dados mockados sem deixar explícita a origem e o contrato esperado.
- Não usar coordenadas sem indicar sua precisão.
- Não usar a marca Airbnb como identidade do produto; usar apenas a direção de design documentada acima.

## Test Conventions

| Type | Naming | Location | Framework |
| --- | --- | --- | --- |
| Backend unit/integration | TBD | Não há suíte automatizada atualmente | TBD |
| Frontend | TBD | Não há suíte automatizada atualmente | TBD |
| Smoke checks | Comandos explícitos no terminal | Raiz e `frontend/` | `compileall`, `npm run typecheck`, `npm run build` |

## Lint & Cleanup

| Command | Tool | Purpose |
| --- | --- | --- |
| `git diff --check` | Git | Detectar whitespace inválido no diff. |
| `cd frontend && npm run typecheck` | TypeScript | Validar tipos do frontend. |
| `cd frontend && npm run build` | Vite/TypeScript | Validar o build do frontend. |
| TBD | TBD | Não há linter configurado atualmente. |

## On-Demand Reading

- [`README.md`](README.md) — visão geral, coleta, banco, API, cron e geocoding.
- [`config/search_filters.toml`](config/search_filters.toml) — filtros e limites do pipeline.
- [`frontend/package.json`](frontend/package.json) — scripts e dependências do frontend.
- [`src/api/main.py`](src/api/main.py) — contratos HTTP atuais.
