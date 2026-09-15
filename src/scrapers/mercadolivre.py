import asyncio

from .listing_base import ListingPortalScraper, PortalConfig


scraper = ListingPortalScraper(PortalConfig(
    portal="mercadolivre",
    default_url="https://lista.mercadolivre.com.br/venda-apartamento-curitiba",
    card_selectors=["li.ui-search-layout__item", ".ui-search-result__wrapper", "[data-testid*=item]"],
    link_patterns=["apartamento.mercadolivre.com.br/", "mercadolivre.com.br/MLB-"],
    page_parameter="Desde",
))


if __name__ == "__main__":
    asyncio.run(scraper.run(max_properties=3))
