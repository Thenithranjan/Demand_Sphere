"""
==============================================================================
Demand Forecasting Visualisation: visualize.py
==============================================================================
Why this file exists:
    A data science pipeline is incomplete without clear visualisation. Business
    stakeholders and executive teams cannot read tabular arrays or raw metrics.
    This file converts validation errors, model parameters, and predictions into
    professional, high-DPI charts.

Visualisations Generated:
    1. Actual vs. Predicted line chart over the validation period.
    2. XGBoost Feature Importance horizontal bar chart.
    3. Historical-to-Future Monthly Quantity demand line chart.
    4. Historical-to-Future Monthly Revenue forecast line chart.
    5. Category-wise predicted demand volume.
    6. Brand-wise predicted demand volume (top 10).
==============================================================================
"""

import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from xgboost import XGBRegressor

# Set path relative to project root
FORECASTING_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FORECASTING_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.forecasting import REPORTS_DIR, logger

# Styling Palette
COLORS = {
    "history": "#1E3A8A",      # Deep Navy for historical data
    "forecast": "#D97706",     # Warm Amber/Gold for predictions
    "actual": "#374151",       # Charcoal for validation actuals
    "predicted": "#E11D48",    # Crimson for validation predictions
    "revenue": "#059669",      # Emerald for revenue
    "grid": "#F3F4F6",         # Very light gray for grids
    "text": "#374151"          # Dark gray for labels
}

def set_style() -> None:
    """Configures global Matplotlib styling parameters for premium look."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["axes.facecolor"] = "white"
    plt.rcParams["grid.color"] = COLORS["grid"]
    plt.rcParams["axes.edgecolor"] = "#E5E7EB"
    plt.rcParams["axes.labelcolor"] = COLORS["text"]
    plt.rcParams["xtick.color"] = COLORS["text"]
    plt.rcParams["ytick.color"] = COLORS["text"]
    plt.rcParams["axes.titlesize"] = 13
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["axes.labelsize"] = 10

def generate_visualizations(
    test_df: pd.DataFrame,
    qty_model: XGBRegressor,
    rev_model: XGBRegressor,
    forecast_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    cat_forecast_df: pd.DataFrame,
    brand_forecast_df: pd.DataFrame
) -> None:
    """
    Orchestrates the generation of all 6 diagnostic and forecast plots.
    """
    logger.info("Initializing demand forecasting visualization pipeline...")
    set_style()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Actual vs Predicted line plot on test set
    plot_actual_vs_predicted(test_df, qty_model, REPORTS_DIR)

    # 2. Feature Importance horizontal bar chart
    plot_feature_importance(qty_model, REPORTS_DIR)

    # 3. Monthly Quantity Forecast (History + Future Month)
    plot_monthly_quantity_forecast(sales_df, forecast_df, REPORTS_DIR)

    # 4. Monthly Revenue Forecast (History + Future Month)
    plot_monthly_revenue_forecast(sales_df, forecast_df, REPORTS_DIR)

    # 5. Category Forecast
    plot_category_forecast(cat_forecast_df, REPORTS_DIR)

    # 6. Brand Forecast (Top 10)
    plot_brand_forecast(brand_forecast_df, REPORTS_DIR)

    logger.info("Forecasting visualisations completed successfully.")


def plot_actual_vs_predicted(test_df: pd.DataFrame, qty_model: XGBRegressor, output_dir: Path) -> None:
    """Generates comparison line chart comparing actual vs predicted quantity over the test months."""
    plt.figure(figsize=(9, 5))
    
    # Feature columns aligned with train_model.py
    feature_cols = [
        "Year", "Month", "Quarter", "Week", "Day",
        "Category", "SubCategory", "Brand", "Price",
        "Quantity", "Revenue", "AveragePrice", "Season", "Festival"
    ]
    
    test_copy = test_df.copy()
    test_copy["Predicted"] = np.clip(qty_model.predict(test_copy[feature_cols]), 0, None)
    
    # Aggregate actuals and predictions monthly
    monthly_comparison = test_copy.groupby("YearMonth").agg(
        Actual=("TargetQuantity", "sum"),
        Predicted=("Predicted", "sum")
    ).reset_index()
    
    # Convert Period to string for plotting labels
    x_labels = [str(period) for period in monthly_comparison["YearMonth"]]
    
    plt.plot(x_labels, monthly_comparison["Actual"], marker='o', color=COLORS["actual"], linewidth=2, label="Actual Demand")
    plt.plot(x_labels, monthly_comparison["Predicted"], marker='s', color=COLORS["predicted"], linestyle='--', linewidth=2, label="Predicted Demand")
    
    plt.title("Validation Set Performance: Actual vs. Predicted Demand (Units)", pad=15)
    plt.xlabel("Validation Month")
    plt.ylabel("Demand (Units)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "actual_vs_predicted.png", dpi=120)
    plt.close()


def plot_feature_importance(qty_model: XGBRegressor, output_dir: Path) -> None:
    """Generates horizontal bar chart of feature importances."""
    plt.figure(figsize=(9, 5))
    
    feature_cols = [
        "Year", "Month", "Quarter", "Week", "Day",
        "Category", "SubCategory", "Brand", "Price",
        "Quantity", "Revenue", "AveragePrice", "Season", "Festival"
    ]
    
    importances = qty_model.feature_importances_
    feat_df = pd.DataFrame({"Feature": feature_cols, "Importance": importances})
    feat_df = feat_df.sort_values(by="Importance", ascending=True)
    
    sns.barplot(
        x="Importance",
        y="Feature",
        data=feat_df,
        hue="Feature",
        palette="viridis",
        legend=False
    )
    plt.title("XGBoost Model Feature Importance (Quantity Forecasting)", pad=15)
    plt.xlabel("Feature Importance Score")
    plt.ylabel("Model Feature")
    plt.tight_layout()
    plt.savefig(output_dir / "feature_importance.png", dpi=120)
    plt.close()


def plot_monthly_quantity_forecast(sales_df: pd.DataFrame, forecast_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates monthly quantity demand line chart extending historical data with future prediction."""
    plt.figure(figsize=(10, 5))
    
    # 1. Aggregate historical monthly sales
    sales_copy = sales_df.copy()
    sales_copy["SaleDate"] = pd.to_datetime(sales_copy["SaleDate"])
    sales_copy["YearMonth"] = sales_copy["SaleDate"].dt.to_period("M")
    hist_monthly = sales_copy.groupby("YearMonth")["Quantity"].sum()
    
    # Sort and split into strings for plotting
    x_hist = [str(period) for period in hist_monthly.index]
    y_hist = hist_monthly.values
    
    # 2. Get future month prediction
    future_month = "2026-01"
    future_qty = forecast_df["PredictedQuantity"].sum()
    
    # Plot history
    plt.plot(x_hist, y_hist, marker='o', color=COLORS["history"], linewidth=2, label="Historical Sales")
    
    # Connect last history point to forecast
    x_combined = [x_hist[-1], future_month]
    y_combined = [y_hist[-1], future_qty]
    plt.plot(x_combined, y_combined, color=COLORS["forecast"], linestyle=':', linewidth=2)
    
    # Plot forecast point
    plt.plot(future_month, future_qty, marker='*', markersize=12, color=COLORS["forecast"], label="Forecast (Jan 2026)")
    
    plt.title("Historical Sales Trend & Future Month Demand Forecast (Units)", pad=15)
    plt.xlabel("Month")
    plt.ylabel("Total Demand Quantity (Units)")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "monthly_quantity_forecast.png", dpi=120)
    plt.close()


