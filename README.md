# Canaan

Sistema automatizado de busca e extração de dados (web scraping) de portais imobiliários (ex: OLX, Zap Imóveis, Chaves na Mão, entre outros).

---

## 📌 Visão Geral

O objetivo do projeto é monitorar ofertas de imóveis na web de forma automatizada, coletando detalhes aprofundados de cada anúncio e armazenando-os de forma estruturada para consulta e análise.

---

## 🔎 Metodologia de coleta

Cada scraper acessa uma URL de busca configurada usando Playwright em navegador headless, percorre as páginas definidas, identifica os anúncios disponíveis e extrai seus dados visíveis — como título, preço, área, quartos, vagas, localização, imagens e descrição — usando seletores específicos de cada portal e funções de normalização para valores monetários e numéricos; ao final, os registros são padronizados no mesmo formato e salvos em arquivos JSON para posterior consulta, análise ou persistência em banco de dados.

---

## 🚀 Funcionalidades

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
