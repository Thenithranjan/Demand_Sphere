"""
==============================================================================
Stock Monitor Module: stock_monitor.py
==============================================================================
Why this file is needed:
    A stock monitor module implements real-time inventory tracking rules.
    It continuously categorises every SKU (Stock Keeping Unit) into risk-based
    status buckets (Out of Stock, Critical, Low, Healthy, Overstock) and checks
    if upcoming predicted demand spikes will exceed current stock levels, enabling
    proactive supply adjustments.

Business Rules & Logic Explained:
    1. Out of Stock (OOS):
       Condition: CurrentStock == 0.
       Impact: Sales are completely blocked. Immediate supplier check required.

    2. Critical Stock:
       Condition: 0 < CurrentStock <= SafetyStock.
       Impact: The safety buffer has been breached. Highly vulnerable to immediate stockouts.

    3. Low Stock:
       Condition: SafetyStock < CurrentStock <= ReorderPoint.
       Impact: The reorder point trigger is reached. Replenishment must be placed immediately.

    4. Overstock:
       Condition: CurrentStock > MaximumStock.
       Impact: Holding space and cash flow are excessively constrained.

    5. Healthy Stock:
       Condition: ReorderPoint < CurrentStock <= MaximumStock.
       Impact: Stable, balanced inventory alignment.

    6. High Demand Alert:
       Condition: ForecastDemand > CurrentStock.
       Impact: Next month's predicted sales exceed physical units in stock, flagging
               a high risk of stockout even if current levels are technically "healthy".
==============================================================================
"""

import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Set path relative to project root
INVENTORY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = INVENTORY_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.inventory import logger

def classify_stock_status(row: pd.Series) -> str:
    """
    Classifies the primary inventory risk status of a product based on stock levels.
    """
    curr = row.get("CurrentStock", 0)
    safety = row.get("SafetyStock", 0)
    reorder = row.get("ReorderPoint", 0)
    max_stock = row.get("MaximumStock", 0)
    
    # Rule 1: Out of Stock
    if curr == 0:
        return "Out of Stock"
        
    # Rule 2: Critical Stock (Safety stock buffer breached)
    if curr <= safety:
        return "Critical Stock"
        
    # Rule 3: Low Stock (Reorder point breached, but safety stock intact)
    if curr <= reorder:
        return "Low Stock"
        
    # Rule 4: Overstock (Exceeding max warehouse target)
    if curr > max_stock:
        return "Overstock"
        
    # Rule 5: Healthy Stock (Stable range)
    return "Healthy Stock"

def monitor_stock_levels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluates the complete dataset, applies classification status tags,
    and generates high demand warning flags.
    """
    logger.info("Running stock monitoring rules and safety limit audits...")
    res = df.copy()
    
    # 1. Apply primary status classification
    res["InventoryStatus"] = res.apply(classify_stock_status, axis=1)
    
    # 2. Derive High Demand Warning Alert flag
    # ForecastDemand represents predicted monthly sales. If it exceeds CurrentStock, flag True.
    res["HighDemandAlert"] = res["ForecastDemand"] > res["CurrentStock"]
    
    # Audit summary counts for logging
    status_counts = res["InventoryStatus"].value_counts().to_dict()
    high_demand_count = int(res["HighDemandAlert"].sum())
    
    logger.info("Stock monitor summary counts:")
    for status, count in status_counts.items():
        logger.info(f"  {status:<18}: {count} products")
    logger.info(f"  High Demand Alerts: {high_demand_count} products flagged")
    
    return res

if __name__ == "__main__":
    from backend.inventory.inventory_service import get_integrated_inventory_state
    from backend.inventory.reorder_engine import compute_reorder_metrics
    
    state = get_integrated_inventory_state()
    enriched = compute_reorder_metrics(state)
    monitored = monitor_stock_levels(enriched)
    print(monitored[["ProductID", "ProductName", "CurrentStock", "SafetyStock", "ReorderPoint", "InventoryStatus", "HighDemandAlert"]].head(5))