def plot_monthly_revenue_forecast(sales_df: pd.DataFrame, forecast_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates monthly revenue forecast line chart extending historical data with future prediction."""
    plt.figure(figsize=(10, 5))
    
    # Aggregate historical monthly revenue
    sales_copy = sales_df.copy()
    sales_copy["SaleDate"] = pd.to_datetime(sales_copy["SaleDate"])
    sales_copy["YearMonth"] = sales_copy["SaleDate"].dt.to_period("M")
    hist_monthly_rev = sales_copy.groupby("YearMonth")["FinalPrice"].sum()
    
    x_hist = [str(period) for period in hist_monthly_rev.index]
    y_hist = hist_monthly_rev.values / 1e5  # Scale to Lakhs ₹
    
    # Get future month revenue forecast
    future_month = "2026-01"
    future_rev = forecast_df["PredictedRevenue"].sum() / 1e5  # Scale to Lakhs ₹
    
    plt.plot(x_hist, y_hist, marker='o', color=COLORS["history"], linewidth=2, label="Historical Revenue")
    
    # Connection line
    x_combined = [x_hist[-1], future_month]
    y_combined = [y_hist[-1], future_rev]
    plt.plot(x_combined, y_combined, color=COLORS["revenue"], linestyle=':', linewidth=2)
    
    plt.plot(future_month, future_rev, marker='*', markersize=12, color=COLORS["revenue"], label="Forecast (Jan 2026)")
    
    plt.title("Historical Revenue Trend & Future Month Revenue Forecast (in Lakhs ₹)", pad=15)
    plt.xlabel("Month")
    plt.ylabel("Revenue (Lakhs ₹)")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "monthly_revenue_forecast.png", dpi=120)
    plt.close()


def plot_category_forecast(cat_forecast_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates category-wise forecast bar chart."""
    plt.figure(figsize=(8, 5))
    
    df = cat_forecast_df.sort_values(by="PredictedQuantity", ascending=False)
    
    sns.barplot(
        x="PredictedQuantity",
        y="Category",
        data=df,
        hue="Category",
        palette="crest",
        legend=False
    )
    plt.title("Predicted Demand Quantity by Product Category (Jan 2026)", pad=15)
    plt.xlabel("Predicted Demand Quantity (Units)")
    plt.ylabel("Product Category")
    plt.tight_layout()
    plt.savefig(output_dir / "category_forecast.png", dpi=120)
    plt.close()


def plot_brand_forecast(brand_forecast_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates brand-wise forecast bar chart for the top 10 brands."""
    plt.figure(figsize=(9, 5))
    
    df = brand_forecast_df.sort_values(by="PredictedQuantity", ascending=False).head(10)
    
    sns.barplot(
        x="PredictedQuantity",
        y="Brand",
        data=df,
        hue="Brand",
        palette="flare",
        legend=False
    )
    plt.title("Top 10 Brands by Predicted Demand Quantity (Jan 2026)", pad=15)
    plt.xlabel("Predicted Demand Quantity (Units)")
    plt.ylabel("Brand Name")
    plt.tight_layout()
    plt.savefig(output_dir / "brand_forecast.png", dpi=120)
    plt.close()
