"""
Inventory Optimization Service
==============================
Handles business logic for inventory monitoring and safety level alerting.
Integrates live inventory records with demand forecast predictions to generate
actionable restocking recommendations.
"""

import logging
from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.services.forecast_service import get_product_forecast

logger = logging.getLogger("inventory_service")


def get_inventory_optimization_data(db: Session, filter_alert: bool = False, filter_low_stock: bool = False) -> List[Dict[str, Any]]:
    """
    Computes inventory optimization recommendations and alerts for all products.
    
    Logic:
        1. Query all inventory items and product metadata from MySQL.
        2. For each item, look up or calculate its next month forecast demand.
        3. Evaluate stock status:
            - If CurrentStock <= SafetyStock: "Restock Urgent" / "Reorder Immediately"
            - If CurrentStock <= ReorderPoint: "Reorder Immediately"
            - If CurrentStock > MaximumStock: "Promote/Discount"
            - Otherwise: "Maintain Stock"
        4. Apply filters for alerts (critical stock) or low-stock (below reorder point).
        5. Return list of recommendations.

    Args:
        db (Session): Database session context.
        filter_alert (bool): If True, returns only critical alerts (CurrentStock <= SafetyStock).
        filter_low_stock (bool): If True, returns only items needing reorder (CurrentStock <= ReorderPoint).

    Returns:
        List[Dict[str, Any]]: Optimized inventory list.
    """
    # Query inventory joined with product
    inventory_items = db.query(models.Inventory).all()
    if not inventory_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No inventory records found."
        )

    results = []
    for item in inventory_items:
        # Load product info
        product = item.product
        if not product:
            continue

        # Get forecast demand (next month quantity)
        try:
            forecast = get_product_forecast(db, item.ProductID)
            forecast_demand = forecast["next_month_quantity"]
        except Exception:
            # Fallback to a baseline if forecast fails
            forecast_demand = item.ReorderPoint * 2 if item.ReorderPoint else 20

        current = item.CurrentStock or 0
        safety = item.SafetyStock or 0
        reorder = item.ReorderPoint or 0
        max_stock = item.MaximumStock or 9999

        # Determine Recommendation
        if current <= safety:
            recommendation = "Reorder Immediately"
        elif current <= reorder:
            recommendation = "Reorder Immediately"
        elif current > max_stock or current > (forecast_demand * 3):
            recommendation = "Promote/Discount"
        else:
            recommendation = "Maintain Stock"

        # Apply filters
        is_alert = current <= safety
        is_low_stock = current <= reorder

        if filter_alert and not is_alert:
            continue
        if filter_low_stock and not is_low_stock:
            continue

        results.append({
            "ProductID": item.ProductID,
            "ProductName": product.ProductName,
            "Warehouse": item.Warehouse,
            "CurrentStock": current,
            "SafetyStock": safety,
            "ReorderPoint": reorder,
            "ForecastDemand": forecast_demand,
            "Recommendation": recommendation
        })

    return results
