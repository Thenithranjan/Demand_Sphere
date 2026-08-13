"""
Suppliers Router
================
REST API endpoints for the Suppliers table.
Supports GET (list/detail), POST, PUT, DELETE with filtering and pagination.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas

router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
    responses={404: {"description": "Supplier not found"}},
)


# ---------------------------------------------------------------------------
# GET /suppliers — List all suppliers
# ---------------------------------------------------------------------------
@router.get("/", response_model=schemas.PaginatedResponse)
def list_suppliers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by supplier status"
    ),
    db: Session = Depends(get_db),
):
    """Retrieve a paginated list of suppliers with optional filters."""
    total, items = crud.get_suppliers(
        db, skip=skip, limit=limit, status=status_filter
    )
    return schemas.PaginatedResponse(
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        items=[schemas.SupplierResponse.model_validate(item) for item in items],
    )


# ---------------------------------------------------------------------------
# GET /suppliers/{supplier_id} — Get supplier details
# ---------------------------------------------------------------------------
@router.get("/{supplier_id}", response_model=schemas.SupplierResponse)
def get_supplier(supplier_id: str, db: Session = Depends(get_db)):
    """Retrieve a single supplier by SupplierID."""
    db_supplier = crud.get_supplier(db, supplier_id)
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID '{supplier_id}' not found",
        )
    return db_supplier


# ---------------------------------------------------------------------------
# POST /suppliers — Create a new supplier
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=schemas.SupplierResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_supplier(
    supplier: schemas.SupplierCreate,
    db: Session = Depends(get_db),
):
    """Create a new supplier record."""
    existing = crud.get_supplier(db, supplier.SupplierID)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Supplier with ID '{supplier.SupplierID}' already exists",
        )
    return crud.create_supplier(db, supplier)


# ---------------------------------------------------------------------------
# PUT /suppliers/{supplier_id} — Update a supplier
# ---------------------------------------------------------------------------
@router.put("/{supplier_id}", response_model=schemas.SupplierResponse)
def update_supplier(
    supplier_id: str,
    supplier: schemas.SupplierUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing supplier. Only provided fields will be updated."""
    updated = crud.update_supplier(db, supplier_id, supplier)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID '{supplier_id}' not found",
        )
    return updated


# ---------------------------------------------------------------------------
# DELETE /suppliers/{supplier_id} — Delete a supplier
# ---------------------------------------------------------------------------
@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(supplier_id: str, db: Session = Depends(get_db)):
    """Delete a supplier by SupplierID."""
    deleted = crud.delete_supplier(db, supplier_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID '{supplier_id}' not found",
        )
    return None
