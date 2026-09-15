import asyncio
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from playwright.async_api import Browser, Page, async_playwright
from playwright_stealth.stealth import Stealth


def clean_currency(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or any(x in text.lower() for x in ["consulte", "sob consulta", "não informado", "--"]):
        return None
    text = re.sub(r"[^\d,.]", "", text)
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    elif "." in text and len(text.rsplit(".", 1)[-1]) == 3:
        text = text.replace(".", "")
    try:
        return float(text)
    except ValueError:
        return None


def clean_int(value: Any) -> Optional[int]:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group()) if match else None


@dataclass
class PortalConfig:
    portal: str
    default_url: str
    card_selectors: List[str]
    link_patterns: List[str]
    page_parameter: str = "pagina"


class ListingPortalScraper:
    def __init__(self, config: PortalConfig, headless: bool = True):
        self.config = config
        self.headless = headless
        self.stealth = Stealth()

    async def extract_cards(self, page: Page) -> List[Dict[str, Any]]:
        patterns = self.config.link_patterns
        raw_cards = await page.evaluate(
            """({selectors, patterns}) => {
                let elements = [];
                for (const selector of selectors) {
                    elements = [...document.querySelectorAll(selector)];
                    if (elements.length) break;
                }
                if (!elements.length) {
                    const links = [...document.querySelectorAll('a')].filter(a =>
                        patterns.some(pattern => a.href.includes(pattern))
                    );
                    elements = links.map(a => a.closest('article, li, [data-testid], [data-qa]') || a.parentElement);
                }
                return [...new Set(elements)].map(element => {
                    const link = element.querySelector('a[href]') || (element.tagName === 'A' ? element : null);
                    return {
                        href: link?.href || '',
                        lines: (element.innerText || '').split('\\n').map(x => x.trim()).filter(Boolean),
                        title: element.querySelector('h2, h3, [class*="title"], [class*="Title"]')?.innerText?.trim() || '',
                        description: element.querySelector('[class*="description"], [class*="Description"]')?.innerText?.trim() || '',
                        images: [...element.querySelectorAll('img')].map(img => img.currentSrc || img.src).filter(Boolean)
                    };
                });
            }""",
            {"selectors": self.config.card_selectors, "patterns": patterns},
        )

        results = []
        for raw in raw_cards:
            url = raw.get("href", "").split("?")[0]
            if not url or not any(pattern in url for pattern in self.config.link_patterns):
                continue
            lines = raw.get("lines", [])
            text = " | ".join(lines)
            title = raw.get("title") or (lines[0] if lines else "")
            price = next((clean_currency(line) for line in lines if line.startswith("R$") and clean_currency(line) is not None), None)

            def find_number(words: List[str]) -> Optional[int]:
                for line in lines:
                    if any(word in line.lower() for word in words):
                        value = clean_int(line)
                        if value is not None:
                            return value
                return None

            area = find_number(["m²", "m2", "metros"])
            bedrooms = find_number(["quarto", "dormitório"])
            bathrooms = find_number(["banheiro"])
            garages = find_number(["vaga", "garagem"])
            location = next((line for line in lines if "," in line and not line.startswith("R$")), None)

            results.append({
                "portal": self.config.portal,
                "url": url,
                "title": title,
                "description": raw.get("description", ""),
                "price": price,
                "condominium_fee": next((clean_currency(line) for line in lines if "condom" in line.lower()), None),
                "iptu_fee": next((clean_currency(line) for line in lines if "iptu" in line.lower()), None),
                "currency": "BRL",
                "property_type": "Apartment" if "apart" in (title + text).lower() else "Imóvel",
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
        return results

    async def run(self, search_url: Optional[str] = None, max_pages: int = 1, max_properties: int = 5, output_file: Optional[str] = None):
        search_url = search_url or self.config.default_url
        output_file = output_file or f"{self.config.portal}_imoveis.json"
        print(f"=== Iniciando Scraping {self.config.portal} ===")
        results = []
        async with async_playwright() as playwright:
            browser: Browser = await playwright.chromium.launch(headless=self.headless, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR", user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36")
            page = await context.new_page()
            await self.stealth.apply_stealth_async(page)
            for number in range(1, max_pages + 1):
                separator = "&" if "?" in search_url else "?"
                url = search_url if number == 1 else f"{search_url}{separator}{self.config.page_parameter}={number}"
                print(f"[+] Acessando página {number}: {url}")
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_timeout(2500)
                    cards = await self.extract_cards(page)
                    print(f"    Extraídos {len(cards)} imóveis.")
                    results.extend(cards[: max_properties - len(results)])
                except Exception as error:
                    print(f" [!] Erro ao carregar listagem: {error}")
                if len(results) >= max_properties:
                    break
            await browser.close()
        with open(output_file, "w", encoding="utf-8") as output:
            json.dump(results, output, ensure_ascii=False, indent=2)
        print(f"=== Finalizado! {len(results)} imóveis salvos em '{output_file}' ===")
        return results
