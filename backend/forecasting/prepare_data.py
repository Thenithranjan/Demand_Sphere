"""
==============================================================================
Demand Forecasting Data Preparation: prepare_data.py
==============================================================================
Why this file exists:
    Data preparation is the foundation of any Machine Learning project. Time-series
    forecasting requires aggregating raw transactional logs (which occur at arbitrary
    times) into regular time steps (monthly buckets) and aligning features at time 't'
    with targets at time 't+1'.

ML Concepts:
    - Cartesian grid generation to resolve Sample Selection Bias (zero-sales months).
    - Auto-regressive target shifting.
    - Chronological data splitting to prevent Temporal Data Leakage.
    - Categorical label mapping using Ordinal Encoding.
==============================================================================
"""

import os
import sys
import logging
import joblib
from pathlib import Path
from typing import Tuple, Dict, List
import pandas as pd
import numpy as np
from sklearn.preprocessing import OrdinalEncoder

# Set path relative to project root
FORECASTING_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FORECASTING_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.forecasting import DATA_DIR, MODELS_DIR, logger

# Month-to-metadata maps derived from transaction history
MONTH_TO_SEASON = {
    1: 'Winter', 2: 'Winter', 3: 'Summer', 4: 'Summer', 5: 'Summer', 
    6: 'Monsoon', 7: 'Monsoon', 8: 'Monsoon', 9: 'Monsoon', 
    10: 'Winter', 11: 'Winter', 12: 'Winter'
}
MONTH_TO_FESTIVAL = {
    1: 'Pongal', 2: 'Regular', 3: 'Summer', 4: 'Summer', 5: 'Summer', 
    6: 'School Season', 7: 'Aadi Sale', 8: 'Independence Day', 9: 'Regular', 
    10: 'Navratri', 11: 'Diwali', 12: 'Wedding Season'
}

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Loads cleaned sales and products datasets."""
    sales_path = DATA_DIR / "sales_clean.csv"
    products_path = DATA_DIR / "products_clean.csv"
    
    if not sales_path.exists() or not products_path.exists():
        raise FileNotFoundError("Cleaned sales and products files must exist in data/processed/")
        
    sales_df = pd.read_csv(sales_path)
    products_df = pd.read_csv(products_path)
    return sales_df, products_df

def prepare_forecasting_data() -> Tuple[pd.DataFrame, Dict[str, OrdinalEncoder]]:
    """
    Main preprocessing pipeline:
    1. Loads datasets.
    2. Builds a complete Product x Month grid.
    3. Aggregates monthly transactions, mapping missing intervals to zero (zero-filling).
    4. Aligns temporal features and shifts targets (TargetQuantity/TargetRevenue for month t+1).
    5. Encodes categorical attributes.
    6. Saves clean forecasting features CSV and encoders joblib.
    """
    logger.info("Initializing demand forecasting data preparation...")
    sales_df, products_df = load_data()
    
    # 1. Standardise sales dates to monthly periods
    sales_df["SaleDate"] = pd.to_datetime(sales_df["SaleDate"])
    sales_df["YearMonth"] = sales_df["SaleDate"].dt.to_period("M")
    
    # Identify complete date range in dataset
    all_months = pd.period_range(
        start=sales_df["YearMonth"].min(),
        end=sales_df["YearMonth"].max(),
        freq="M"
    )
    all_product_ids = products_df["ProductID"].unique()
    
    logger.info(f"Detected {len(all_months)} months and {len(all_product_ids)} unique products.")
    
    # 2. Generate Cartesian Product Grid (Product x Month) to resolve sample selection bias
    logger.info("Generating full Cartesian Product grid for products and calendar months...")
    grid_index = pd.MultiIndex.from_product(
        [all_product_ids, all_months],
        names=["ProductID", "YearMonth"]
    )
    grid_df = pd.DataFrame(index=grid_index).reset_index()
    
    # 3. Aggregate transaction sales per product-month
    logger.info("Aggregating sales quantities and revenues...")
    agg_sales = sales_df.groupby(["ProductID", "YearMonth"]).agg(
        Quantity=("Quantity", "sum"),
        Revenue=("FinalPrice", "sum")
    ).reset_index()
    
    # Join aggregated sales into complete grid
    grid_df = pd.merge(grid_df, agg_sales, on=["ProductID", "YearMonth"], how="left")
    
    # Fill sales gaps with zero-values (essential for zero-demand periods)
    grid_df["Quantity"] = grid_df["Quantity"].fillna(0)
    grid_df["Revenue"] = grid_df["Revenue"].fillna(0)
    
    # Join product metadata (Category, SubCategory, Brand, base Price)
    grid_df = pd.merge(
        grid_df, 
        products_df[["ProductID", "Category", "SubCategory", "Brand", "Price"]], 
        on="ProductID", 
        how="left"
    )
    
    # 4. Engineer temporal, average selling price, and seasonal metrics
    grid_df["Year"] = grid_df["YearMonth"].dt.year
    grid_df["Month"] = grid_df["YearMonth"].dt.month
    grid_df["Quarter"] = grid_df["YearMonth"].dt.quarter
    grid_df["Week"] = 1 # Approximation for aggregated monthly data (set to first week of the month)
    grid_df["Day"] = 1  # Standard monthly boundary representation
    
    # Compute Average Selling Price: (Revenue / Quantity) or default to product baseline Price if no sales
    grid_df["AveragePrice"] = np.where(
        grid_df["Quantity"] > 0,
        grid_df["Revenue"] / grid_df["Quantity"],
        grid_df["Price"]
    )
    
    # Map seasons and festivals based on calendar month
    grid_df["Season"] = grid_df["Month"].map(MONTH_TO_SEASON)
    grid_df["Festival"] = grid_df["Month"].map(MONTH_TO_FESTIVAL)
    
    # Sort data chronologically per product
    grid_df = grid_df.sort_values(by=["ProductID", "YearMonth"]).reset_index(drop=True)
    
    # 5. Shifting Target Variables (Align features at t with sales/revenue targets at t+1)
    logger.info("Generating target variables (Future Monthly Quantity and Revenue)...")
    grid_df["TargetQuantity"] = grid_df.groupby("ProductID")["Quantity"].shift(-1)
    grid_df["TargetRevenue"] = grid_df.groupby("ProductID")["Revenue"].shift(-1)
    
    # 6. Categorical Encoding
    logger.info("Encoding categorical variables...")
    categorical_cols = ["Category", "SubCategory", "Brand", "Season", "Festival"]
    encoders: Dict[str, OrdinalEncoder] = {}
    
    for col in categorical_cols:
        encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        # Reshape to 2D array for fit_transform
        grid_df[col] = encoder.fit_transform(grid_df[[col]])
        encoders[col] = encoder
        
    # Save encoders to disk for inference model preprocessing
    encoders_path = MODELS_DIR / "forecasting_encoders.joblib"
    joblib.dump(encoders, encoders_path)
    logger.info(f"Saved categorical encoders -> {encoders_path}")
    
    # Save full processed dataset
    dataset_path = DATA_DIR / "forecasting_features.csv"
    
    # Convert Period to string format for saving
    grid_df_save = grid_df.copy()
    grid_df_save["YearMonth"] = grid_df_save["YearMonth"].astype(str)
    grid_df_save.to_csv(dataset_path, index=False)
    logger.info(f"Saved forecasting features -> {dataset_path}")
    
    return grid_df, encoders

def split_forecasting_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits the aggregated dataset chronologically:
    1. Inference Set: The final month (December 2025), where the targets (January 2026 sales) are NaN.
    2. Training & Testing Pool: All rows where targets are known.
       - Train Set: Jan 2024 to June 2025 (first 18 months).
       - Test Set: July 2025 to Nov 2025 (subsequent 5 months).
    """
    logger.info("Splitting dataset into chronological training, validation, and inference partitions...")
    
    # Separate Inference Set (Future Predict Pool)
    inference_mask = df["TargetQuantity"].isna()
    inference_df = df[inference_mask].copy()
    
    # Historical pool with known targets
    history_df = df[~inference_mask].copy()
    
    # Define chronological split boundary
    # Training: Jan 2024 (2024-01) to June 2025 (2025-06)
    # Testing: July 2025 (2025-07) to Nov 2025 (2025-11)
    split_period = pd.Period("2025-06", freq="M")
    
    train_df = history_df[history_df["YearMonth"] <= split_period].copy()
    test_df = history_df[history_df["YearMonth"] > split_period].copy()
    
    logger.info(f"Data partitions successfully created:")
    logger.info(f"  Training Set   : {train_df.shape[0]} rows (Jan 2024 to Jun 2025)")
    logger.info(f"  Validation Set : {test_df.shape[0]} rows (Jul 2025 to Nov 2025)")
    logger.info(f"  Inference Set  : {inference_df.shape[0]} rows (Dec 2025, target = Jan 2026)")
    
    return train_df, test_df, inference_df

if __name__ == "__main__":
    grid, _ = prepare_forecasting_data()
    train_df, test_df, inference_df = split_forecasting_data(grid)
