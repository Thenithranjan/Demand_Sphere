"""
Forecast Router
===============
REST API endpoints for the ForecastResults table.
Supports GET (list/detail/by-product), POST, PUT, DELETE with filtering.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas

router = APIRouter(
    prefix="/forecast",
    tags=["Forecast Results"],
    responses={404: {"description": "Forecast record not found"}},
)


# ---------------------------------------------------------------------------
# GET /forecast — List all forecast results
# ---------------------------------------------------------------------------
@router.get("/", response_model=schemas.PaginatedResponse)
def list_forecast_results(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    demand_level: Optional[str] = Query(
        None, description="Filter by demand level (High, Medium, Low)"
    ),
    db: Session = Depends(get_db),
):
    """Retrieve a paginated list of forecast results with optional filters."""
    total, items = crud.get_forecast_results(
        db, skip=skip, limit=limit, demand_level=demand_level
    )
    return schemas.PaginatedResponse(
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        items=[
            schemas.ForecastResultResponse.model_validate(item) for item in items
        ],
    )


# ---------------------------------------------------------------------------
# GET /forecast/product/{product_id} — Get forecasts for a product
# ---------------------------------------------------------------------------
@router.get(
    "/product/{product_id}",
    response_model=list[schemas.ForecastResultResponse],
)
def get_forecasts_by_product(product_id: str, db: Session = Depends(get_db)):
    """Retrieve all forecast results for a specific product."""
    results = crud.get_forecast_by_product(db, product_id)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No forecast results found for product '{product_id}'",
        )
    return results


# ---------------------------------------------------------------------------
# GET /forecast/{product_id} — Get dynamic demand forecast
# ---------------------------------------------------------------------------
@router.get(
    "/{product_id}",
    response_model=schemas.ForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Demand Forecast for Product",
    description=(
        "Retrieves a dynamic AI-powered demand forecast for the next month and next quarter.\n\n"
        "**AI Pipeline Logic:**\n"
        "- Loads the pre-trained XGBoost regressors (cached in memory) for quantity and revenue forecasting.\n"
        "- Feeds the historical monthly feature vectors for December 2025 (e.g. lag sales, season, festival tags).\n"
        "- Outputs the estimated quantity, projected revenue, and category-derived confidence rating.\n"
        "- Calculates next quarter projections based on category seasonality scaling factors."
    ),
)
def get_dynamic_forecast(
    product_id: str,
    db: Session = Depends(get_db),
):
    """
    HTTP GET endpoint for dynamic product demand forecasting.
    Defers business logic completely to the Service Layer.
    """
    from app.services import forecast_service
    return forecast_service.get_product_forecast(db, product_id)


# ---------------------------------------------------------------------------
# GET /forecast/{product_id}/{year_month} — Get forecast detail
# ---------------------------------------------------------------------------
@router.get("/{product_id}/{year_month}", response_model=schemas.ForecastResultResponse)
def get_forecast_result(product_id: str, year_month: str, db: Session = Depends(get_db)):
    """Retrieve a single forecast result by ProductID and YearMonth."""
    db_forecast = crud.get_forecast_result(db, product_id, year_month)
    if not db_forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast for product '{product_id}' and month '{year_month}' not found",
        )
    return db_forecast


# ---------------------------------------------------------------------------
# POST /forecast — Create a forecast result
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=schemas.ForecastResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_forecast_result(
    forecast: schemas.ForecastResultCreate,
    db: Session = Depends(get_db),
):
    """Create a new forecast result record."""
    return crud.create_forecast_result(db, forecast)


# ---------------------------------------------------------------------------
# PUT /forecast/{product_id}/{year_month} — Update a forecast result
# ---------------------------------------------------------------------------
@router.put("/{product_id}/{year_month}", response_model=schemas.ForecastResultResponse)
def update_forecast_result(
    product_id: str,
    year_month: str,
    forecast: schemas.ForecastResultUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing forecast result. Only provided fields are updated."""
    updated = crud.update_forecast_result(db, product_id, year_month, forecast)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast for product '{product_id}' and month '{year_month}' not found",
        )
    return updated


# ---------------------------------------------------------------------------
# DELETE /forecast/{product_id}/{year_month} — Delete a forecast result
# ---------------------------------------------------------------------------
@router.delete("/{product_id}/{year_month}", status_code=status.HTTP_204_NO_CONTENT)
def delete_forecast_result(product_id: str, year_month: str, db: Session = Depends(get_db)):
    """Delete a forecast result by ProductID and YearMonth."""
    deleted = crud.delete_forecast_result(db, product_id, year_month)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast for product '{product_id}' and month '{year_month}' not found",
        )
    return None
