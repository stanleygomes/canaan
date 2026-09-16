"""Controle de ritmo e retries das navegações dos scrapers."""

from __future__ import annotations

import asyncio
import os
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import monotonic
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import Page, Response

from ..logger import logger


RETRYABLE_STATUS_CODES = frozenset({403, 408, 425, 429, 500, 502, 503, 504})
DEFAULT_TIMEOUT_MS = 45_000


@dataclass(frozen=True)
class RateLimitSettings:
    min_interval_seconds: float = 3.0
    jitter_seconds: float = 1.0
    max_retries: int = 3
    backoff_seconds: float = 5.0

    @classmethod
    def from_environment(cls) -> "RateLimitSettings":
        return cls(
            min_interval_seconds=max(0.0, float(os.getenv("SCRAPE_MIN_INTERVAL_SECONDS", "3"))),
            jitter_seconds=max(0.0, float(os.getenv("SCRAPE_JITTER_SECONDS", "1"))),
            max_retries=max(0, int(os.getenv("SCRAPE_MAX_RETRIES", "3"))),
            backoff_seconds=max(0.0, float(os.getenv("SCRAPE_BACKOFF_SECONDS", "5"))),
        )


class ScrapeRateLimiter:
    """Aplica intervalo mínimo por domínio e evita rajadas de requisições."""

    def __init__(self, settings: RateLimitSettings | None = None):
        self.settings = settings or RateLimitSettings.from_environment()
        self._last_request_at: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def wait_for_slot(self, url: str, portal: str) -> None:
        domain = urlparse(url).netloc or portal
        async with self._lock:
            elapsed = monotonic() - self._last_request_at.get(domain, 0.0)
            interval = self.settings.min_interval_seconds + random.uniform(0, self.settings.jitter_seconds)
            delay = max(0.0, interval - elapsed)
            if delay:
                logger.info("⏳ Rate limit: aguardando {:.1f}s antes de acessar {}", delay, domain)
                await asyncio.sleep(delay)
            self._last_request_at[domain] = monotonic()

    async def backoff(self, attempt: int, response: Response | None, portal: str) -> None:
        retry_after = self._retry_after_seconds(response)
        delay = retry_after if retry_after is not None else self.settings.backoff_seconds * (2 ** (attempt - 1))
        delay += random.uniform(0, self.settings.jitter_seconds)
        logger.warning("🔁 Retry {}/{} para {} em {:.1f}s", attempt, self.settings.max_retries, portal, delay)
        await asyncio.sleep(delay)

    @staticmethod
    def _retry_after_seconds(response: Response | None) -> float | None:
        if response is None:
            return None
        value = response.headers.get("retry-after")
        if not value:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(value)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                return None


rate_limiter = ScrapeRateLimiter()


async def navigate_with_rate_limit(
    page: Page,
    url: str,
    portal: str,
    **navigation_options: Any,
) -> Response | None:
    """Navega com intervalo por domínio e retry para bloqueios/erros transitórios."""
    navigation_options.setdefault("wait_until", "domcontentloaded")
    navigation_options.setdefault("timeout", DEFAULT_TIMEOUT_MS)

    for attempt in range(rate_limiter.settings.max_retries + 1):
        await rate_limiter.wait_for_slot(url, portal)
        response: Response | None = None
        try:
            response = await page.goto(url, **navigation_options)
            status = response.status if response else None
            if status not in RETRYABLE_STATUS_CODES:
                return response
            logger.warning("⚠️ {} respondeu HTTP {}: {}", portal, status, url)
        except Exception as error:
            if attempt >= rate_limiter.settings.max_retries:
                raise
            logger.warning("⚠️ Falha transitória ao acessar {}: {}", portal, error)

        if attempt >= rate_limiter.settings.max_retries:
            status = response.status if response else "sem resposta"
            raise RuntimeError(f"{portal} excedeu retries ao acessar {url} ({status})")
        await rate_limiter.backoff(attempt + 1, response, portal)

    raise RuntimeError(f"Navegação não concluída: {url}")
