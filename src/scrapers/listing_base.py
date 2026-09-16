import asyncio
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from playwright.async_api import Browser, Page, async_playwright
from playwright_stealth.stealth import Stealth
from ..logger import logger


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


def fold_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(char for char in text if not unicodedata.combining(char)).lower()


def labeled_number(lines: List[str], labels: List[str]) -> Optional[int]:
    for index, line in enumerate(lines):
        current = fold_text(line)
        context = f"{current} {fold_text(lines[index + 1]) if index + 1 < len(lines) else ''}"
        for label in labels:
            match = re.search(rf"(\d+)\s*{re.escape(fold_text(label))}", context)
            if match:
                return int(match.group(1))
            if fold_text(label) in current and index > 0:
                previous = clean_int(lines[index - 1])
                if previous is not None:
                    return previous
    return None


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
                    elements = links.map(a => a.closest('article, li, [data-testid], [data-qa], [class*="card"], [class*="item"]') || a.parentElement);
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
                labeled = labeled_number(lines, words)
                if labeled is not None:
                    return labeled
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

    async def enrich_from_detail(self, page: Page, item: Dict[str, Any]) -> Dict[str, Any]:
        """Completa campos que alguns portais só exibem na página do anúncio."""
        try:
            await page.goto(item["url"], wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(700)
            lines = await page.locator("body").evaluate(
                "body => body.innerText.split('\\n').map(x => x.trim()).filter(Boolean)"
            )
            title = await page.locator("h1").first.inner_text() if await page.locator("h1").count() else ""
            detail_text = " | ".join(lines)
            if title:
                item["title"] = title.strip()
            if not item.get("price"):
                item["price"] = next((clean_currency(line) for line in lines if line.startswith("R$") and clean_currency(line) is not None), None)

            def detail_number(words: List[str]) -> Optional[int]:
                labeled = labeled_number(lines, words)
                if labeled is not None:
                    return labeled
                for line in lines:
                    if any(word in fold_text(line) for word in words):
                        value = clean_int(line)
                        if value is not None:
                            return value
                return None

            item["bedrooms"] = item.get("bedrooms") or detail_number(["quarto", "dormitorio"])
            item["bathrooms"] = item.get("bathrooms") or detail_number(["banheiro"])
            item["garages"] = item.get("garages") or detail_number(["vaga", "garagem"])
            item["useful_area_m2"] = item.get("useful_area_m2") or detail_number(["m²", "m2", "metros"])
            item["description"] = item.get("description") or detail_text[:4000]
            if item.get("property_type") == "Imóvel":
                item["property_type"] = "Apartment" if "apartamento" in fold_text(item["title"] + detail_text) else item["property_type"]
        except Exception as error:
            logger.opt(exception=error).warning("⚠️ Não foi possível enriquecer {}", item.get("url"))
        return item

    async def run(self, search_url: Optional[str] = None, max_pages: int = 1, max_properties: int = 5, output_file: Optional[str] = None):
        search_url = search_url or self.config.default_url
        output_file = output_file or f"{self.config.portal}_imoveis.json"
        logger.info("🚀 Iniciando scraping: {}", self.config.portal)
        results = []
        async with async_playwright() as playwright:
            browser: Browser = await playwright.chromium.launch(headless=self.headless, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR", user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36")
            page = await context.new_page()
            await self.stealth.apply_stealth_async(page)
            for number in range(1, max_pages + 1):
                separator = "&" if "?" in search_url else "?"
                url = search_url if number == 1 else f"{search_url}{separator}{self.config.page_parameter}={number}"
                logger.info("🌐 Acessando {} página {}: {}", self.config.portal, number, url)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_timeout(2500)
                    cards = await self.extract_cards(page)
                    logger.info("📦 {} imóveis extraídos de {}", len(cards), self.config.portal)
                    for card in cards:
                        if not card.get("bedrooms") or not card.get("price"):
                            await self.enrich_from_detail(page, card)
                    results.extend(cards[: max_properties - len(results)])
                except Exception as error:
                    logger.opt(exception=error).error("❌ Erro ao carregar listagem de {}", self.config.portal)
                if len(results) >= max_properties:
                    break
            await browser.close()
        with open(output_file, "w", encoding="utf-8") as output:
            json.dump(results, output, ensure_ascii=False, indent=2)
        logger.info("✅ Scraping {} finalizado: {} imóveis salvos em '{}'", self.config.portal, len(results), output_file)
        return results
