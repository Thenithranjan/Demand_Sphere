"""
==============================================================================
Inventory Service Module: inventory_service.py
==============================================================================
Why this file is needed:
    In any inventory optimization system, you must establish a unified view of the
    operational state. This service acts as the data aggregator. It loads current
    stock statuses from the ERP database (inventory_clean.csv), demand forecasts
    from the ML pipeline (forecast_results.csv), and product metadata from the
    catalog (products_clean.csv) to compute core variables.

Business Calculations Explained:
    1. Current Stock: The physical units currently sitting on warehouse shelves.
    2. Forecast Demand: Predicted quantity expected to sell next month (from ML).
    3. Available Stock: Physically present units ready to satisfy orders.
    4. Safety Stock: Buffer inventory held to protect against shipping delays or spikes.
    5. Reorder Point: Stock level threshold that triggers replenishment orders.
    6. Lead Time: Number of days between placing a purchase order and receiving goods.
    7. Monthly Consumption: The average historical rate at which units are sold monthly.
==============================================================================
"""

import os
import sys
import logging
from pathlib import Path
from typing import Tuple
import pandas as pd

# Set path relative to project root
INVENTORY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = INVENTORY_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.inventory import DATA_DIR, logger

def load_raw_datasets() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads all necessary datasets for inventory service."""
    inventory_path = DATA_DIR / "inventory_clean.csv"
    forecast_path = PROJECT_ROOT / "forecast_results.csv"
    products_path = DATA_DIR / "products_clean.csv"
    sales_path = DATA_DIR / "sales_clean.csv"

    # Fail-fast check for file existence
    for path in [inventory_path, forecast_path, products_path, sales_path]:
        if not path.exists():
            raise FileNotFoundError(f"Required inventory/forecast dataset missing: {path}")

    logger.info("Loading cleaned inventory, products, sales, and forecast results datasets...")
    inventory_df = pd.read_csv(inventory_path)
    forecast_df = pd.read_csv(forecast_path)
    products_df = pd.read_csv(products_path)
    sales_df = pd.read_csv(sales_path)

    return inventory_df, forecast_df, products_df, sales_df

def calculate_monthly_consumption(sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates historical average Monthly Consumption for every product.
    This aggregates transaction quantities into monthly bins, then averages
    those monthly aggregates to compute the typical consumption rate.
    """
    logger.info("Calculating historical monthly consumption averages per product...")
    df = sales_df.copy()
    df["SaleDate"] = pd.to_datetime(df["SaleDate"])
    df["YearMonth"] = df["SaleDate"].dt.to_period("M")
    
    # 1. Group by product and calendar month to get sum of quantities sold
    monthly_sales = df.groupby(["ProductID", "YearMonth"])["Quantity"].sum().reset_index()
    
    # 2. Group by product and average the monthly quantities
    consumption_df = monthly_sales.groupby("ProductID")["Quantity"].mean().reset_index()
    consumption_df = consumption_df.rename(columns={"Quantity": "MonthlyConsumption"})
    
    return consumption_df

def get_integrated_inventory_state() -> pd.DataFrame:
    """
    Orchestrates data aggregation and creates the unified inventory state:
    1. Loads CSVs.
    2. Calculates historical monthly consumption rates.
    3. Standardises column names to prevent duplicate overlaps.
    4. Merges datasets on ProductID using left joins to maintain catalog records.
    5. Fills missing demand and consumption fields with zero indicators.
    """
    logger.info("Assembling unified inventory and demand dataset...")
    
    try:
        inventory_df, forecast_df, products_df, sales_df = load_raw_datasets()
        consumption_df = calculate_monthly_consumption(sales_df)
        
        # Standardise and rename columns to avoid name collisions
        forecast_subset = forecast_df[["ProductID", "PredictedQuantity", "Recommendation"]].rename(
            columns={
                "PredictedQuantity": "ForecastDemand",
                "Recommendation": "ForecastRecommendation"
            }
        )
        
        # Merge datasets (left joins on products to ensure complete catalog coverage)
        logger.info("Executing multi-table database joins...")
        merged_df = pd.merge(
            products_df[["ProductID", "ProductName", "Category", "SubCategory", "Brand", "Price", "CostPrice", "SupplierID"]],
            inventory_df[["ProductID", "Warehouse", "CurrentStock", "MinimumStock", "MaximumStock", "SafetyStock", "ReorderPoint", "LeadTimeDays"]],
            on="ProductID",
            how="left"
        )
        
        merged_df = pd.merge(merged_df, forecast_subset, on="ProductID", how="left")
        merged_df = pd.merge(merged_df, consumption_df, on="ProductID", how="left")
        
        # Fill missing values
        merged_df["ForecastDemand"] = merged_df["ForecastDemand"].fillna(0)
        merged_df["MonthlyConsumption"] = merged_df["MonthlyConsumption"].fillna(0)
        
        # Derive "Available Stock" (physically present and ready for sale)
        # Standard retail formula: Available = CurrentStock + OnOrder - Allocated
        # In our baseline environment, Available = CurrentStock
        merged_df["AvailableStock"] = merged_df["CurrentStock"]
        
        logger.info(f"Inventory integrated state compiled successfully. Shape: {merged_df.shape}")
        return merged_df
        
    except Exception as e:
        logger.error(f"Failed to integrate inventory datasets: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    state = get_integrated_inventory_state()
    # Print sample of the merged state
    print(state[["ProductID", "ProductName", "CurrentStock", "ForecastDemand", "SafetyStock", "MonthlyConsumption"]].head(5))
