import asyncio

from .listing_base import ListingPortalScraper, PortalConfig


scraper = ListingPortalScraper(PortalConfig(
    portal="loft",
    default_url="https://loft.com.br/venda/apartamentos/pr/curitiba",
    card_selectors=["[data-testid*=listing]", "[data-testid*=property]", "article", "li"],
    link_patterns=["loft.com.br/venda/imovel/"],
))


if __name__ == "__main__":
    asyncio.run(scraper.run(max_properties=3))
