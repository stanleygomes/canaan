import asyncio
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict

from ..db import (
    DatabaseUnavailable,
    ScrapeAlreadyRunning,
    ScrapeExecutionLock,
)
from ..search import run as run_scrape


@dataclass
class ScrapeRun:
    run_id: str
    source: str
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    properties_count: int | None = None
    error: str | None = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ScrapeService:
    def __init__(self) -> None:
        self._runs: Dict[str, ScrapeRun] = {}
        self._tasks: Dict[str, asyncio.Task[None]] = {}
        self._state_lock = asyncio.Lock()

    async def start(self, source: str = "all") -> ScrapeRun:
        async with self._state_lock:
            if any(run.status == "running" for run in self._runs.values()):
                raise ScrapeAlreadyRunning("Já existe uma execução em andamento")

            lock = ScrapeExecutionLock().acquire()
            run = ScrapeRun(run_id=str(uuid.uuid4()), source=source, status="running")
            run.started_at = self._now()
            self._runs[run.run_id] = run
            self._tasks[run.run_id] = asyncio.create_task(self._execute(run, lock))
            return run

    async def _execute(self, run: ScrapeRun, lock: ScrapeExecutionLock) -> None:
        try:
            properties = await run_scrape(run.source)
            run.properties_count = len(properties)
            run.status = "completed"
        except Exception as error:
            run.status = "failed"
            run.error = str(error)
        finally:
            run.finished_at = self._now()
            lock.close()
            self._tasks.pop(run.run_id, None)

    async def get(self, run_id: str) -> ScrapeRun | None:
        async with self._state_lock:
            return self._runs.get(run_id)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


scrape_service = ScrapeService()
