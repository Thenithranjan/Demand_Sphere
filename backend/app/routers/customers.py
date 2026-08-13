"""
Customers Router
================
REST API endpoints for the Customers table.
Supports GET (list/detail), POST, PUT, DELETE with filtering and pagination.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
    responses={404: {"description": "Customer not found"}},
)


# ---------------------------------------------------------------------------
# GET /customers — List all customers
# ---------------------------------------------------------------------------
@router.get("/", response_model=schemas.PaginatedResponse)
def list_customers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    membership: Optional[str] = Query(None, description="Filter by membership tier"),
    city: Optional[str] = Query(None, description="Filter by city"),
    db: Session = Depends(get_db),
):
    """Retrieve a paginated list of customers with optional filters."""
    total, items = crud.get_customers(
        db, skip=skip, limit=limit, membership=membership, city=city
    )
    return schemas.PaginatedResponse(
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        items=[schemas.CustomerResponse.model_validate(item) for item in items],
    )


# ---------------------------------------------------------------------------
# GET /customers/{customer_id} — Get customer details
# ---------------------------------------------------------------------------
@router.get("/{customer_id}", response_model=schemas.CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """Retrieve a single customer by their CustomerID."""
    db_customer = crud.get_customer(db, customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found",
        )
    return db_customer


# ---------------------------------------------------------------------------
# POST /customers — Create a new customer
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=schemas.CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
):
    """Create a new customer record."""
    existing = crud.get_customer(db, customer.CustomerID)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer with ID '{customer.CustomerID}' already exists",
        )
    return crud.create_customer(db, customer)


# ---------------------------------------------------------------------------
# PUT /customers/{customer_id} — Update a customer
# ---------------------------------------------------------------------------
@router.put("/{customer_id}", response_model=schemas.CustomerResponse)
def update_customer(
    customer_id: str,
    customer: schemas.CustomerUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing customer. Only provided fields will be updated."""
    updated = crud.update_customer(db, customer_id, customer)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found",
        )
    return updated


# ---------------------------------------------------------------------------
# DELETE /customers/{customer_id} — Delete a customer
# ---------------------------------------------------------------------------
@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: str, db: Session = Depends(get_db)):
    """Delete a customer by CustomerID."""
    deleted = crud.delete_customer(db, customer_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found",
        )
    return None
