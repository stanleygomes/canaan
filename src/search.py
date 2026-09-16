import asyncio
import json
import os
import sys
import tomllib
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote

from .db import get_search_filters, save_properties
from .geocoding import NominatimGeocoder
from .logger import logger
from .scrapers.chavesnamao import ChavesNaMaoScraper
from .scrapers.imobiliarias_uberlandia import AGENCIES
from .scrapers.imovelweb import ImovelWebScraper
from .scrapers.loft import scraper as loft_scraper
from .scrapers.mercadolivre import scraper as mercadolivre_scraper
from .scrapers.olx import OLXScraper
from .scrapers.quintoandar import scraper as quintoandar_scraper
from .scrapers.vivareal import VivaRealScraper
from .scrapers.zapimoveis import ZapImoveisScraper


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "search_filters.toml"


def load_config() -> Dict[str, Any]:
    with CONFIG_PATH.open("rb") as config_file:
        return tomllib.load(config_file)["search"]


def uberlandia_urls(purpose: str = "sale") -> Dict[str, str]:
    transaction = "aluguel" if purpose == "rent" else "venda"
    quintoandar_transaction = "alugar" if purpose == "rent" else "comprar"
    chaves_transaction = "para-alugar" if purpose == "rent" else "a-venda"
    return {
        "chavesnamao": f"https://www.chavesnamao.com.br/apartamentos-{chaves_transaction}/mg-uberlandia/",
        "vivareal": f"https://www.vivareal.com.br/{transaction}/minas-gerais/uberlandia/apartamento_residencial/",
        "zapimoveis": f"https://www.zapimoveis.com.br/{transaction}/apartamentos/mg+uberlandia/",
        "olx": f"https://www.olx.com.br/imoveis/{transaction}/apartamentos/estado-mg/uberlandia",
        "imovelweb": f"https://www.imovelweb.com.br/apartamentos-{transaction}-uberlandia-mg.html",
        "quintoandar": f"https://www.quintoandar.com.br/{quintoandar_transaction}/imovel/uberlandia-mg-brasil/apartamento",
        "mercadolivre": f"https://lista.mercadolivre.com.br/{transaction}-apartamento-uberlandia",
        "loft": f"https://loft.com.br/{transaction}/apartamentos/mg/uberlandia",
    }


def source_scrapers() -> Dict[str, Any]:
    return {
        "chavesnamao": ChavesNaMaoScraper(),
        "vivareal": VivaRealScraper(),
        "zapimoveis": ZapImoveisScraper(),
        "olx": OLXScraper(),
        "imovelweb": ImovelWebScraper(),
        "quintoandar": quintoandar_scraper,
        "mercadolivre": mercadolivre_scraper,
        "loft": loft_scraper,
        **AGENCIES,
    }


