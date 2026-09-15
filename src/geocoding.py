import asyncio
import json
import os
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import httpx


ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = ROOT / "data" / "geocode_cache.json"


def fold_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).lower()
    return "".join(char for char in text if not unicodedata.combining(char))


def numeric_coordinate(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


class NominatimGeocoder:
    def __init__(
        self,
        enabled: bool = True,
        max_requests: int = 4,
        min_interval_seconds: float = 15.0,
        endpoint: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        self.enabled = enabled
        self.max_requests = max_requests
        self.min_interval_seconds = min_interval_seconds
        self.endpoint = endpoint or os.environ.get(
            "GEOCODING_URL", "https://nominatim.openstreetmap.org/search"
        )
        self.user_agent = user_agent or os.environ.get(
            "GEOCODING_USER_AGENT", "canaan/0.1 (contact: configure-your-email@example.com)"
        )
        self._cache = self._load_cache()
        self._requests = 0
        self._last_request_at = 0.0

    async def enrich(
        self,
        properties: Iterable[Dict[str, Any]],
        city: str = "",
        state: str = "",
    ) -> int:
        items = list(properties)
        for item in items:
            self._normalize_existing_geo(item)
        if not self.enabled:
            return 0

        enriched = 0
        async with httpx.AsyncClient(
            headers={"User-Agent": self.user_agent}, timeout=20.0
        ) as client:
            for item in items:
                if self._normalize_existing_geo(item):
                    continue
                if self._requests >= self.max_requests:
                    break
                query = self._address_query(item, city, state)
                if not query:
                    continue
                result = self._cache.get(fold_text(query))
                if result is None:
                    result = await self._request(client, query)
                    self._cache[fold_text(query)] = result or {}
                if result:
                    item["geo"] = result
                    enriched += 1
        self._save_cache()
        return enriched

    async def _request(self, client: httpx.AsyncClient, query: str) -> Optional[Dict[str, Any]]:
        wait_for = self.min_interval_seconds - (time.monotonic() - self._last_request_at)
        if wait_for > 0:
            await asyncio.sleep(wait_for)
        try:
            response = await client.get(
                self.endpoint,
                params={"q": query, "format": "jsonv2", "limit": 1, "addressdetails": 1},
            )
            response.raise_for_status()
            results = response.json()
            self._requests += 1
            self._last_request_at = time.monotonic()
            if not results:
                return None
            result = results[0]
            latitude = numeric_coordinate(result.get("lat"))
            longitude = numeric_coordinate(result.get("lon"))
            if latitude is None or longitude is None:
                return None
            return {
                "latitude": latitude,
                "longitude": longitude,
                "precision": self._precision(result.get("type")),
                "display_name": result.get("display_name"),
                "provider": "nominatim",
                "geocoded_at": datetime.now(timezone.utc).isoformat(),
            }
        except (httpx.HTTPError, ValueError, TypeError):
            return None

    @staticmethod
    def _address_query(item: Dict[str, Any], city: str, state: str) -> str:
        address = item.get("address") or {}
        address_parts = [address.get("street"), address.get("locality"), address.get("raw_text")]
        if not any(str(part or "").strip() for part in address_parts):
            return ""
        parts = [
            address.get("street"),
            address.get("locality"),
            address.get("raw_text"),
            city,
            state,
            "Brasil",
        ]
        values: List[str] = []
        for part in parts:
            value = str(part or "").strip()
            if value and value not in values:
                values.append(value)
        return ", ".join(values)

    @staticmethod
    def _precision(result_type: Optional[str]) -> str:
        if result_type in {"house", "building", "apartments", "residential"}:
            return "building"
        if result_type in {"road", "street"}:
            return "street"
        return "locality"

    @staticmethod
    def _normalize_existing_geo(item: Dict[str, Any]) -> bool:
        geo = item.get("geo") or {}
        latitude = numeric_coordinate(geo.get("latitude"))
        longitude = numeric_coordinate(geo.get("longitude"))
        if latitude is None or longitude is None:
            return False
        item["geo"] = {**geo, "latitude": latitude, "longitude": longitude}
        return True

    @staticmethod
    def _load_cache() -> Dict[str, Dict[str, Any]]:
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_cache(self) -> None:
        CACHE_PATH.parent.mkdir(exist_ok=True)
        CACHE_PATH.write_text(
            json.dumps(self._cache, ensure_ascii=False, indent=2), encoding="utf-8"
        )
