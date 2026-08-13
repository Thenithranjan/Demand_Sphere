"""
Inventory Router
================
REST API endpoints for the Inventory table.
Supports GET (list/detail), POST, PUT, DELETE with filtering, pagination,
and business-logic endpoints (low stock alerts, summary).
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas
from ..inventory import get_low_stock_items, get_overstock_items, get_inventory_summary

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
    responses={404: {"description": "Inventory record not found"}},
)


# ---------------------------------------------------------------------------
# GET /inventory — List all inventory records
# ---------------------------------------------------------------------------
@router.get("/", response_model=schemas.PaginatedResponse)
def list_inventory(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by inventory status"
    ),
    warehouse: Optional[str] = Query(None, description="Filter by warehouse"),
    db: Session = Depends(get_db),
):
    """Retrieve a paginated list of inventory records with optional filters."""
    total, items = crud.get_all_inventory(
        db, skip=skip, limit=limit, status=status_filter, warehouse=warehouse
    )
    return schemas.PaginatedResponse(
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        items=[schemas.InventoryResponse.model_validate(item) for item in items],
    )


# ---------------------------------------------------------------------------
# GET /inventory/summary — Inventory health summary
# ---------------------------------------------------------------------------
@router.get("/summary")
def inventory_summary(db: Session = Depends(get_db)):
    """Get an aggregate summary of inventory health across all warehouses."""
    return get_inventory_summary(db)


# ---------------------------------------------------------------------------
# GET /inventory/low-stock — Low stock alerts
# ---------------------------------------------------------------------------
@router.get(
    "/low-stock",
    response_model=list[schemas.InventoryAlertResponse],
    summary="Get Low Stock Products",
    description=(
        "Retrieves a list of products whose CurrentStock is at or below their ReorderPoint.\n\n"
        "**AI Pipeline Logic:**\n"
        "- Compares current stock levels against safety and reorder targets.\n"
        "- Dynamically fetches next month forecast demand from XGBoost to predict if the stock will be depleted."
    ),
)
def low_stock_alerts(db: Session = Depends(get_db)):
    """Retrieve products that are at or below their reorder point."""
    from app.services import inventory_service
    return inventory_service.get_inventory_optimization_data(db, filter_low_stock=True)


# ---------------------------------------------------------------------------
# GET /inventory/alerts — Critical inventory alerts
# ---------------------------------------------------------------------------
@router.get(
    "/alerts",
    response_model=list[schemas.InventoryAlertResponse],
    summary="Get Critical Inventory Alerts",
    description=(
        "Retrieves critical stock alerts for items whose CurrentStock is at or below their SafetyStock.\n\n"
        "**AI Pipeline Logic:**\n"
        "- Marks items requiring urgent restocking to prevent stockouts."
    ),
)
def critical_alerts(db: Session = Depends(get_db)):
    """Retrieve critical stock level items."""
    from app.services import inventory_service
    return inventory_service.get_inventory_optimization_data(db, filter_alert=True)


# ---------------------------------------------------------------------------
# GET /inventory/recommendations — Restocking recommendations
# ---------------------------------------------------------------------------
@router.get(
    "/recommendations",
    response_model=list[schemas.InventoryAlertResponse],
    summary="Get Inventory Restocking Recommendations",
    description=(
        "Retrieves restocking recommendations for all products, merging current stock metrics, "
        "safety thresholds, and future forecast demand."
    ),
)
def inventory_recommendations(db: Session = Depends(get_db)):
    """Retrieve inventory recommendations for all items."""
    from app.services import inventory_service
    return inventory_service.get_inventory_optimization_data(db)


# ---------------------------------------------------------------------------
# GET /inventory/overstock — Overstock alerts
# ---------------------------------------------------------------------------
@router.get("/overstock", response_model=list[schemas.InventoryResponse])
def overstock_alerts(db: Session = Depends(get_db)):
    """Retrieve products whose stock exceeds their maximum threshold."""
    items = get_overstock_items(db)
    return items


# ---------------------------------------------------------------------------
# GET /inventory/{product_id} — Get inventory for a product
# ---------------------------------------------------------------------------
@router.get("/{product_id}", response_model=schemas.InventoryResponse)
def get_inventory(product_id: str, db: Session = Depends(get_db)):
    """Retrieve inventory details for a specific product."""
    db_inventory = crud.get_inventory(db, product_id)
    if not db_inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory record for product '{product_id}' not found",
        )
    return db_inventory


# ---------------------------------------------------------------------------
# POST /inventory — Create inventory record
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=schemas.InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory(
    inventory: schemas.InventoryCreate,
    db: Session = Depends(get_db),
):
    """Create a new inventory record for a product."""
    existing = crud.get_inventory(db, inventory.ProductID)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Inventory for product '{inventory.ProductID}' already exists",
        )
    return crud.create_inventory(db, inventory)


# ---------------------------------------------------------------------------
# PUT /inventory/{product_id} — Update inventory
# ---------------------------------------------------------------------------
@router.put("/{product_id}", response_model=schemas.InventoryResponse)
def update_inventory(
    product_id: str,
    inventory: schemas.InventoryUpdate,
    db: Session = Depends(get_db),
):
    """Update inventory for a product. Only provided fields will be updated."""
    updated = crud.update_inventory(db, product_id, inventory)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory record for product '{product_id}' not found",
        )
    return updated


# ---------------------------------------------------------------------------
# DELETE /inventory/{product_id} — Delete inventory record
# ---------------------------------------------------------------------------
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory(product_id: str, db: Session = Depends(get_db)):
    """Delete inventory record for a product."""
    deleted = crud.delete_inventory(db, product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory record for product '{product_id}' not found",
        )
    return None