def normalized_text(property_data: Dict[str, Any]) -> str:
    address = property_data.get("address") or {}
    text = " ".join(
        str(value or "")
        for value in [
            property_data.get("url"),
            property_data.get("title"),
            property_data.get("description"),
            address.get("raw_text"),
            address.get("locality"),
            address.get("street"),
        ]
    ).lower()
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def matches_filters(property_data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    text = normalized_text(property_data)

    neighborhoods = [str(item).lower() for item in filters.get("neighborhoods", [])]
    if neighborhoods and not any(neighborhood in text for neighborhood in neighborhoods):
        return False

    property_type = str(filters.get("property_type", "")).lower()
    if property_type and property_type not in text and property_type not in str(property_data.get("property_type", "")).lower():
        return False

    bedrooms_min = _as_decimal(filters.get("bedrooms_min"))
    bedrooms = _as_decimal(property_data.get("bedrooms")) or Decimal("0")
    if bedrooms_min is not None and bedrooms < bedrooms_min:
        return False

    max_price = _as_decimal(filters.get("max_price"))
    price = _as_decimal(property_data.get("price"))
    if max_price is not None and (price is None or price > max_price):
        return False

    city = unicodedata.normalize("NFKD", str(filters.get("city", "")).lower())
    city = "".join(char for char in city if not unicodedata.combining(char))
    if city and city not in text:
        return False

    return True


def _as_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


async def collect_source(
    name: str,
    scraper: Any,
    filters: Dict[str, Any],
    on_item: Any = None,
) -> List[Dict[str, Any]]:
    urls = uberlandia_urls(str(filters.get("purpose", "sale")))
    kwargs = {
        "max_pages": filters.get("max_pages", 1),
        "max_properties": filters.get("max_properties_per_source", 5),
        "output_file": str(ROOT / "data" / f"raw_{name}.json"),
    }
    if name in urls:
        kwargs["search_url"] = urls[name]
    if on_item:
        kwargs["on_item"] = on_item
    return await scraper.run(**kwargs)


async def run(source: str = "all") -> List[Dict[str, Any]]:
    file_filters = load_config()
    try:
        filters = get_search_filters() or file_filters
        logger.info("🧭 Filtros carregados do PostgreSQL")
    except Exception as error:
        filters = file_filters
        logger.warning("⚠️ Não foi possível carregar filtros do PostgreSQL: {}", error)
    available = source_scrapers()
    configured = filters.get("sources", list(available))
    selected = list(available) if source in ("", "all") else [source]
    selected = [name for name in selected if name in configured]

    if not selected:
        raise SystemExit(f"Source desconhecido ou não configurado: {source}")

    (ROOT / "data").mkdir(exist_ok=True)
    geocoder = NominatimGeocoder(
        enabled=filters.get("geocoding_enabled", False),
        max_requests=filters.get("geocoding_max_requests", 4),
        min_interval_seconds=filters.get("geocoding_min_interval_seconds", 15.0),
    )
    all_properties: List[Dict[str, Any]] = []
    for name in selected:
        logger.info("🔎 Iniciando source: {}", name)

        async def persist_item(item: Dict[str, Any]) -> None:
            if not matches_filters(item, filters) or not filters.get("persist_database", True):
                return
            try:
                await asyncio.to_thread(save_properties, [item])
                logger.debug("💾 Imóvel persistido durante a coleta: {}", item.get("url"))
            except Exception as error:
                logger.opt(exception=error).warning(
                    "⚠️ Não foi possível persistir o imóvel durante a coleta: {}",
                    item.get("url"),
                )

        try:
            properties = await collect_source(name, available[name], filters, persist_item)
            geocoded = await geocoder.enrich(
                properties,
                city=str(filters.get("city", "")),
                state=str(filters.get("state", "")),
            )
            if geocoded:
                logger.info("📍 {} imóveis geocodificados em {}", geocoded, name)
            matched = [item for item in properties if matches_filters(item, filters)]
            logger.info("✅ {} imóveis passaram pelos filtros de {}", len(matched), name)
            all_properties.extend(matched)
        except Exception as error:
            logger.opt(exception=error).error("❌ Source {} falhou", name)

    unique: Dict[str, Dict[str, Any]] = {}
    for item in all_properties:
        unique[item["url"]] = item

    output_path = ROOT / str(filters.get("output_file", "imoveis_filtrados.json"))
    with output_path.open("w", encoding="utf-8") as output:
        json.dump(list(unique.values()), output, ensure_ascii=False, indent=2)

    if filters.get("persist_database", True):
        try:
            saved = save_properties(unique.values())
            logger.info("💾 Banco atualizado: {} imóveis persistidos", saved)
        except Exception as error:
            logger.opt(exception=error).error("❌ Não foi possível persistir no PostgreSQL")

    logger.info("🏁 Busca concluída: {} imóveis em '{}'", len(unique), output_path.name)
    return list(unique.values())


if __name__ == "__main__":
    asyncio.run(run(os.environ.get("SOURCE", sys.argv[1] if len(sys.argv) > 1 else "all")))
