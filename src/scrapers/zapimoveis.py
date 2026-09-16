import asyncio
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from playwright.async_api import Browser, Page, async_playwright
from playwright_stealth.stealth import Stealth
from ..logger import logger


def clean_currency(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    if not val_str or any(w in val_str.lower() for w in ["consulte", "sob consulta", "não informado", "--"]):
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


class ZapImoveisScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.stealth = Stealth()

    async def extract_listing_cards(self, page: Page) -> List[Dict[str, Any]]:
        """Extrai todos os cards da listagem da página de busca do ZAP Imóveis."""
        raw_cards = await page.evaluate(r"""() => {
            const els = Array.from(document.querySelectorAll('.olx-core-card'));
            return els.map(el => {
                const href = el.href || el.querySelector('a')?.href || '';
                const lines = el.innerText.split('\n').map(s => s.trim()).filter(Boolean);
                const imgs = Array.from(el.querySelectorAll('img')).map(i => i.src);
                return { href, lines, imgs };
            });
        }""")

        cards = []
        for rc in raw_cards:
            href = rc.get("href", "").split("?")[0]
            if not href or ("/imovel/" not in href and "/lancamento" not in href):
                continue

            lines: List[str] = rc.get("lines", [])
            imgs: List[str] = rc.get("imgs", [])

            title = ""
            advertiser = None
            price = None
            condo = None
            iptu = None
            area = None
            bedrooms = None
            bathrooms = None
            garages = None
            street = None
            locality = None

            for i, line in enumerate(lines):
                if "Apartamento para comprar com" in line or "Imóvel para" in line:
                    title = line
                    if i + 1 < len(lines):
                        locality = lines[i + 1]
                    if i + 2 < len(lines) and ("Rua " in lines[i + 2] or "Avenida " in lines[i + 2] or "Alameda " in lines[i + 2] or "Praça " in lines[i + 2]):
                        street = lines[i + 2]
                elif line.startswith("R$ ") and price is None:
                    price = clean_currency(line)
                elif "Cond." in line or "IPTU" in line:
                    condo_match = re.search(r"Cond\.\s*R\$\s*([\d\.]+)", line)
                    if condo_match:
                        condo = clean_currency(condo_match.group(1))
                    iptu_match = re.search(r"IPTU\s*R\$\s*([\d\.]+)", line)
                    if iptu_match:
                        iptu = clean_currency(iptu_match.group(1))
                elif line == "Tamanho do imóvel" and i + 1 < len(lines):
                    area = clean_int(lines[i + 1])
                elif line == "Quantidade de quartos" and i + 1 < len(lines):
                    bedrooms = clean_int(lines[i + 1])
                elif line == "Quantidade de banheiros" and i + 1 < len(lines):
                    bathrooms = clean_int(lines[i + 1])
                elif line == "Quantidade de vagas de garagem" and i + 1 < len(lines):
                    garages = clean_int(lines[i + 1])

            # Anunciante
            for l in lines[:3]:
                if l not in ["Destaque", "Super Destaque", "Em construção"] and not l.startswith("+") and not l.startswith("R$"):
                    advertiser = l
                    break

            if not title and lines:
                title = lines[0]

            item = {
                "portal": "zapimoveis",
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
                    "street": street,
                    "locality": locality,
                    "raw_text": f"{street or ''}, {locality or ''}".strip(", "),
                },
                "advertiser": {
                    "name": advertiser,
                },
                "images": imgs,
                "collected_at": datetime.now().isoformat(),
            }
            cards.append(item)

        return cards

    async def run(
        self,
        search_url: str = "https://www.zapimoveis.com.br/venda/apartamentos/pr+curitiba/",
        max_pages: int = 1,
        max_properties: int = 5,
        output_file: str = "zapimoveis_imoveis.json",
    ) -> List[Dict[str, Any]]:
        """Orquestra a coleta de imóveis do ZAP Imóveis."""
        logger.info("🚀 Iniciando scraping ZAP Imóveis | URL: {} | páginas: {} | limite: {}", search_url, max_pages, max_properties)

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
                url = f"{search_url.rstrip('/')}/?pagina={pg}" if pg > 1 else search_url
                logger.info("🌐 Acessando ZAP Imóveis página {}: {}", pg, url)

                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_timeout(2500)
                except Exception as e:
                    logger.opt(exception=e).error("❌ Erro ao carregar listagem ZAP Imóveis: {}", url)
                    continue

                cards = await self.extract_listing_cards(page)
                logger.info("📦 {} imóveis extraídos da página {} do ZAP Imóveis", len(cards), pg)

                for c in cards:
                    all_properties.append(c)
                    if len(all_properties) >= max_properties:
                        break

                if len(all_properties) >= max_properties:
                    break

            await browser.close()

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_properties, f, ensure_ascii=False, indent=2)

        logger.info("✅ Scraping ZAP Imóveis finalizado: {} imóveis salvos em '{}'", len(all_properties), output_file)
        return all_properties


if __name__ == "__main__":
    scraper = ZapImoveisScraper(headless=True)
    asyncio.run(
        scraper.run(
            search_url="https://www.zapimoveis.com.br/venda/apartamentos/pr+curitiba/",
            max_pages=1,
            max_properties=3,
            output_file="zapimoveis_imoveis.json",
        )
    )
