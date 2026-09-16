import asyncio
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from playwright.async_api import Browser, Page, async_playwright
from playwright_stealth.stealth import Stealth
from ..logger import logger


def clean_currency(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text or any(word in text.lower() for word in ["consulte", "sob consulta", "não informado", "--"]):
        return None

    cleaned = re.sub(r"[^\d,.]", "", text)
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    elif "." in cleaned and len(cleaned.rsplit(".", 1)[-1]) == 3:
        cleaned = cleaned.replace(".", "")

    try:
        return float(cleaned)
    except ValueError:
        return None


def clean_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else None


class ImovelWebScraper:
    """Coleta anúncios da busca do Imovelweb e salva o resultado em JSON."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.stealth = Stealth()

    async def extract_listing_cards(self, page: Page) -> List[Dict[str, Any]]:
        raw_cards = await page.evaluate(r"""() => {
            const selectors = [
                '[data-qa="posting"]',
                '[data-qa="posting-card"]',
                '.postingCard',
                'article[class*="posting"]',
                'article'
            ];
            let elements = [];
            for (const selector of selectors) {
                elements = Array.from(document.querySelectorAll(selector));
                if (elements.length) break;
            }

            return elements.map((element) => {
                const link = element.querySelector('a[href*="/imovel/"], a[href*="/propriedade/"]') || element.querySelector('a');
                const lines = (element.innerText || '').split('\n').map(x => x.trim()).filter(Boolean);
                const images = Array.from(element.querySelectorAll('img')).map(img => img.currentSrc || img.src).filter(Boolean);
                return {
                    href: link ? link.href : '',
                    lines,
                    images,
                    title: element.querySelector('[class*="Title"], [class*="title"], h2, h3')?.innerText?.trim() || '',
                    description: element.querySelector('[class*="Description"], [class*="description"]')?.innerText?.trim() || '',
                };
            });
        }""")

        properties = []
        for raw in raw_cards:
            url = raw.get("href", "").split("?")[0]
            if not url or "imovelweb.com.br" not in url:
                continue

            lines = raw.get("lines", [])
            title = raw.get("title") or (lines[0] if lines else "")
            description = raw.get("description", "")
            price = condominium = iptu = area = bedrooms = bathrooms = garages = None
            location = None

            for index, line in enumerate(lines):
                lower = line.lower()
                if price is None and line.startswith("R$ "):
                    price = clean_currency(line)
                if "condom" in lower and condominium is None:
                    condominium = clean_currency(line)
                if "iptu" in lower and iptu is None:
                    iptu = clean_currency(line)
                if area is None and re.search(r"\d+\s*m²", lower):
                    area = clean_int(line)
                if bedrooms is None and re.search(r"\d+\s*(quarto|dormitório)", lower):
                    bedrooms = clean_int(line)
                if bathrooms is None and re.search(r"\d+\s*banheiro", lower):
                    bathrooms = clean_int(line)
                if garages is None and re.search(r"\d+\s*vaga", lower):
                    garages = clean_int(line)
                if location is None and ("curitiba" in lower or "uber" in lower or "," in line):
                    if not line.startswith("R$ ") and not any(word in lower for word in ["quarto", "banheiro", "vaga", "m²"]):
                        location = line

            properties.append({
                "portal": "imovelweb",
                "url": url,
                "title": title,
                "description": description,
                "price": price,
                "condominium_fee": condominium,
                "iptu_fee": iptu,
                "currency": "BRL",
                "property_type": "Apartment" if "apart" in (title + url).lower() else "Imóvel",
                "bedrooms": bedrooms,
                "suites": None,
                "bathrooms": bathrooms,
                "garages": garages,
                "useful_area_m2": area,
                "total_area_m2": None,
                "address": {"raw_text": location},
                "advertiser": {"name": None},
                "images": raw.get("images", []),
                "collected_at": datetime.now().isoformat(),
            })

        return properties

    async def run(
        self,
        search_url: str = "https://www.imovelweb.com.br/apartamentos-venda-curitiba-pr.html",
        max_pages: int = 1,
        max_properties: int = 5,
        output_file: str = "imovelweb_imoveis.json",
    ) -> List[Dict[str, Any]]:
        logger.info("🚀 Iniciando scraping Imovelweb | URL: {} | páginas: {} | limite: {}", search_url, max_pages, max_properties)
        results = []

        async with async_playwright() as playwright:
            browser: Browser = await playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                locale="pt-BR",
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            )
            page = await context.new_page()
            await self.stealth.apply_stealth_async(page)

            for page_number in range(1, max_pages + 1):
                url = search_url if page_number == 1 else f"{search_url.rstrip('/')}/?pagina={page_number}"
                logger.info("🌐 Acessando Imovelweb página {}: {}", page_number, url)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_timeout(2500)
                    page_text = (await page.locator("body").inner_text()).lower()
                    if "verificação de segurança" in page_text or "executando verificação" in page_text:
                        raise RuntimeError(
                            "O Imovelweb exibiu uma verificação antirobô (Cloudflare); "
                            "nenhum anúncio foi coletado."
                        )
                except Exception as error:
                    logger.opt(exception=error).error("❌ Erro ao carregar listagem Imovelweb")
                    continue

                cards = await self.extract_listing_cards(page)
                logger.info("📦 {} imóveis extraídos da página {} do Imovelweb", len(cards), page_number)
                results.extend(cards[: max_properties - len(results)])
                if len(results) >= max_properties:
                    break

            await browser.close()

        with open(output_file, "w", encoding="utf-8") as output:
            json.dump(results, output, ensure_ascii=False, indent=2)
        logger.info("✅ Scraping Imovelweb finalizado: {} imóveis salvos em '{}'", len(results), output_file)
        return results


if __name__ == "__main__":
    asyncio.run(ImovelWebScraper().run(max_properties=3))
