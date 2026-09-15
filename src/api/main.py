import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, status
from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import JSONResponse

from ..application.scrape_service import scrape_service
from ..db import (
    DatabaseUnavailable,
    ScrapeAlreadyRunning,
    get_property,
    list_properties,
)


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


class PropertyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    portal: str
    url: str
    title: str
    description: str
    price: Optional[Decimal] = None
    condominium_fee: Optional[Decimal] = None
    iptu_fee: Optional[Decimal] = None
    currency: str
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    suites: Optional[int] = None
    bathrooms: Optional[int] = None
    garages: Optional[int] = None
    useful_area_m2: Optional[Decimal] = None
    total_area_m2: Optional[Decimal] = None
    address: Dict[str, Any]
    geo: Dict[str, Any]
    advertiser: Dict[str, Any]
    amenities: List[Any]
    images: List[str]
    collected_at: Optional[datetime] = None
    first_seen_at: datetime
    last_seen_at: datetime


class PropertyListResponse(BaseModel):
    items: List[PropertyResponse]
    page: int
    page_size: int
    total: int


app = FastAPI(title="Canaan API", version="1.0.0")


@app.get("/health", tags=["system"])
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/api/v1/properties",
    response_model=PropertyListResponse,
    tags=["properties"],
)
async def read_properties(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    portal: Optional[str] = Query(default=None, min_length=1, max_length=80),
    city: Optional[str] = Query(default=None, min_length=1, max_length=120),
    neighborhood: Optional[str] = Query(default=None, min_length=1, max_length=120),
    price_max: Optional[float] = Query(default=None, ge=0),
    bedrooms_min: Optional[int] = Query(default=None, ge=0),
    min_lat: Optional[float] = Query(default=None, ge=-90, le=90),
    min_lon: Optional[float] = Query(default=None, ge=-180, le=180),
    max_lat: Optional[float] = Query(default=None, ge=-90, le=90),
    max_lon: Optional[float] = Query(default=None, ge=-180, le=180),
) -> PropertyListResponse:
    bbox_values = [min_lat, min_lon, max_lat, max_lon]
    if any(value is not None for value in bbox_values) and not all(
        value is not None for value in bbox_values
    ):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "invalid_bbox",
                    "message": "Informe min_lat, min_lon, max_lat e max_lon juntos",
                }
            },
        )

    result = await asyncio.to_thread(
        list_properties,
        page=page,
        page_size=page_size,
        portal=portal,
        city=city,
        neighborhood=neighborhood,
        price_max=price_max,
        bedrooms_min=bedrooms_min,
        bbox=tuple(bbox_values) if all(value is not None for value in bbox_values) else None,
    )
    return PropertyListResponse(
        items=result["items"], page=page, page_size=page_size, total=result["total"]
    )


@app.get(
    "/api/v1/properties/{property_id}",
    response_model=PropertyResponse,
    tags=["properties"],
    responses={404: {"model": ErrorResponse}},
)
async def read_property(property_id: int) -> PropertyResponse:
    property_data = await asyncio.to_thread(get_property, property_id)
    if property_data is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "property_not_found",
                    "message": "Imóvel não encontrado",
                }
            },
        )
    return PropertyResponse(**property_data)


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
