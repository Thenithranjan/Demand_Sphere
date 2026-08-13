"""
Products Router
===============
REST API endpoints for the Products table.
Supports GET (list/detail), POST, PUT, DELETE with filtering and pagination.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    responses={404: {"description": "Product not found"}},
)


# ---------------------------------------------------------------------------
# GET /products — List all products
# ---------------------------------------------------------------------------
@router.get("/", response_model=schemas.PaginatedResponse)
def list_products(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    status: Optional[str] = Query(None, description="Filter by product status"),
    db: Session = Depends(get_db),
):
    """Retrieve a paginated list of products with optional filters."""
    total, items = crud.get_products(
        db, skip=skip, limit=limit, category=category, brand=brand, status=status
    )
    return schemas.PaginatedResponse(
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        items=[schemas.ProductResponse.model_validate(item) for item in items],
    )


# ---------------------------------------------------------------------------
# GET /products/{product_id} — Get product details
# ---------------------------------------------------------------------------
@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """Retrieve a single product by its ProductID."""
    db_product = crud.get_product(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found",
        )
    return db_product


# ---------------------------------------------------------------------------
# POST /products — Create a new product
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=schemas.ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
):
    """Create a new product record."""
    existing = crud.get_product(db, product.ProductID)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with ID '{product.ProductID}' already exists",
        )
    return crud.create_product(db, product)


# ---------------------------------------------------------------------------
# PUT /products/{product_id} — Update a product
# ---------------------------------------------------------------------------
@router.put("/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: str,
    product: schemas.ProductUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing product. Only provided fields will be updated."""
    updated = crud.update_product(db, product_id, product)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found",
        )
    return updated


# ---------------------------------------------------------------------------
# DELETE /products/{product_id} — Delete a product
# ---------------------------------------------------------------------------
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, db: Session = Depends(get_db)):
    """Delete a product by ProductID."""
    deleted = crud.delete_product(db, product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found",
        )
    return None
