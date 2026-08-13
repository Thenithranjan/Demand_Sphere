"""
Sales Router
=============
REST API endpoints for the Sales table.
Supports GET (list/detail), POST, PUT, DELETE with filtering and pagination.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas

router = APIRouter(
    prefix="/sales",
    tags=["Sales"],
    responses={404: {"description": "Sale not found"}},
)


# ---------------------------------------------------------------------------
# GET /sales — List all sales
# ---------------------------------------------------------------------------
@router.get("/", response_model=schemas.PaginatedResponse)
def list_sales(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
    product_id: Optional[str] = Query(None, description="Filter by product"),
    festival: Optional[str] = Query(None, description="Filter by festival"),
    season: Optional[str] = Query(None, description="Filter by season"),
    db: Session = Depends(get_db),
):
    """Retrieve a paginated list of sales with optional filters."""
    total, items = crud.get_sales(
        db,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        product_id=product_id,
        festival=festival,
        season=season,
    )
    return schemas.PaginatedResponse(
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        items=[schemas.SaleResponse.model_validate(item) for item in items],
    )


# ---------------------------------------------------------------------------
# GET /sales/{sale_id} — Get sale details
# ---------------------------------------------------------------------------
@router.get("/{sale_id}", response_model=schemas.SaleResponse)
def get_sale(sale_id: str, db: Session = Depends(get_db)):
    """Retrieve a single sale by SaleID."""
    db_sale = crud.get_sale(db, sale_id)
    if not db_sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sale with ID '{sale_id}' not found",
        )
    return db_sale


# ---------------------------------------------------------------------------
# POST /sales — Create a new sale
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=schemas.SaleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sale(
    sale: schemas.SaleCreate,
    db: Session = Depends(get_db),
):
    """Create a new sale record."""
    existing = crud.get_sale(db, sale.SaleID)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sale with ID '{sale.SaleID}' already exists",
        )
    return crud.create_sale(db, sale)


# ---------------------------------------------------------------------------
# PUT /sales/{sale_id} — Update a sale
# ---------------------------------------------------------------------------
@router.put("/{sale_id}", response_model=schemas.SaleResponse)
def update_sale(
    sale_id: str,
    sale: schemas.SaleUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing sale. Only provided fields will be updated."""
    updated = crud.update_sale(db, sale_id, sale)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sale with ID '{sale_id}' not found",
        )
    return updated


# ---------------------------------------------------------------------------
# DELETE /sales/{sale_id} — Delete a sale
# ---------------------------------------------------------------------------
@router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sale(sale_id: str, db: Session = Depends(get_db)):
    """Delete a sale by SaleID."""
    deleted = crud.delete_sale(db, sale_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sale with ID '{sale_id}' not found",
        )
    return None
