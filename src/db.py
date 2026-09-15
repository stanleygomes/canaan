from typing import Any, Dict, Iterable

import psycopg
from psycopg.types.json import Jsonb

from .settings import get_settings


SCRAPE_LOCK_KEY = "canaan:scrape"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS properties (
    id BIGSERIAL PRIMARY KEY,
    portal VARCHAR(80) NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    price NUMERIC(14, 2),
    condominium_fee NUMERIC(14, 2),
    iptu_fee NUMERIC(14, 2),
    currency CHAR(3) NOT NULL DEFAULT 'BRL',
    property_type VARCHAR(80),
    bedrooms SMALLINT,
    suites SMALLINT,
    bathrooms SMALLINT,
    garages SMALLINT,
    useful_area_m2 NUMERIC(12, 2),
    total_area_m2 NUMERIC(12, 2),
    address JSONB NOT NULL DEFAULT '{}'::jsonb,
    geo JSONB NOT NULL DEFAULT '{}'::jsonb,
    advertiser JSONB NOT NULL DEFAULT '{}'::jsonb,
    amenities JSONB NOT NULL DEFAULT '[]'::jsonb,
    images JSONB NOT NULL DEFAULT '[]'::jsonb,
    collected_at TIMESTAMPTZ,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT properties_portal_url_key UNIQUE (portal, url),
    CONSTRAINT properties_currency_length CHECK (char_length(currency) = 3),
    CONSTRAINT properties_non_negative_numbers CHECK (
        (price IS NULL OR price >= 0) AND
        (bedrooms IS NULL OR bedrooms >= 0) AND
        (suites IS NULL OR suites >= 0) AND
        (bathrooms IS NULL OR bathrooms >= 0) AND
        (garages IS NULL OR garages >= 0) AND
        (useful_area_m2 IS NULL OR useful_area_m2 >= 0) AND
        (total_area_m2 IS NULL OR total_area_m2 >= 0)
    )
);

CREATE INDEX IF NOT EXISTS properties_portal_idx ON properties (portal);
CREATE INDEX IF NOT EXISTS properties_price_idx ON properties (price);
CREATE INDEX IF NOT EXISTS properties_bedrooms_idx ON properties (bedrooms);
CREATE INDEX IF NOT EXISTS properties_last_seen_idx ON properties (last_seen_at);
"""


UPSERT_SQL = """
INSERT INTO properties (
    portal, url, title, description, price, condominium_fee, iptu_fee,
    currency, property_type, bedrooms, suites, bathrooms, garages,
    useful_area_m2, total_area_m2, address, geo, advertiser, amenities,
    images, collected_at, raw_payload
) VALUES (
    %(portal)s, %(url)s, %(title)s, %(description)s, %(price)s,
    %(condominium_fee)s, %(iptu_fee)s, %(currency)s, %(property_type)s,
    %(bedrooms)s, %(suites)s, %(bathrooms)s, %(garages)s,
    %(useful_area_m2)s, %(total_area_m2)s, %(address)s, %(geo)s,
    %(advertiser)s, %(amenities)s, %(images)s, %(collected_at)s,
    %(raw_payload)s
)
ON CONFLICT (portal, url) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    price = EXCLUDED.price,
    condominium_fee = EXCLUDED.condominium_fee,
    iptu_fee = EXCLUDED.iptu_fee,
    currency = EXCLUDED.currency,
    property_type = EXCLUDED.property_type,
    bedrooms = EXCLUDED.bedrooms,
    suites = EXCLUDED.suites,
    bathrooms = EXCLUDED.bathrooms,
    garages = EXCLUDED.garages,
    useful_area_m2 = EXCLUDED.useful_area_m2,
    total_area_m2 = EXCLUDED.total_area_m2,
    address = EXCLUDED.address,
    geo = EXCLUDED.geo,
    advertiser = EXCLUDED.advertiser,
    amenities = EXCLUDED.amenities,
    images = EXCLUDED.images,
    collected_at = EXCLUDED.collected_at,
    last_seen_at = NOW(),
    raw_payload = EXCLUDED.raw_payload
"""


def database_url() -> str:
    return get_settings().database_url


class ScrapeAlreadyRunning(RuntimeError):
    pass


class DatabaseUnavailable(RuntimeError):
    pass


class ScrapeExecutionLock:
    """Lock distribuído no PostgreSQL para API e cron compartilharem o estado."""

    def __init__(self) -> None:
        self.connection: psycopg.Connection | None = None

    def acquire(self) -> "ScrapeExecutionLock":
        try:
            self.connection = psycopg.connect(database_url(), connect_timeout=5)
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_try_advisory_lock(hashtextextended(%s, 0))",
                    (SCRAPE_LOCK_KEY,),
                )
                acquired = cursor.fetchone()[0]
            if not acquired:
                self.close()
                raise ScrapeAlreadyRunning("Já existe uma execução em andamento")
            return self
        except ScrapeAlreadyRunning:
            raise
        except Exception as error:
            self.close()
            raise DatabaseUnavailable("PostgreSQL indisponível") from error

    def close(self) -> None:
        if self.connection is None:
            return
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_unlock(hashtextextended(%s, 0))",
                    (SCRAPE_LOCK_KEY,),
                )
            self.connection.commit()
        finally:
            self.connection.close()
            self.connection = None


def normalized_property(item: Dict[str, Any]) -> Dict[str, Any]:
    """Converte a saída dos scrapers para o contrato persistido no banco."""
    if not item.get("portal") or not item.get("url"):
        raise ValueError("Imóvel precisa de portal e url para ser persistido")

    return {
        "portal": str(item["portal"]),
        "url": str(item["url"]),
        "title": str(item.get("title") or ""),
        "description": str(item.get("description") or ""),
        "price": item.get("price"),
        "condominium_fee": item.get("condominium_fee"),
        "iptu_fee": item.get("iptu_fee"),
        "currency": str(item.get("currency") or "BRL").upper(),
        "property_type": item.get("property_type"),
        "bedrooms": item.get("bedrooms"),
        "suites": item.get("suites"),
        "bathrooms": item.get("bathrooms"),
        "garages": item.get("garages"),
        "useful_area_m2": item.get("useful_area_m2"),
        "total_area_m2": item.get("total_area_m2"),
        "address": Jsonb(item.get("address") or {}),
        "geo": Jsonb(item.get("geo") or {}),
        "advertiser": Jsonb(item.get("advertiser") or {}),
        "amenities": Jsonb(item.get("amenities") or []),
        "images": Jsonb(item.get("images") or []),
        "collected_at": item.get("collected_at"),
        "raw_payload": Jsonb(item),
    }


def save_properties(properties: Iterable[Dict[str, Any]]) -> int:
    records = [normalized_property(item) for item in properties]
    if not records:
        return 0

    with psycopg.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(SCHEMA_SQL)
            cursor.executemany(UPSERT_SQL, records)
        connection.commit()
    return len(records)
