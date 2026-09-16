import asyncio
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from playwright.async_api import Browser, Page, async_playwright
from ..logger import logger
from .rate_limiter import navigate_with_rate_limit


def clean_currency(val: Any) -> Optional[float]:
    """Converte valores como 'R$ 1.091.740', 'R$ 550,00', '560000' em float."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    if not val_str or val_str in ["R$ -", "R$ --", "Consulte", "--", "-"]:
        return None
    cleaned = re.sub(r"[^\d,\.]", "", val_str)
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    elif "." in cleaned and len(cleaned.split(".")[-1]) == 3:
        cleaned = cleaned.replace(".", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def clean_int(val: Any) -> Optional[int]:
    """Extrai número inteiro de strings como '2 quartos', '95m²', etc."""
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)
    match = re.search(r"\d+", str(val))
    return int(match.group()) if match else None


def find_in_dict(obj: Any, key: str) -> Any:
    """Busca uma chave recursivamente em dicionários e listas aninhadas."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            found = find_in_dict(v, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_in_dict(item, key)
            if found is not None:
                return found
    return None


class ChavesNaMaoScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def extract_detail(self, page: Page, url: str) -> Optional[Dict[str, Any]]:
        """Acessa a página de detalhes de um imóvel e extrai todos os dados."""
        logger.info("🌐 Acessando detalhe Chaves na Mão: {}", url)
        try:
            await navigate_with_rate_limit(page, url, "chavesnamao")
            await page.wait_for_timeout(1500)
        except Exception as e:
            logger.opt(exception=e).error("❌ Erro ao carregar detalhe Chaves na Mão: {}", url)
            return None

        # 1. Extrair dados estruturados Schema.org (JSON-LD)
        ld_json_data = await page.evaluate(
            """() => {
            const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
            return scripts.map(s => {
                try { return JSON.parse(s.innerText); } catch(e) { return null; }
            }).filter(Boolean);
        }"""
        )

        offers = None
        images = []
        for script_obj in ld_json_data:
            if not offers:
                offers = find_in_dict(script_obj, "offers")
            if not images:
                imgs = find_in_dict(script_obj, "image")
                if isinstance(imgs, list):
                    images = imgs

        item_offered = offers.get("itemOffered", {}) if isinstance(offers, dict) else {}
        offered_by = offers.get("offeredBy", {}) if isinstance(offers, dict) else {}

        # 2. Dados visíveis em tela (fallback e complementos)
        page_lines: List[str] = await page.evaluate(
            """() => {
            return document.body.innerText.split('\\n').map(l => l.trim()).filter(Boolean);
        }"""
        )

        def get_value_after(label: str) -> Optional[str]:
            label_lower = label.lower()
            for idx, line in enumerate(page_lines):
                if line.lower() == label_lower and idx + 1 < len(page_lines):
                    return page_lines[idx + 1]
            return None

        condo_str = get_value_after("Condomínio")
        iptu_str = get_value_after("IPTU")
        garagens_str = get_value_after("Garagens")
        suites_str = get_value_after("Suites")
        area_util_str = get_value_after("Área útil")
        area_total_str = get_value_after("Área total")
        banheiros_str = get_value_after("Banheiros")
        quartos_str = get_value_after("Quartos")

        # Título
        h1_texts = await page.locator("h1").all_inner_texts()
        title = h1_texts[0].strip() if h1_texts else (offers.get("name") if isinstance(offers, dict) else "")

        # Preço: JSON-LD > Linha após 'Venda' / 'Aluguel' > Regex na URL
        price = None
        if isinstance(offers, dict) and offers.get("price"):
            price = clean_currency(offers.get("price"))
        if price is None:
            price_text = get_value_after("Venda") or get_value_after("Aluguel")
            price = clean_currency(price_text)
        if price is None:
            url_match = re.search(r"-RS(\d+)", url)
            if url_match:
                price = float(url_match.group(1))

        # Endereço
        addr = item_offered.get("address", {}) if isinstance(item_offered, dict) else {}
        geo = item_offered.get("geo", {}) if isinstance(item_offered, dict) else {}

        # Endereço por texto visível (se não houver no JSON-LD)
        visible_address = None
        for line in page_lines[:25]:
            if "/" in line and any(c in line for c in ["Curitiba", "PR", "SP", "RJ", "SC", "RS", "MG"]):
                visible_address = line
                break

        # Amenities / Características
        amenities = []
        if isinstance(item_offered, dict):
            for f in item_offered.get("amenityFeature", []):
                if isinstance(f, dict) and f.get("name"):
                    amenities.append(f.get("name"))

        # Montagem dos dados
        data = {
            "portal": "chavesnamao",
            "url": url,
            "title": title,
            "description": offers.get("description", "") if isinstance(offers, dict) else "",
            "price": price,
            "condominium_fee": clean_currency(condo_str),
            "iptu_fee": clean_currency(iptu_str),
            "currency": offers.get("priceCurrency", "BRL") if isinstance(offers, dict) else "BRL",
            "property_type": item_offered.get("@type", "Apartment") if isinstance(item_offered, dict) else "Apartment",
            "bedrooms": clean_int(quartos_str)
            or (item_offered.get("numberOfBedrooms") if isinstance(item_offered, dict) else None),
            "suites": clean_int(suites_str),
            "bathrooms": clean_int(banheiros_str)
            or (item_offered.get("numberOfBathroomsTotal") if isinstance(item_offered, dict) else None),
            "garages": clean_int(garagens_str),
            "useful_area_m2": clean_int(area_util_str)
            or clean_int(item_offered.get("floorSize", {}).get("value") if isinstance(item_offered, dict) else None),
            "total_area_m2": clean_int(area_total_str),
            "address": {
                "street": addr.get("streetAddress"),
                "locality": addr.get("addressLocality"),
                "region": addr.get("addressRegion"),
                "postal_code": addr.get("postalCode"),
                "country": addr.get("addressCountry", "BR"),
                "raw_text": visible_address,
            },
            "geo": {
                "latitude": geo.get("latitude") if isinstance(geo, dict) else None,
                "longitude": geo.get("longitude") if isinstance(geo, dict) else None,
            },
            "advertiser": {
                "name": offered_by.get("name") if isinstance(offered_by, dict) else None,
                "phone": offered_by.get("telephone") if isinstance(offered_by, dict) else None,
                "url": offered_by.get("url") if isinstance(offered_by, dict) else None,
            },
            "amenities": amenities,
            "images": images,
            "collected_at": datetime.now().isoformat(),
        }

        return data

    async def get_listing_urls(self, page: Page, search_url: str, max_pages: int = 1) -> List[str]:
        """Varre as páginas da busca e retorna uma lista de URLs de imóveis."""
        property_urls = set()

        for pg in range(1, max_pages + 1):
            url = f"{search_url.rstrip('/')}/?pg={pg}" if pg > 1 else search_url
            logger.info("🔗 Coletando links Chaves na Mão página {}: {}", pg, url)

            try:
                await navigate_with_rate_limit(page, url, "chavesnamao")
                await page.wait_for_timeout(2000)
            except Exception as e:
                logger.opt(exception=e).error("❌ Erro ao carregar busca Chaves na Mão: {}", url)
                continue

            links = await page.evaluate(
                """() => {
                const anchors = Array.from(document.querySelectorAll('a'));
                return anchors
                    .map(a => a.href)
                    .filter(href => href && (href.includes('/imovel/') || href.includes('/lancamento/')) && href.includes('/id-'));
            }"""
            )

            for link in links:
                clean_link = link.split("?")[0]
                property_urls.add(clean_link)

            logger.info("🔗 {} links encontrados; {} únicos acumulados", len(links), len(property_urls))

        return list(property_urls)

    async def run(
        self,
        search_url: str = "https://www.chavesnamao.com.br/apartamentos-a-venda/pr-curitiba/",
        max_pages: int = 1,
        max_properties: int = 3,
        output_file: str = "chavesnamao_imoveis.json",
    ) -> List[Dict[str, Any]]:
        """Orquestra a busca, coleta os detalhes de cada imóvel e salva em JSON."""
        logger.info("🚀 Iniciando scraping Chaves na Mão | URL: {} | páginas: {} | limite: {}", search_url, max_pages, max_properties)

        results = []

        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            )
            page = await context.new_page()

            urls = await self.get_listing_urls(page, search_url, max_pages=max_pages)
            urls_to_scrape = urls[:max_properties]

            logger.info("📦 Extraindo detalhes de {} imóveis", len(urls_to_scrape))

            for idx, prop_url in enumerate(urls_to_scrape, 1):
                logger.info("🏠 Imóvel {}/{}", idx, len(urls_to_scrape))
                item = await self.extract_detail(page, prop_url)
                if item:
                    results.append(item)
                    logger.info("✅ {} | R$ {} | {}m² | {} quartos | {} vagas | {} fotos", item['title'][:55], item['price'], item['useful_area_m2'], item['bedrooms'], item['garages'], len(item['images']))

                await asyncio.sleep(1)

            await browser.close()

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info("✅ Scraping Chaves na Mão finalizado: {} imóveis salvos em '{}'", len(results), output_file)
        return results


if __name__ == "__main__":
    scraper = ChavesNaMaoScraper(headless=True)
    asyncio.run(
        scraper.run(
            search_url="https://www.chavesnamao.com.br/apartamentos-a-venda/pr-curitiba/",
            max_pages=1,
            max_properties=3,
            output_file="chavesnamao_imoveis.json",
        )
    )
