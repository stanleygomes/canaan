from typing import Any, Dict

from fastapi import FastAPI, status
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import JSONResponse

from ..application.scrape_service import scrape_service
from ..db import DatabaseUnavailable, ScrapeAlreadyRunning


class ScrapeRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(default="all", min_length=1, max_length=80)


class ScrapeRunResponse(BaseModel):
    run_id: str
    source: str
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    properties_count: int | None = None
    error: str | None = None


class ErrorResponse(BaseModel):
    error: Dict[str, Any]


app = FastAPI(title="Canaan API", version="1.0.0")


@app.get("/health", tags=["system"])
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/v1/scrape-runs",
    response_model=ScrapeRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["scrape-runs"],
    responses={
        409: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def create_scrape_run(request: ScrapeRunRequest) -> ScrapeRunResponse:
    try:
        run = await scrape_service.start(request.source)
    except ScrapeAlreadyRunning as error:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": {"code": "scrape_already_running", "message": str(error)}},
        )
    except DatabaseUnavailable as error:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": {"code": "database_unavailable", "message": str(error)}},
        )
    return ScrapeRunResponse(**run.as_dict())


@app.get(
    "/api/v1/scrape-runs/{run_id}",
    response_model=ScrapeRunResponse,
    tags=["scrape-runs"],
    responses={404: {"model": ErrorResponse}},
)
async def get_scrape_run(run_id: str) -> ScrapeRunResponse:
    run = await scrape_service.get(run_id)
    if run is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "scrape_run_not_found",
                    "message": "Execução não encontrada",
                }
            },
        )
    return ScrapeRunResponse(**run.as_dict())
