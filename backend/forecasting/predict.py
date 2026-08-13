"""
==============================================================================
Demand Forecasting Prediction Engine: predict.py
==============================================================================
Why this file exists:
    Training a model is useless unless we can deploy it to generate predictions.
    This file acts as our inference layer. It loads the saved XGBoost models,
    processes the feature vectors for the forecast period (January 2026),
    runs model prediction, projects monthly numbers to quarterly targets,
    and applies retail business rules to generate automated inventory recommendations.

ML Concepts:
    - Batch inference pipeline.
    - Category-based quarterly projection scaling.
    - Multi-source data merging for business decision logic.
==============================================================================
"""

import os
import sys
import logging
import joblib
from pathlib import Path
from typing import Tuple, Dict, Any, List
import pandas as pd
import numpy as np
from xgboost import XGBRegressor

# Set path relative to project root
FORECASTING_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FORECASTING_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.forecasting import DATA_DIR, MODELS_DIR, logger

def load_forecasting_models() -> Tuple[XGBRegressor, XGBRegressor]:
    """Loads saved XGBoost models for quantity and revenue forecasting."""
    qty_path = MODELS_DIR / "forecast_quantity_xgb.joblib"
    rev_path = MODELS_DIR / "forecast_revenue_xgb.joblib"
    
    if not qty_path.exists() or not rev_path.exists():
        raise FileNotFoundError("Trained forecasting models missing from backend/models/")
        
    qty_model = joblib.load(qty_path)
    rev_model = joblib.load(rev_path)
    return qty_model, rev_model

def get_quarterly_scaling_factors(sales_df: pd.DataFrame) -> Dict[str, float]:
    """
    Computes a quarterly scaling factor per Category from historical sales.
    The factor projects January sales to Q1 sales (Jan + Feb + Mar):
    Scaling Factor = (Jan + Feb + Mar sales) / Jan sales in historical data.
    """
    logger.info("Computing category-specific quarterly seasonal projection factors...")
    
    df = sales_df.copy()
    df["SaleDate"] = pd.to_datetime(df["SaleDate"])
    df["Month"] = df["SaleDate"].dt.month
    df["Year"] = df["SaleDate"].dt.year
    
    # We will use 2025 sales data to compute the Q1-to-Jan ratio
    df_25 = df[df["Year"] == 2025]
    if df_25.empty:
        df_25 = df # Fallback to all data if 2025 is empty
        
    # Group by category and month
    # First, join with products to get categories if not present in sales
    products_path = DATA_DIR / "products_clean.csv"
    products_df = pd.read_csv(products_path)
    df_25 = pd.merge(df_25, products_df[["ProductID", "Category"]], on="ProductID", how="left")
    
    monthly_sales = df_25.groupby(["Category", "Month"])["Quantity"].sum().reset_index()
    
    factors: Dict[str, float] = {}
    for cat in monthly_sales["Category"].unique():
        cat_df = monthly_sales[monthly_sales["Category"] == cat]
        
        jan_sales = cat_df[cat_df["Month"] == 1]["Quantity"].sum()
        feb_sales = cat_df[cat_df["Month"] == 2]["Quantity"].sum()
        mar_sales = cat_df[cat_df["Month"] == 3]["Quantity"].sum()
        
        if jan_sales > 0:
            q1_total = jan_sales + feb_sales + mar_sales
            factors[cat] = q1_total / jan_sales
        else:
            factors[cat] = 3.0  # Default fallback multiplier
            
    logger.info(f"Category quarterly scaling factors: {factors}")
    return factors

