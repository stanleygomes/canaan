import asyncio

from .listing_base import ListingPortalScraper, PortalConfig


scraper = ListingPortalScraper(PortalConfig(
    portal="quintoandar",
    default_url="https://www.quintoandar.com.br/comprar/imovel/curitiba-pr-brasil/apartamento",
    card_selectors=["[data-testid*=property-card]", "[data-qa*=property]", "article", "li"],
    link_patterns=["quintoandar.com.br/imovel/"],
))


if __name__ == "__main__":
    asyncio.run(scraper.run(max_properties=3))
