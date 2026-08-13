"""
==============================================================================
Inventory Visualisation Module: visualize.py
==============================================================================
Why this file is needed:
    A supply chain dashboard requires clear visual analytics. This file acts as our
    **visualization engine**. It takes the optimized inventory decisions dataset,
    aggregates metrics, and generates 8 high-DPI charts saved inside
    `reports/inventory/` to help executives monitor operational risk and warehouse capacity.

Visualisations Generated:
    1. Inventory Distribution: Histogram of physical stock levels.
    2. Low Stock Products: Top 15 products with lowest current stock.
    3. Stock by Category: Stock quantities aggregated by Product Category.
    4. Stock by Brand: Stock quantities aggregated by top brands.
    5. Forecast vs. Current Stock: Scatter plot mapping demand vs. supply.
    6. Inventory Risk Heatmap: Pivot heatmap of average risk per Category x Warehouse.
    7. Warehouse Utilization: Total stock holding per warehouse.
    8. Reorder Quantity: Suggested purchase quantities per category.
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

# Set path relative to project root
INVENTORY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = INVENTORY_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.inventory import REPORTS_DIR, logger

# Visual styling colors
COLORS = {
    "primary": "#1E3A8A",      # Deep Navy
    "secondary": "#D97706",    # Gold/Amber
    "accent": "#059669",       # Emerald
    "danger": "#E11D48",       # Crimson Red
    "teal": "#0D9488",         # Teal
    "neutral_dark": "#374151", # Charcoal
    "neutral_light": "#F3F4F6"# Off-white
}

def set_visual_style() -> None:
    """Configures global Matplotlib parameters for consistent professional visuals."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["axes.facecolor"] = "white"
    plt.rcParams["axes.edgecolor"] = "#E5E7EB"
    plt.rcParams["grid.color"] = "#F3F4F6"
    plt.rcParams["axes.labelcolor"] = COLORS["neutral_dark"]
    plt.rcParams["xtick.color"] = COLORS["neutral_dark"]
    plt.rcParams["ytick.color"] = COLORS["neutral_dark"]
    plt.rcParams["axes.titlesize"] = 13
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["axes.labelsize"] = 10

def generate_inventory_charts(df: pd.DataFrame) -> None:
    """
    Orchestrates the generation of all 8 inventory plots.
    """
    logger.info("Initializing inventory visualization pipeline...")
    set_visual_style()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Inventory Distribution
    plot_inventory_distribution(df, REPORTS_DIR)
    
    # 2. Low Stock Products
    plot_low_stock_products(df, REPORTS_DIR)
    
    # 3. Stock by Category
    plot_stock_by_category(df, REPORTS_DIR)
    
    # 4. Stock by Brand
    plot_stock_by_brand(df, REPORTS_DIR)
    
    # 5. Forecast vs Current Stock
    plot_forecast_vs_current(df, REPORTS_DIR)
    
    # 6. Inventory Risk Heatmap
    plot_risk_heatmap(df, REPORTS_DIR)
    
    # 7. Warehouse Utilization
    plot_warehouse_utilization(df, REPORTS_DIR)
    
    # 8. Reorder Quantity
    plot_reorder_quantity(df, REPORTS_DIR)
    
    logger.info("Inventory visualisations generated successfully.")


