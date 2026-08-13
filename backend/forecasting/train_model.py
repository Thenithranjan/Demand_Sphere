"""
==============================================================================
Demand Forecasting Model Training: train_model.py
==============================================================================
Why this file exists:
    This file handles training, tuning, and hyperparameter validation for our
    forecasting regressors. Model training turns raw feature vectors into a
    decision engine. Saving these models allows predict.py to make offline and
    online inferences instantly.

ML Concepts:
    - XGBoost Regressor (gradient boosting on decision trees).
    - Time-series cross validation (TimeSeriesSplit).
    - Grid search hyperparameter tuning.
    - Feature importance evaluation.
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
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV

# Set path relative to project root
FORECASTING_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FORECASTING_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.forecasting import DATA_DIR, MODELS_DIR, logger
from backend.forecasting.prepare_data import split_forecasting_data

# Define feature columns list
FEATURE_COLS = [
    "Year", "Month", "Quarter", "Week", "Day",
    "Category", "SubCategory", "Brand", "Price",
    "Quantity", "Revenue", "AveragePrice", "Season", "Festival"
]

def train_demand_forecast_models() -> Tuple[XGBRegressor, XGBRegressor, Dict[str, Any]]:
    """
    Executes the training and tuning pipeline:
    1. Loads the processed features dataset.
    2. Splits it chronologically into training and test sets.
    3. Runs hyperparameter grid search using TimeSeriesSplit cross-validation.
    4. Trains two XGBRegressor models (for Quantity and Revenue forecasting).
    5. Saves trained models to backend/models/ as joblib files.
    6. Extracts and logs feature importances.
    """
    logger.info("Initializing demand forecasting model training...")
    
    # 1. Load aggregated feature dataset
    dataset_path = DATA_DIR / "forecasting_features.csv"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Forecasting features not found at {dataset_path}. Run prepare_data.py first.")
        
    df = pd.read_csv(dataset_path)
    
    # Convert YearMonth back to Period for split utility compatibility
    df["YearMonth"] = pd.to_datetime(df["YearMonth"]).dt.to_period("M")
    
    # 2. Chronological data split
    train_df, test_df, _ = split_forecasting_data(df)
    
    # Separate features and target labels
    X_train = train_df[FEATURE_COLS]
    y_train_quantity = train_df["TargetQuantity"]
    y_train_revenue = train_df["TargetRevenue"]
    
    logger.info(f"Training features shape: {X_train.shape}")
    
    # 3. Define hyperparameter search space
    param_grid = {
        "n_estimators": [50, 100],
        "max_depth": [3, 5, 7],
        "learning_rate": [0.05, 0.1],
        "subsample": [0.8, 1.0],
        "random_state": [42]
    }
    
    # TimeSeriesSplit cross-validation (essential for time-series splits)
    tscv = TimeSeriesSplit(n_splits=3)
    
    # 4. Tune and Train Quantity Forecasting Model
    logger.info("Tuning hyper-parameters for Quantity Forecasting Model...")
    xgb_base = XGBRegressor(objective="reg:squarederror")
    grid_search_qty = GridSearchCV(
        estimator=xgb_base,
        param_grid=param_grid,
        cv=tscv,
        scoring="neg_mean_absolute_error",
        n_jobs=-1
    )
    grid_search_qty.fit(X_train, y_train_quantity)
    best_qty_model = grid_search_qty.best_estimator_
    logger.info(f"Best Quantity Parameters: {grid_search_qty.best_params_}")
    logger.info(f"Best Quantity Validation MAE: {-grid_search_qty.best_score_:.4f}")
    
    # 5. Tune and Train Revenue Forecasting Model
    logger.info("Tuning hyper-parameters for Revenue Forecasting Model...")
    grid_search_rev = GridSearchCV(
        estimator=xgb_base,
        param_grid=param_grid,
        cv=tscv,
        scoring="neg_mean_absolute_error",
        n_jobs=-1
    )
    grid_search_rev.fit(X_train, y_train_revenue)
    best_rev_model = grid_search_rev.best_estimator_
    logger.info(f"Best Revenue Parameters: {grid_search_rev.best_params_}")
    logger.info(f"Best Revenue Validation MAE: {-grid_search_rev.best_score_:.4f}")
    
    # 6. Extract Feature Importance
    importance_qty = best_qty_model.feature_importances_
    importance_rev = best_rev_model.feature_importances_
    
    importance_summary = pd.DataFrame({
        "Feature": FEATURE_COLS,
        "QuantityImportance": importance_qty,
        "RevenueImportance": importance_rev
    }).sort_values(by="QuantityImportance", ascending=False)
    
    logger.info("Top Feature Importances (Quantity forecasting):")
    for idx, row in importance_summary.head(5).iterrows():
        logger.info(f"  {row['Feature']}: {row['QuantityImportance']:.4f}")
        
    # 7. Save Models to models/ directory
    qty_model_path = MODELS_DIR / "forecast_quantity_xgb.joblib"
    rev_model_path = MODELS_DIR / "forecast_revenue_xgb.joblib"
    
    joblib.dump(best_qty_model, qty_model_path)
    joblib.dump(best_rev_model, rev_model_path)
    
    logger.info(f"Quantity model saved -> {qty_model_path}")
    logger.info(f"Revenue model saved -> {rev_model_path}")
    
    # Return objects and details
    metadata = {
        "best_params_quantity": grid_search_qty.best_params_,
        "best_params_revenue": grid_search_rev.best_params_,
        "feature_importances": importance_summary.to_dict(orient="records")
    }
    
    return best_qty_model, best_rev_model, metadata

if __name__ == "__main__":
    train_demand_forecast_models()
