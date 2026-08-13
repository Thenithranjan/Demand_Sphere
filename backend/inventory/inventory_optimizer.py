"""
==============================================================================
Inventory Optimizer Module: inventory_optimizer.py
==============================================================================
Why this file is needed:
    A supply chain optimization engine must synthesize raw stock status, demand
    predictions, and SCM rules into mathematical risk indicators and concrete purchase
    quantities. This module calculates the Suggested Purchase Quantity, predicts
    stockout timelines, and computes a multi-factor Inventory Risk Score to prioritize
    replenishment.

Business Calculations & Risk Score Logic:
    1. Suggested Purchase Quantity:
       - If stock is below ROP: Suggested Qty = OptimalOrderQuantity.
       - If High Demand Alert is active (forecast > current stock):
         Preemptive Qty = ForecastDemand - CurrentStock + SafetyStock.
       - Else: Suggested Qty = 0.

    2. Expected Stock After Reorder:
       CurrentStock + SuggestedPurchaseQuantity.

    3. Expected Days Until Stockout:
       Equal to the stock coverage days.

    4. Inventory Risk Score (0 to 100):
       - CurrentStock == 0: Score = 100 (Immediate Stockout).
       - CurrentStock <= SafetyStock: Score scales from 75 to 99.
       - CurrentStock <= ReorderPoint: Score scales from 40 to 74.
       - ForecastDemand > CurrentStock: Score scales from 25 to 39.
       - Healthy Range: Score scales from 0 to 24 (lower coverage increases score).
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

def calculate_suggested_purchase_qty(row: pd.Series) -> int:
    """
    Calculates the exact quantity to purchase based on current stock,
    reorder parameters, and forecasted demand surges.
    """
    curr = row.get("CurrentStock", 0)
    reorder = row.get("ReorderPoint", 0)
    opt_qty = row.get("OptimalOrderQuantity", 0)
    forecast = row.get("ForecastDemand", 0)
    safety = row.get("SafetyStock", 0)
    
    # Condition 1: Replenishment trigger reached
    if curr <= reorder:
        return int(opt_qty)
        
    # Condition 2: Preemptive buy due to upcoming demand spike
    if forecast > curr:
        shortfall = forecast - curr + safety
        return int(np.ceil(shortfall))
        
    # Condition 3: Stable inventory
    return 0

def calculate_inventory_risk_score(row: pd.Series) -> float:
    """
    Calculates a dynamic risk score between 0 and 100 representing stockout risk.
    """
    curr = float(row.get("CurrentStock", 0))
    safety = float(row.get("SafetyStock", 0))
    reorder = float(row.get("ReorderPoint", 0))
    forecast = float(row.get("ForecastDemand", 0))
    coverage = float(row.get("StockCoverageDays", 30))
    status = row.get("InventoryStatus", "Healthy Stock")
    
    # Case 1: Out of Stock
    if curr == 0:
        return 100.0
        
    # Case 2: Critical Stock (Safety buffer breached)
    # Scales linearly from 75 (at safety stock) up to 99 (near 0 stock)
    if curr <= safety and safety > 0:
        pct_breached = 1.0 - (curr / safety)
        return round(75.0 + (24.0 * pct_breached), 2)
        
    # Case 3: Low Stock (Reorder point breached)
    # Scales linearly from 40 (at reorder point) up to 74 (at safety stock boundary)
    if curr <= reorder:
        denominator = reorder - safety
        if denominator > 0:
            pct_breached = (reorder - curr) / denominator
            return round(40.0 + (34.0 * pct_breached), 2)
        return 40.0
        
    # Case 4: High Demand Warning (Forecast exceeds current stock)
    # Scales between 25 and 39 based on shortfall size
    if forecast > curr and forecast > 0:
        shortfall_pct = (forecast - curr) / forecast
        return round(25.0 + (14.0 * shortfall_pct), 2)
        
    # Case 5: Overstocked items (lower stockout risk, holding cost risk is separate)
    if status == "Overstock":
        return 5.0
        
    # Case 6: Healthy / Stable stock
    # Scales risk between 0 and 24 based on coverage days
    # (Lower coverage days increase stockout risk)
    if coverage > 0:
        risk_factor = min(1.0, 30.0 / coverage)  # High risk if coverage is below 30 days
        return round(risk_factor * 24.0, 2)
        
    return 0.0

def map_risk_level(score: float) -> str:
    """Categorises numerical risk scores into qualitative levels."""
    if score >= 75.0:
        return "Critical"
    elif score >= 40.0:
        return "High"
    elif score >= 20.0:
        return "Medium"
    return "Low"

def generate_optimized_recommendation(row: pd.Series) -> str:
    """
    Generates actionable business decisions by combining risk scores,
    suggested quantities, and status classifications.
    """
    risk_lvl = row.get("RiskLevel", "Low")
    suggested_qty = int(row.get("SuggestedPurchaseQuantity", 0))
    pname = row.get("ProductName", "Product")
    category = row.get("Category", "Apparel")
    subcategory = row.get("SubCategory", "")
    status = row.get("InventoryStatus", "Healthy Stock")
    
    category_label = subcategory if subcategory else category
    
    if risk_lvl == "Critical":
        return f"URGENT REORDER: Buy {suggested_qty} units of {category_label} {pname} immediately to restore safety buffer."
    elif risk_lvl == "High":
        return f"REORDER: Buy {suggested_qty} units of {category_label} {pname} to cover reorder shortage."
    elif risk_lvl == "Medium":
        return f"PREEMPTIVE BUY: Order {suggested_qty} units of {category_label} {pname} to cover forecasted demand spike."
    elif status == "Overstock":
        return f"HALT ORDERS: Do not order {pname}. Stock levels exceed maximum targets."
    return f"MAINTAIN: Stock level is healthy for {pname}."

def optimize_inventory_decisions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the mathematical optimizer calculations, risk scoring,
    and recommendations to the consolidated inventory dataset.
    """
    logger.info("Initializing inventory decision optimization algorithms...")
    res = df.copy()
    
    # 1. Suggested Purchase Quantity
    res["SuggestedPurchaseQuantity"] = res.apply(calculate_suggested_purchase_qty, axis=1)
    
    # 2. Expected Stock Level After Reorder
    res["ExpectedStockAfterReorder"] = res["CurrentStock"] + res["SuggestedPurchaseQuantity"]
    
    # 3. Expected Days Until Stockout (linked to Stock Coverage Days)
    res["ExpectedDaysUntilStockout"] = res["StockCoverageDays"]
    
    # 4. Inventory Risk Score
    res["InventoryRiskScore"] = res.apply(calculate_inventory_risk_score, axis=1)
    
    # 5. Categorical Risk Level mapping
    res["RiskLevel"] = res["InventoryRiskScore"].apply(map_risk_level)
    
    # 6. Optimized Recommendation text
    logger.info("Mapping finalized purchase recommendations...")
    res["Recommendation"] = res.apply(generate_optimized_recommendation, axis=1)
    
    # Audit logging
    risk_summary = res["RiskLevel"].value_counts().to_dict()
    total_suggested = int(res["SuggestedPurchaseQuantity"].sum())
    
    logger.info("Inventory optimization complete:")
    for lvl, count in risk_summary.items():
        logger.info(f"  Risk Level {lvl:<10}: {count} products")
    logger.info(f"  Total Suggested Purchase Volume: {total_suggested} units")
    
    return res

if __name__ == "__main__":
    from backend.inventory.inventory_service import get_integrated_inventory_state
    from backend.inventory.reorder_engine import compute_reorder_metrics
    from backend.inventory.stock_monitor import monitor_stock_levels
    
    state = get_integrated_inventory_state()
    enriched = compute_reorder_metrics(state)
    monitored = monitor_stock_levels(enriched)
    optimized = optimize_inventory_decisions(monitored)
    print(optimized[["ProductID", "ProductName", "SuggestedPurchaseQuantity", "InventoryRiskScore", "RiskLevel", "Recommendation"]].head(5))