def plot_inventory_distribution(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates histogram of current stock levels."""
    plt.figure(figsize=(8, 5))
    sns.histplot(data=df, x="CurrentStock", kde=True, color=COLORS["primary"], bins=20, edgecolor="white")
    plt.title("Current Inventory Stock Level Distribution", pad=15)
    plt.xlabel("Current Stock Level (Units)")
    plt.ylabel("Number of Products")
    plt.tight_layout()
    plt.savefig(output_dir / "inventory_distribution.png", dpi=120)
    plt.close()


def plot_low_stock_products(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates horizontal bar chart showing top 15 products with lowest stock."""
    plt.figure(figsize=(10, 6))
    low_stock = df.sort_values(by="CurrentStock").head(15).copy()
    low_stock["DisplayName"] = low_stock["ProductName"] + " (" + low_stock["ProductID"] + ")"
    
    sns.barplot(
        x="CurrentStock",
        y="DisplayName",
        hue="DisplayName",
        data=low_stock,
        palette="Reds_r",
        legend=False
    )
    plt.title("Top 15 Products with Lowest Stock Levels", pad=15)
    plt.xlabel("Current Stock Level (Units)")
    plt.ylabel("Product Details")
    plt.tight_layout()
    plt.savefig(output_dir / "low_stock_products.png", dpi=120)
    plt.close()


def plot_stock_by_category(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates bar chart of stock quantity grouped by Category."""
    plt.figure(figsize=(8, 5))
    cat_stock = df.groupby("Category")["CurrentStock"].sum().reset_index().sort_values(by="CurrentStock", ascending=False)
    
    sns.barplot(
        x="CurrentStock",
        y="Category",
        hue="Category",
        data=cat_stock,
        palette="crest",
        legend=False
    )
    plt.title("Total Stock Volume by Product Category", pad=15)
    plt.xlabel("Total Stock Held (Units)")
    plt.ylabel("Product Category")
    plt.tight_layout()
    plt.savefig(output_dir / "stock_by_category.png", dpi=120)
    plt.close()


def plot_stock_by_brand(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates bar chart of stock quantity grouped by top 15 Brands."""
    plt.figure(figsize=(9, 5))
    brand_stock = df.groupby("Brand")["CurrentStock"].sum().reset_index().sort_values(by="CurrentStock", ascending=False).head(15)
    
    sns.barplot(
        x="CurrentStock",
        y="Brand",
        hue="Brand",
        data=brand_stock,
        palette="viridis",
        legend=False
    )
    plt.title("Top 15 Brands by Total Stock Volume", pad=15)
    plt.xlabel("Total Stock Held (Units)")
    plt.ylabel("Brand Name")
    plt.tight_layout()
    plt.savefig(output_dir / "stock_by_brand.png", dpi=120)
    plt.close()


def plot_forecast_vs_current(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates scatter plot of Forecast Demand vs Current Stock."""
    plt.figure(figsize=(8, 6))
    
    sns.scatterplot(
        data=df,
        x="CurrentStock",
        y="ForecastDemand",
        hue="RiskLevel",
        palette="Set1",
        alpha=0.7,
        edgecolor=None
    )
    
    # Plot diagonal reference line where Forecast = Stock
    max_val = max(df["CurrentStock"].max(), df["ForecastDemand"].max())
    plt.plot([0, max_val], [0, max_val], color=COLORS["neutral_dark"], linestyle="--", alpha=0.5, label="Supply = Demand")
    
    plt.title("Forecast Demand vs. Current Stock Levels (Risk Mapping)", pad=15)
    plt.xlabel("Current Stock Level (Units)")
    plt.ylabel("Forecasted Demand (Units)")
    plt.legend(title="Risk Level")
    plt.tight_layout()
    plt.savefig(output_dir / "forecast_vs_current.png", dpi=120)
    plt.close()


def plot_risk_heatmap(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates Category vs Warehouse risk average heatmap."""
    plt.figure(figsize=(9, 6))
    
    # Pivot table of average Risk Score per category in each warehouse
    pivot_df = df.pivot_table(
        values="InventoryRiskScore",
        index="Category",
        columns="Warehouse",
        aggfunc="mean"
    ).fillna(0)
    
    sns.heatmap(pivot_df, annot=True, fmt=".1f", cmap="Reds", cbar_kws={'label': 'Average Risk Score'})
    plt.title("Inventory Risk Heatmap (Average Risk Score by Category & Warehouse)", pad=15)
    plt.xlabel("Warehouse Location")
    plt.ylabel("Product Category")
    plt.tight_layout()
    plt.savefig(output_dir / "inventory_risk_heatmap.png", dpi=120)
    plt.close()


def plot_warehouse_utilization(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates bar chart of stock quantity holding per warehouse location."""
    plt.figure(figsize=(7, 5))
    wh_stock = df.groupby("Warehouse")["CurrentStock"].sum().reset_index().sort_values(by="CurrentStock", ascending=False)
    
    sns.barplot(
        x="Warehouse",
        y="CurrentStock",
        hue="Warehouse",
        data=wh_stock,
        palette=[COLORS["primary"], COLORS["teal"], COLORS["secondary"]][:len(wh_stock)],
        legend=False
    )
    plt.title("Warehouse Stock Holdings", pad=15)
    plt.xlabel("Warehouse Location")
    plt.ylabel("Total Stock Volume (Units)")
    plt.tight_layout()
    plt.savefig(output_dir / "warehouse_utilization.png", dpi=120)
    plt.close()


def plot_reorder_quantity(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates bar chart of suggested purchase quantity grouped by category."""
    plt.figure(figsize=(8, 5))
    reorder_qty = df.groupby("Category")["SuggestedPurchaseQuantity"].sum().reset_index().sort_values(by="SuggestedPurchaseQuantity", ascending=False)
    
    sns.barplot(
        x="SuggestedPurchaseQuantity",
        y="Category",
        hue="Category",
        data=reorder_qty,
        palette="flare",
        legend=False
    )
    plt.title("Suggested Purchase Order Quantity by Product Category", pad=15)
    plt.xlabel("Total Suggested Purchase Order Quantity (Units)")
    plt.ylabel("Product Category")
    plt.tight_layout()
    plt.savefig(output_dir / "reorder_quantity.png", dpi=120)
    plt.close()
