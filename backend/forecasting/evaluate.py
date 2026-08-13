"""
==============================================================================
Demand Forecasting Evaluation Engine: evaluate.py
==============================================================================
Why this file exists:
    An evaluation file provides mathematical proof of model performance.
    We cannot trust a machine learning model unless we measure its accuracy on
    unseen historical test data (July 2025 to November 2025). This script
    calculates key regression metrics, highlights error distributions, and
    explains how to interpret them in a retail setting.

ML Concepts:
    - Regression metrics: MAE, MSE, RMSE, R², and MAPE.
    - WAPE (Weighted Absolute Percentage Error) for zero-demand targets.
    - Test-set predictions vs. actual validation values.
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
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
from xgboost import XGBRegressor

# Set path relative to project root
FORECASTING_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FORECASTING_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.forecasting import DATA_DIR, logger

def calculate_wape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Calculates Weighted Absolute Percentage Error (WAPE).
    WAPE is the standard metric in supply chain analytics because it avoids
    division-by-zero errors when actual demand is 0.
    WAPE = Sum(|Actual - Predicted|) / Sum(Actual)
    """
    total_actual = np.sum(actual)
    if total_actual == 0:
        return 0.0
    return np.sum(np.abs(actual - predicted)) / total_actual

def evaluate_models(
    qty_model: XGBRegressor,
    rev_model: XGBRegressor,
    test_df: pd.DataFrame
) -> Dict[str, Dict[str, float]]:
    """
    Evaluates forecasting models on the test set:
    1. Extracts feature columns and runs predictions.
    2. Clips negative predictions to zero.
    3. Calculates MAE, MSE, RMSE, R2, MAPE, and WAPE.
    4. Logs metrics in a structured format.
    """
    logger.info("Initializing demand forecasting evaluation on validation set...")
    
    # Feature columns aligned with train_model.py
    feature_cols = [
        "Year", "Month", "Quarter", "Week", "Day",
        "Category", "SubCategory", "Brand", "Price",
        "Quantity", "Revenue", "AveragePrice", "Season", "Festival"
    ]
    
    X_test = test_df[feature_cols]
    y_qty_actual = test_df["TargetQuantity"].values
    y_rev_actual = test_df["TargetRevenue"].values
    
    # Generate predictions
    qty_pred = np.clip(qty_model.predict(X_test), 0, None)
    rev_pred = np.clip(rev_model.predict(X_test), 0, None)
    
    # Quantity Metrics
    mae_qty = mean_absolute_error(y_qty_actual, qty_pred)
    mse_qty = mean_squared_error(y_qty_actual, qty_pred)
    rmse_qty = np.sqrt(mse_qty)
    r2_qty = r2_score(y_qty_actual, qty_pred)
    wape_qty = calculate_wape(y_qty_actual, qty_pred)
    
    # Standard MAPE (handling division by zero by filtering out zero actuals)
    non_zero_mask_qty = y_qty_actual > 0
    if np.any(non_zero_mask_qty):
        mape_qty = mean_absolute_percentage_error(y_qty_actual[non_zero_mask_qty], qty_pred[non_zero_mask_qty])
    else:
        mape_qty = 0.0

    # Revenue Metrics
    mae_rev = mean_absolute_error(y_rev_actual, rev_pred)
    mse_rev = mean_squared_error(y_rev_actual, rev_pred)
    rmse_rev = np.sqrt(mse_rev)
    r2_rev = r2_score(y_rev_actual, rev_pred)
    wape_rev = calculate_wape(y_rev_actual, rev_pred)
    
    non_zero_mask_rev = y_rev_actual > 0
    if np.any(non_zero_mask_rev):
        mape_rev = mean_absolute_percentage_error(y_rev_actual[non_zero_mask_rev], rev_pred[non_zero_mask_rev])
    else:
        mape_rev = 0.0

    metrics = {
        "quantity": {
            "MAE": float(mae_qty),
            "MSE": float(mse_qty),
            "RMSE": float(rmse_qty),
            "R2": float(r2_qty),
            "MAPE": float(mape_qty),
            "WAPE": float(wape_qty)
        },
        "revenue": {
            "MAE": float(mae_rev),
            "MSE": float(mse_rev),
            "RMSE": float(rmse_rev),
            "R2": float(r2_rev),
            "MAPE": float(mape_rev),
            "WAPE": float(wape_rev)
        }
    }
    
    # Log the summary metrics
    logger.info("=" * 60)
    logger.info("DEMAND FORECASTING EVALUATION REPORT")
    logger.info("=" * 60)
    
    logger.info("Quantity forecasting model metrics:")
    logger.info(f"  Mean Absolute Error (MAE)        : {mae_qty:.4f} units")
    logger.info(f"  Mean Squared Error (MSE)          : {mse_qty:.4f}")
    logger.info(f"  Root Mean Squared Error (RMSE)    : {rmse_qty:.4f} units")
    logger.info(f"  Coefficient of Determination (R²): {r2_qty:.4f}")
    logger.info(f"  Mean Absolute % Error (MAPE)      : {mape_qty * 100:.2f}%")
    logger.info(f"  Weighted Absolute % Error (WAPE)  : {wape_qty * 100:.2f}%")
    
    logger.info("-" * 60)
    
    logger.info("Revenue forecasting model metrics:")
    logger.info(f"  Mean Absolute Error (MAE)        : ₹{mae_rev:,.4f}")
    logger.info(f"  Mean Squared Error (MSE)          : {mse_rev:.4f}")
    logger.info(f"  Root Mean Squared Error (RMSE)    : ₹{rmse_rev:,.4f}")
    logger.info(f"  Coefficient of Determination (R²): {r2_rev:.4f}")
    logger.info(f"  Mean Absolute % Error (MAPE)      : {mape_rev * 100:.2f}%")
    logger.info(f"  Weighted Absolute % Error (WAPE)  : {wape_rev * 100:.2f}%")
    
    logger.info("=" * 60)
    
    return metrics

if __name__ == "__main__":
    from backend.forecasting.prepare_data import prepare_forecasting_data, split_forecasting_data
    from backend.forecasting.predict import load_forecasting_models
    
    grid, _ = prepare_forecasting_data()
    _, test_df, _ = split_forecasting_data(grid)
    
    qty_model, rev_model = load_forecasting_models()
    evaluate_models(qty_model, rev_model, test_df)
