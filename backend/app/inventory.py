"""
Inventory Helper Module
========================
Utility functions for inventory analysis, status checks, and alert generation.
Used by the inventory router for business-logic endpoints.
"""

from typing import Optional

from sqlalchemy.orm import Session

from . import models


def get_low_stock_items(db: Session, threshold: Optional[int] = None):
    """
    Retrieve products whose CurrentStock is at or below the ReorderPoint.
    Optionally override with a custom threshold.
    """
    query = db.query(models.Inventory)
    if threshold is not None:
        items = query.filter(
            models.Inventory.CurrentStock <= threshold
        ).all()
    else:
        items = query.filter(
            models.Inventory.CurrentStock <= models.Inventory.ReorderPoint
        ).all()
    return items


def get_overstock_items(db: Session):
    """
    Retrieve products whose CurrentStock exceeds MaximumStock.
    """
    return db.query(models.Inventory).filter(
        models.Inventory.CurrentStock > models.Inventory.MaximumStock
    ).all()


def get_inventory_summary(db: Session):
    """
    Generate a summary of inventory health across all warehouses.
    """
    from sqlalchemy import func

    total_items = db.query(func.count(models.Inventory.ProductID)).scalar()
    healthy = db.query(func.count(models.Inventory.ProductID)).filter(
        models.Inventory.InventoryStatus == "Healthy"
    ).scalar()
    reorder_required = db.query(func.count(models.Inventory.ProductID)).filter(
        models.Inventory.InventoryStatus == "Reorder Required"
    ).scalar()
    critical = db.query(func.count(models.Inventory.ProductID)).filter(
        models.Inventory.InventoryStatus == "Critical"
    ).scalar()
    overstock = db.query(func.count(models.Inventory.ProductID)).filter(
        models.Inventory.InventoryStatus == "Overstock"
    ).scalar()

    avg_utilisation = db.query(
        func.avg(models.Inventory.StockUtilisation)
    ).scalar()

    return {
        "total_items": total_items or 0,
        "healthy": healthy or 0,
        "reorder_required": reorder_required or 0,
        "critical": critical or 0,
        "overstock": overstock or 0,
        "average_utilisation": round(float(avg_utilisation or 0), 2),
    }
