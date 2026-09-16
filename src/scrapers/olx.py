import asyncio
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from playwright.async_api import Browser, Page, async_playwright
from playwright_stealth.stealth import Stealth
from ..logger import logger
from .rate_limiter import navigate_with_rate_limit


def clean_currency(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    if not val_str or any(w in val_str.lower() for w in ["consulte", "não informado", "--"]):
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
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)
    match = re.search(r"\d+", str(val))
    return int(match.group()) if match else None


class OLXScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.stealth = Stealth()

    async def extract_listing_cards(self, page: Page) -> List[Dict[str, Any]]:
        """Extrai todos os cards de anúncios da página de busca da OLX."""
        raw_cards = await page.evaluate(r"""() => {
            const sections = Array.from(document.querySelectorAll('section.olx-adcard'));
            return sections.map(s => {
                const linkEl = s.querySelector('a.olx-adcard__link') || s.querySelector('a[href*="/imoveis/"]');
                const href = linkEl ? linkEl.href : '';
                const lines = s.innerText.split('\n').map(l => l.trim()).filter(Boolean);
                const imgs = Array.from(s.querySelectorAll('img')).map(i => i.src);
                return { href, lines, imgs };
            });
        }""")

        cards = []
        for rc in raw_cards:
            href = rc.get("href", "").split("?")[0]
            if not href or "/imoveis/" not in href:
                continue

            lines: List[str] = rc.get("lines", [])
            imgs: List[str] = rc.get("imgs", [])

            title = lines[0] if lines else ""
            price = None
            condo = None
            iptu = None
            area = None
            bedrooms = None
            bathrooms = None
            garages = None
            location_str = None

            # Interpretar as linhas do card da OLX
            # Padrão típico do card OLX:
            # 0: Título
            # 1: Metragem (ex: 30m²)
            # 2: Quartos
            # 3: Banheiros
            # 4: Vagas
            # 5+: Preço (ex: R$ 370.000)
            # 6+: IPTU ou Condomínio
            # 7+: Localização (ex: Curitiba, Cajuru)
            for idx, line in enumerate(lines):
                if line.endswith("m²") and area is None:
                    area = clean_int(line)
                    # Os números seguintes costumam ser quartos, banheiros e vagas
                    if idx + 1 < len(lines) and lines[idx + 1].isdigit():
                        bedrooms = clean_int(lines[idx + 1])
                    if idx + 2 < len(lines) and lines[idx + 2].isdigit():
                        bathrooms = clean_int(lines[idx + 2])
                    if idx + 3 < len(lines) and lines[idx + 3].isdigit():
                        garages = clean_int(lines[idx + 3])
                elif line.startswith("R$ ") and price is None:
                    price = clean_currency(line)
                elif "IPTU" in line:
                    iptu = clean_currency(line.replace("IPTU", ""))
                elif "Condomínio" in line or "Cond." in line:
                    condo = clean_currency(line.replace("Condomínio", "").replace("Cond.", ""))
                elif any(w in line.lower() for w in ["hoje,", "ontem,"]) or re.search(r"\d{2}/\d{2}", line):
                    # A linha anterior à data costuma ser a localização (Bairro, Cidade)
                    if idx > 0 and "," in lines[idx - 1] and not lines[idx - 1].startswith("R$"):
                        location_str = lines[idx - 1]
                elif "," in line and not line.startswith("R$") and "•" not in line and location_str is None:
                    location_str = line

            item = {
                "portal": "olx",
                "url": href,
                "title": title,
                "description": "",
                "price": price,
                "condominium_fee": condo,
                "iptu_fee": iptu,
                "currency": "BRL",
                "property_type": "Apartment" if "apartamento" in href.lower() else "Imóvel",
                "bedrooms": bedrooms,
                "suites": None,
                "bathrooms": bathrooms,
                "garages": garages,
                "useful_area_m2": area,
                "total_area_m2": None,
                "address": {
                    "raw_text": location_str,
                },
                "advertiser": {
                    "name": None,
                },
                "images": imgs,
                "collected_at": datetime.now().isoformat(),
            }
            cards.append(item)

        return cards

    async def run(
        self,
        search_url: str = "https://www.olx.com.br/imoveis/venda/apartamentos/estado-pr/curitiba-e-regiao",
        max_pages: int = 1,
        max_properties: int = 5,
        output_file: str = "olx_imoveis.json",
    ) -> List[Dict[str, Any]]:
        """Orquestra a coleta de imóveis da OLX."""
        logger.info("🚀 Iniciando scraping OLX | URL: {} | páginas: {} | limite: {}", search_url, max_pages, max_properties)

        all_properties = []

        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                locale="pt-BR",
            )
            page = await context.new_page()
            await self.stealth.apply_stealth_async(page)

            for pg in range(1, max_pages + 1):
                url = f"{search_url.rstrip('/')}?o={pg}" if pg > 1 else search_url
                logger.info("🌐 Acessando OLX página {}: {}", pg, url)

                try:
                    await navigate_with_rate_limit(page, url, "olx")
                    await page.wait_for_timeout(2500)
                except Exception as e:
                    logger.opt(exception=e).error("❌ Erro ao carregar listagem OLX: {}", url)
                    continue

                cards = await self.extract_listing_cards(page)
                logger.info("📦 {} imóveis extraídos da página {} da OLX", len(cards), pg)

                for c in cards:
                    all_properties.append(c)
                    if len(all_properties) >= max_properties:
                        break

                if len(all_properties) >= max_properties:
                    break

            await browser.close()

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_properties, f, ensure_ascii=False, indent=2)

        logger.info("✅ Scraping OLX finalizado: {} imóveis salvos em '{}'", len(all_properties), output_file)
        return all_properties


if __name__ == "__main__":
    scraper = OLXScraper(headless=True)
    asyncio.run(
        scraper.run(
            search_url="https://www.olx.com.br/imoveis/venda/apartamentos/estado-pr/curitiba-e-regiao",
            max_pages=1,
            max_properties=3,
            output_file="olx_imoveis.json",
        )
    )