def generate_forecast_results(
    qty_model: XGBRegressor,
    rev_model: XGBRegressor,
    inference_df: pd.DataFrame,
    products_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    sales_df: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Executes model inference and generates aggregated predictions:
    1. Prepares features and runs the XGBoost models.
    2. Clips negative predictions to zero.
    3. Calculates Next Quarter projections based on category scaling factors.
    4. Merges current inventory levels to compute actionable inventory recommendations.
    5. Categorizes demand levels (High/Medium/Low) based on quantity percentiles.
    6. Aggregates predictions by Category and Brand.
    """
    logger.info("Running forecasting inference for next month (January 2026)...")
    
    # Feature columns aligned with train_model.py
    feature_cols = [
        "Year", "Month", "Quarter", "Week", "Day",
        "Category", "SubCategory", "Brand", "Price",
        "Quantity", "Revenue", "AveragePrice", "Season", "Festival"
    ]
    
    X_inf = inference_df[feature_cols]
    
    # Run predictions
    pred_qty = qty_model.predict(X_inf)
    pred_rev = rev_model.predict(X_inf)
    
    # Create prediction df
    results = pd.DataFrame({
        "ProductID": inference_df["ProductID"],
        "PredictedQuantity": np.clip(pred_qty, 0, None),  # Demand cannot be negative
        "PredictedRevenue": np.clip(pred_rev, 0, None)
    })
    
    # Standardise column format
    results["ForecastMonth"] = "2026-01"
    
    # Join product metadata
    results = pd.merge(
        results,
        products_df[["ProductID", "ProductName", "Category", "SubCategory", "Brand"]],
        on="ProductID",
        how="left"
    )
    
    # Compute quarterly scaling factors and apply them
    scaling_factors = get_quarterly_scaling_factors(sales_df)
    results["CategoryFactor"] = results["Category"].map(scaling_factors).fillna(3.0)
    results["PredictedQtyQuarter"] = results["PredictedQuantity"] * results["CategoryFactor"]
    results["PredictedRevQuarter"] = results["PredictedRevenue"] * results["CategoryFactor"]
    
    # Define Demand Level categories based on quantity percentiles
    qty_75 = results["PredictedQuantity"].quantile(0.75)
    qty_25 = results["PredictedQuantity"].quantile(0.25)
    
    def get_demand_level(q: float) -> str:
        if q >= qty_75:
            return "High"
        elif q <= qty_25:
            return "Low"
        return "Medium"
        
    results["DemandLevel"] = results["PredictedQuantity"].apply(get_demand_level)
    
    # Merge current stock details to generate recommendations
    logger.info("Merging current stock metrics to evaluate reorder requirements...")
    results = pd.merge(
        results,
        inventory_df[["ProductID", "CurrentStock", "ReorderPoint", "MaximumStock"]],
        on="ProductID",
        how="left"
    )
    
    # Generate recommendations using inventory business rules
    def get_recommendation(row: pd.Series) -> str:
        curr = row.get("CurrentStock", 0)
        reorder = row.get("ReorderPoint", 0)
        max_stock = row.get("MaximumStock", 9999)
        pred_q = row.get("PredictedQuantity", 0)
        
        # Scenario 1: Critical stock shortage
        if curr <= reorder or curr < pred_q:
            return "Restock Urgent"
        # Scenario 2: Overstocking hazard
        elif curr > max_stock or curr > (pred_q * 3):
            return "Promote/Discount"
        # Scenario 3: Healthy inventory balance
        return "Maintain Stock"
        
    results["Recommendation"] = results.apply(get_recommendation, axis=1)
    
    # 7. Aggregate predictions by Product, Category, and Brand
    # Product Level DataFrame (clean fields)
    product_forecast = results[[
        "ProductID", "ProductName", "ForecastMonth", 
        "PredictedQuantity", "PredictedRevenue", 
        "PredictedQtyQuarter", "PredictedRevQuarter", 
        "DemandLevel", "Recommendation"
    ]].copy()
    
    # Category Level Aggregation
    category_forecast = results.groupby("Category").agg(
        PredictedQuantity=("PredictedQuantity", "sum"),
        PredictedRevenue=("PredictedRevenue", "sum"),
        PredictedQtyQuarter=("PredictedQtyQuarter", "sum"),
        PredictedRevQuarter=("PredictedRevQuarter", "sum")
    ).reset_index()
    
    # Brand Level Aggregation
    brand_forecast = results.groupby("Brand").agg(
        PredictedQuantity=("PredictedQuantity", "sum"),
        PredictedRevenue=("PredictedRevenue", "sum"),
        PredictedQtyQuarter=("PredictedQtyQuarter", "sum"),
        PredictedRevQuarter=("PredictedRevQuarter", "sum")
    ).reset_index()
    
    # Category and Brand are already decoded via the products_df merge.
    aggregations = {
        "product": product_forecast,
        "category": category_forecast,
        "brand": brand_forecast
    }
    
    logger.info("Predictions and aggregations successfully generated.")
    return product_forecast, aggregations

if __name__ == "__main__":
    from backend.forecasting.prepare_data import prepare_forecasting_data, split_forecasting_data
    sales_df = pd.read_csv(DATA_DIR / "sales_clean.csv")
    products_df = pd.read_csv(DATA_DIR / "products_clean.csv")
    inventory_df = pd.read_csv(DATA_DIR / "inventory_clean.csv")
    
    grid, _ = prepare_forecasting_data()
    _, _, inference_df = split_forecasting_data(grid)
    
    qty_model, rev_model = load_forecasting_models()
    prod_fc, aggs = generate_forecast_results(
        qty_model, rev_model, inference_df, products_df, inventory_df, sales_df
    )
