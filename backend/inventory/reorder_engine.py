"""
==============================================================================
Reorder Engine Module: reorder_engine.py
==============================================================================
Why this file is needed:
    A reorder engine implements SCM (Supply Chain Management) decision logic.
    Instead of managers guessing how much to buy, this engine calculates the
    mathematically optimal order size (EOQ) and stock coverage intervals, preventing
    under-purchasing (which causes stockouts) and over-purchasing (which wastes capital).

SCM Formulas and Explanations:
    1. Economic Order Quantity (EOQ):
       EOQ = sqrt(2 * D * S / H)
       Minimises total inventory costs (Setup costs + Holding costs).
       - D (Annual Demand): Monthly forecast demand multiplied by 12.
       - S (Setup/Ordering Cost): Fixed administrative cost per order (e.g. ₹500).
       - H (Holding Cost): Cost of holding 1 unit in stock for 1 year.
         Calculated as carrying cost rate (e.g. 20%) * CostPrice.

    2. Stock Coverage (Days):
       Stock Coverage = (Current Stock / Monthly Forecast Demand) * 30 days.
       Indicates how long the current inventory will last at the predicted sales rate.

    3. Inventory Turnover:
       Inventory Turnover = Annual Demand / Average Stock.
       Where Average Stock = Safety Stock + (EOQ / 2).
       Measures how many times the average inventory is sold and replaced per year.
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

# Business Constants (No hardcoded values)
ORDERING_SETUP_COST: float = 500.0  # S: Administrative and transport setup cost per purchase order (₹)
CARRYING_COST_RATE: float = 0.20    # H rate: 20% annual holding cost rate on unit cost price
DEFAULT_HOLDING_MIN: float = 1.0    # Fallback to prevent divide-by-zero for extremely cheap products

def calculate_eoq(forecast_demand: float, cost_price: float) -> int:
    """
    Calculates the Economic Order Quantity (EOQ).
    """
    annual_demand = forecast_demand * 12.0
    
    # Calculate holding cost (Carrying rate * unit cost price)
    holding_cost = cost_price * CARRYING_COST_RATE
    holding_cost = max(holding_cost, DEFAULT_HOLDING_MIN)  # Prevent division by zero
    
    # EOQ formula: sqrt(2 * D * S / H)
    eoq_value = np.sqrt((2.0 * annual_demand * ORDERING_SETUP_COST) / holding_cost)
    
    # Return as integer (must order whole units)
    return int(np.round(eoq_value))

def calculate_stock_coverage(current_stock: float, forecast_demand: float, monthly_consumption: float) -> float:
    """
    Calculates Stock Coverage in Days.
    If forecast demand is 0, falls back to historical monthly consumption.
    If both are 0, returns a maximum default coverage (e.g. 999 days).
    """
    demand_rate = forecast_demand if forecast_demand > 0 else monthly_consumption
    
    if demand_rate <= 0:
        return 999.0  # Stock will last indefinitely as there is zero demand
        
    coverage_months = current_stock / demand_rate
    return round(coverage_months * 30.0, 1)

def calculate_inventory_turnover(forecast_demand: float, safety_stock: float, eoq: float) -> float:
    """
    Calculates expected Inventory Turnover Ratio.
    Average Stock = Safety Stock + (EOQ / 2)
    Turnover = Annual Demand / Average Stock
    """
    annual_demand = forecast_demand * 12.0
    avg_stock = safety_stock + (eoq / 2.0)
    
    if avg_stock <= 0:
        return 0.0
        
    return round(annual_demand / avg_stock, 2)

def generate_reorder_recommendation(row: pd.Series) -> str:
    """
    Generates actionable business reorder recommendations based on stock level.
    """
    product_name = row.get("ProductName", "Unknown Product")
    category = row.get("Category", "Product")
    subcategory = row.get("SubCategory", "")
    curr_stock = row.get("CurrentStock", 0)
    reorder_point = row.get("ReorderPoint", 0)
    max_stock = row.get("MaximumStock", 0)
    opt_qty = row.get("OptimalOrderQuantity", 0)
    forecast = row.get("ForecastDemand", 0)
    
    # Formatting helper for display categories
    category_label = subcategory if subcategory else category

    # Rule 1: Replenishment is triggered
    if curr_stock <= reorder_point:
        return f"Order {opt_qty} {category_label} {product_name}"
        
    # Rule 2: High Demand warning
    if forecast > curr_stock:
        return f"Increase {category_label} stock (High Forecast Demand)"
        
    # Rule 3: Excess Inventory holding warning
    if curr_stock > max_stock:
        return f"Do not reorder {product_name} (Overstocked)"
        
    # Default Rule: Healthy stable stock
    return f"Maintain stock levels for {product_name}"

def compute_reorder_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches the integrated inventory dataframe with reorder and optimal ordering metrics.
    """
    logger.info("Computing SCM reorder optimization metrics (EOQ, Stock Coverage, Turnover)...")
    res = df.copy()
    
    # 1. Calculate EOQ per product
    res["EOQ"] = res.apply(lambda r: calculate_eoq(r["ForecastDemand"], r["CostPrice"]), axis=1)
    
    # 2. Calculate Stock Coverage in Days
    res["StockCoverageDays"] = res.apply(
        lambda r: calculate_stock_coverage(r["CurrentStock"], r["ForecastDemand"], r["MonthlyConsumption"]), 
        axis=1
    )
    
    # 3. Calculate expected Inventory Turnover
    res["InventoryTurnover"] = res.apply(
        lambda r: calculate_inventory_turnover(r["ForecastDemand"], r["SafetyStock"], r["EOQ"]), 
        axis=1
    )
    
    # 4. Map Buffer Stock (Buffer Stock is Safety Stock held as a safety margin)
    res["BufferStock"] = res["SafetyStock"]
    
    # 5. Calculate Reorder Quantity and Optimal Order Quantity
    # Reorder Quantity: EOQ if replenishment is triggered, else 0
    res["ReorderQuantity"] = np.where(res["CurrentStock"] <= res["ReorderPoint"], res["EOQ"], 0)
    
    # Optimal Order Quantity: Max of EOQ or the difference to reach Max Stock level if triggered
    res["OptimalOrderQuantity"] = np.where(
        res["CurrentStock"] <= res["ReorderPoint"],
        np.maximum(res["EOQ"], res["MaximumStock"] - res["CurrentStock"]),
        0
    )
    # Ensure OptimalOrderQuantity is integer type
    res["OptimalOrderQuantity"] = res["OptimalOrderQuantity"].astype(int)
    
    # 6. Generate text recommendation strings
    logger.info("Generating text reorder recommendations...")
    res["Recommendation"] = res.apply(generate_reorder_recommendation, axis=1)
    
    return res

if __name__ == "__main__":
    from backend.inventory.inventory_service import get_integrated_inventory_state
    state = get_integrated_inventory_state()
    enriched = compute_reorder_metrics(state)
    print(enriched[["ProductID", "ProductName", "EOQ", "StockCoverageDays", "InventoryTurnover", "Recommendation"]].head(5))
