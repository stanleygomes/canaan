import asyncio
import sys
from typing import Dict

from .listing_base import ListingPortalScraper, PortalConfig


AGENCIES: Dict[str, ListingPortalScraper] = {
    "rotina": ListingPortalScraper(PortalConfig(
        portal="rotina",
        default_url="https://www.rotina.com.br/venda",
        card_selectors=[],
        link_patterns=["rotina.com.br/imovel/"],
    )),
    "multi": ListingPortalScraper(PortalConfig(
        portal="multi",
        default_url="https://www2.multi.com.br/vendas",
        card_selectors=[],
        link_patterns=["multi.com.br/vendas/"],
    )),
    "objetiva": ListingPortalScraper(PortalConfig(
        portal="objetiva",
        default_url="https://www.objetivauberlandia.com.br/venda/imovel",
        card_selectors=[],
        link_patterns=["objetivauberlandia.com.br/imovel/"],
    )),
    "alianca": ListingPortalScraper(PortalConfig(
        portal="alianca",
        default_url="https://aliancaimob.com/imoveis-venda",
        card_selectors=[],
        link_patterns=["aliancaimob.com/imoveis-venda/"],
    )),
    "delta": ListingPortalScraper(PortalConfig(
        portal="delta",
        default_url="https://www.deltaimoveis.com.br/pesquisa-de-imoveis/?locacao_venda=V&finalidade=residencial&ordem=6",
        card_selectors=[],
        link_patterns=["deltaimoveis.com.br/imovel/", "deltaimoveis.com.br/imoveis/"],
    )),
    "arantes": ListingPortalScraper(PortalConfig(
        portal="arantes",
        default_url="https://www.arantesimoveis.com/revenda/Tipo_Imovel/Regiao/busca",
        card_selectors=[],
        link_patterns=["/revenda"],
    )),
    "ivan": ListingPortalScraper(PortalConfig(
        portal="ivan",
        default_url="https://www.ivannegocios.com.br/comprar/uberlandia/casa?flag_empree_ou_imoveis=1",
        card_selectors=[],
        link_patterns=["ivannegocios.com.br/imovel/"],
    )),
    "lider": ListingPortalScraper(PortalConfig(
        portal="lider",
        default_url="https://www.liderimobiliaria.com.br/venda/imoveis/todas-as-cidades/todos-os-bairros/0-quartos/0-suite-ou-mais/0-vaga/0-banheiro-ou-mais/todos-os-condominios?valorminimo=0&valormaximo=0&pagina=1",
        card_selectors=[],
        link_patterns=["liderimobiliaria.com.br/imovel/"],
    )),
}


async def run_all(max_properties: int = 5) -> None:
    for name, scraper in AGENCIES.items():
        print(f"\n### {name} ###")
        await scraper.run(max_properties=max_properties)


async def run_one(name: str, max_properties: int = 5) -> None:
    if name not in AGENCIES:
        raise SystemExit(f"Imobiliária desconhecida: {name}. Opções: {', '.join(AGENCIES)}")
    await AGENCIES[name].run(max_properties=max_properties)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(run_one(sys.argv[1], max_properties=3))
    else:
        asyncio.run(run_all(max_properties=3))
