"""
Inventory Optimization Service
==============================
Handles business logic for inventory monitoring and safety level alerting.
Integrates live inventory records with demand forecast predictions to generate
actionable restocking recommendations.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app import models

logger = logging.getLogger("inventory_service")

# ---------------------------------------------------------------------------
# Fast In-Memory Cache (TTL: 15 seconds)
# ---------------------------------------------------------------------------
_cached_inventory_data: Optional[List[Dict[str, Any]]] = None
_cache_timestamp: float = 0.0
CACHE_TTL_SECONDS: float = 15.0


def invalidate_inventory_cache() -> None:
    """Invalidate the inventory cache when inventory records are modified."""
    global _cached_inventory_data, _cache_timestamp
    _cached_inventory_data = None
    _cache_timestamp = 0.0


def get_inventory_optimization_data(
    db: Session,
    filter_alert: bool = False,
    filter_low_stock: bool = False,
    force_refresh: bool = False,
) -> List[Dict[str, Any]]:
    """
    Computes inventory optimization recommendations and alerts for all products.
    Uses an in-memory TTL cache to deliver responses in <1ms.
    """
    global _cached_inventory_data, _cache_timestamp

    now = time.time()
    if not force_refresh and _cached_inventory_data is not None and (now - _cache_timestamp) < CACHE_TTL_SECONDS:
        all_items = _cached_inventory_data
    else:
        # Query inventory eagerly joined with product
        inventory_items = db.query(models.Inventory).options(joinedload(models.Inventory.product)).all()
        if not inventory_items:
            return []

        # Bulk fetch latest forecast demand to prevent N+1 query overhead
        latest_ym = db.query(func.max(models.ForecastResult.YearMonth)).scalar()
        forecast_map: Dict[str, int] = {}
        if latest_ym:
            forecast_records = db.query(
                models.ForecastResult.ProductID, models.ForecastResult.Quantity
            ).filter(models.ForecastResult.YearMonth == latest_ym).all()
            forecast_map = {p_id: int(qty or 0) for p_id, qty in forecast_records}

        all_items = []
        for item in inventory_items:
            product = item.product
            if not product:
                continue

            # Get forecast demand from bulk map or fallback calculation
            forecast_demand = forecast_map.get(item.ProductID)
            if forecast_demand is None:
                forecast_demand = (item.ReorderPoint or 10) * 2

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

            all_items.append({
                "ProductID": item.ProductID,
                "ProductName": product.ProductName,
                "Warehouse": item.Warehouse,
                "CurrentStock": current,
                "SafetyStock": safety,
                "ReorderPoint": reorder,
                "ForecastDemand": forecast_demand,
                "Recommendation": recommendation,
                "_is_alert": current <= safety,
                "_is_low_stock": current <= reorder,
            })

        _cached_inventory_data = all_items
        _cache_timestamp = now

    # Filter in memory
    if filter_alert:
        filtered = [item for item in all_items if item["_is_alert"]]
    elif filter_low_stock:
        filtered = [item for item in all_items if item["_is_low_stock"]]
    else:
        filtered = all_items

    # Return clean dictionary list without internal flags
    return [
        {k: v for k, v in item.items() if not k.startswith("_")}
        for item in filtered
    ]
