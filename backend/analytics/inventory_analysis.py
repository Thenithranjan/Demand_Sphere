"""
==============================================================================
Inventory Analysis Module: inventory_analysis.py
==============================================================================
Importance of Inventory Analysis:
    Inventory is working capital tied up in physical assets. Proper inventory analysis
    prevents stockouts (which lead to lost sales) and minimizes overstocking (which
    increases holding costs, risk of obsolescence, and reduces cash flow liquidity).

Business Insights Provided:
    1. Stock Allocation: Maps total stock volume across different warehouses
       (Chennai, Madurai, Coimbatore), ensuring stock distribution matches regional demand.
    2. Stockout Risk (Low Stock & Reorder Points): Pinpoints exactly which products have
       dipped below their safety limits, prompting immediate restock orders.
    3. Holding Cost Risk (Overstock): Highlights products that exceed their maximum
       stock thresholds, indicating where promotion or markdowns may be needed to clear space.
    4. Supply Chain Health (Safety Stock): Reviews the buffer stock margins across product
       categories to prevent disruptions from lead-time delays.

==============================================================================
"""

import os
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Import shared configurations
from backend.analytics import COLORS, set_plot_style

logger = logging.getLogger("analytics.inventory")

def run_inventory_analysis(inventory_df: pd.DataFrame, products_df: pd.DataFrame, output_dir: Path) -> None:
    """
    Orchestrates inventory metrics analysis, generates all 6 requested plots,
    and saves them in the output directory.

    Parameters
    ----------
    inventory_df : pd.DataFrame
        The cleaned inventory dataset (from inventory_clean.csv).
    products_df : pd.DataFrame
        The cleaned products catalog (from products_clean.csv).
    output_dir : Path
        Directory where generated charts will be saved.
    """
    logger.info("Starting Inventory Analysis...")
    set_plot_style()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Merge inventory and product metadata on ProductID to enable category-wise analyses
    df = pd.merge(inventory_df, products_df[["ProductID", "ProductName", "Category", "SubCategory"]], on="ProductID", how="left")

    # 1. Current Stock Distribution
    plot_current_stock_distribution(df, output_dir)

    # 2. Low Stock Products
    plot_low_stock_products(df, output_dir)

    # 3. Overstock Products
    plot_overstock_products(df, output_dir)

    # 4. Warehouse Stock
    plot_warehouse_stock(df, output_dir)

    # 5. Safety Stock Analysis
    plot_safety_stock_analysis(df, output_dir)

    # 6. Reorder Point Analysis
    plot_reorder_point_analysis(df, output_dir)

    logger.info("Inventory Analysis complete. All charts saved successfully.")


def plot_current_stock_distribution(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates histogram of current stock levels across all products."""
    plt.figure(figsize=(8, 5))
    
    sns.histplot(data=df, x="CurrentStock", kde=True, color=COLORS["primary"], bins=20, edgecolor="white")
    plt.title("Current Stock Levels Distribution", pad=15)
    plt.xlabel("Current Stock (Units)")
    plt.ylabel("Number of Products")
    plt.tight_layout()
    plt.savefig(output_dir / "inventory_stock_distribution.png", dpi=120)
    plt.close()


def plot_low_stock_products(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates bar chart listing products that are critically low on stock (relative to MinimumStock)."""
    plt.figure(figsize=(10, 6))
    
    # Filter for low stock items
    low_stock = df[df["CurrentStock"] <= df["MinimumStock"]].copy()
    
    if low_stock.empty:
        # Fallback if no products are below minimum: show the 10 products with lowest current stock
        low_stock = df.nsmallest(10, "CurrentStock")
        title = "Top 10 Products with Lowest Current Stock Levels (None below MinimumStock)"
    else:
        # Calculate shortage ratio (how much stock is left relative to the minimum required)
        low_stock["StockRatio"] = low_stock["CurrentStock"] / low_stock["MinimumStock"]
        low_stock = low_stock.sort_values(by="StockRatio", ascending=True).head(12)
        title = "Top Critical Low-Stock Products (Current <= Minimum Stock)"

    # Identify Display Name
    low_stock["DisplayName"] = low_stock["ProductName"] + " (" + low_stock["ProductID"] + ")"
    
    # Custom color palette where low values are bright red (danger)
    sns.barplot(
        x="CurrentStock",
        y="DisplayName",
        hue="DisplayName",
        data=low_stock,
        palette="Reds_r",
        legend=False
    )
    plt.title(title, pad=15)
    plt.xlabel("Current Stock Level (Units)")
    plt.ylabel("Product Details")
    plt.tight_layout()
    plt.savefig(output_dir / "inventory_low_stock.png", dpi=120)
    plt.close()


def plot_overstock_products(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates bar chart listing products that are overstocked (relative to MaximumStock)."""
    plt.figure(figsize=(10, 6))
    
    # Filter or compute overstock ratio
    df_copy = df.copy()
    df_copy["OverstockRatio"] = df_copy["CurrentStock"] / df_copy["MaximumStock"]
    
    # Select the top 10 items exceeding their MaximumStock threshold
    overstocked = df_copy[df_copy["CurrentStock"] > df_copy["MaximumStock"]]
    if overstocked.empty:
        overstocked = df_copy.nlargest(10, "OverstockRatio")
        title = "Top 10 Products with Highest Stock-to-Max Ratios (None exceeding MaximumStock)"
    else:
        overstocked = overstocked.sort_values(by="OverstockRatio", ascending=False).head(10)
        title = "Top Overstocked Products (Current > Maximum Stock)"
        
    overstocked["DisplayName"] = overstocked["ProductName"] + " (" + overstocked["ProductID"] + ")"
    
    sns.barplot(
        x="CurrentStock",
        y="DisplayName",
        hue="DisplayName",
        data=overstocked,
        palette="Oranges_r",
        legend=False
    )
    plt.title(title, pad=15)
    plt.xlabel("Current Stock Level (Units)")
    plt.ylabel("Product Details")
    plt.tight_layout()
    plt.savefig(output_dir / "inventory_overstock.png", dpi=120)
    plt.close()


def plot_warehouse_stock(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates bar chart showing warehouse wise stock aggregates."""
    plt.figure(figsize=(7, 5))
    wh_stock = df.groupby("Warehouse")["CurrentStock"].sum().sort_values(ascending=False)
    
    sns.barplot(
        x=wh_stock.index,
        y=wh_stock.values,
        hue=wh_stock.index,
        palette=[COLORS["primary"], COLORS["teal"], COLORS["secondary"]][:len(wh_stock)],
        legend=False
    )
    plt.title("Total Stock Volume by Warehouse", pad=15)
    plt.xlabel("Warehouse Location")
    plt.ylabel("Total Stock Volume (Units)")
    plt.tight_layout()
    plt.savefig(output_dir / "inventory_warehouse_stock.png", dpi=120)
    plt.close()


def plot_safety_stock_analysis(df: pd.DataFrame, output_dir: Path) -> None:
    """
    Generates safety stock analysis chart.
    Compares Average Safety Stock vs. Average Current Stock across Product Categories.
    """
    plt.figure(figsize=(9, 5))
    
    # Calculate category averages
    cat_averages = df.groupby("Category")[["CurrentStock", "SafetyStock"]].mean().reset_index()
    
    # Melt dataframe to long format for Seaborn plotting
    melted = cat_averages.melt(id_vars="Category", value_vars=["CurrentStock", "SafetyStock"], 
                               var_name="StockType", value_name="AverageUnits")
    
    sns.barplot(
        data=melted,
        x="Category",
        y="AverageUnits",
        hue="StockType",
        palette=[COLORS["primary"], COLORS["accent"]]
    )
    plt.title("Safety Stock buffer vs. Average Current Stock by Category", pad=15)
    plt.xlabel("Product Category")
    plt.ylabel("Average Stock (Units)")
    plt.legend(title="Stock Metric")
    plt.tight_layout()
    plt.savefig(output_dir / "inventory_safety_stock.png", dpi=120)
    plt.close()


def plot_reorder_point_analysis(df: pd.DataFrame, output_dir: Path) -> None:
    """
    Generates Reorder Point Analysis chart.
    Selects 15 products with the lowest CurrentStock/ReorderPoint ratio and plots their CurrentStock
    against their ReorderPoint.
    """
    plt.figure(figsize=(11, 6))
    
    # Calculate reorder ratio
    df_copy = df.copy()
    df_copy["ReorderRatio"] = df_copy["CurrentStock"] / df_copy["ReorderPoint"]
    
    # Select top 15 most urgent items needing reordering
    urgent = df_copy.sort_values(by="ReorderRatio", ascending=True).head(15)
    urgent["DisplayName"] = urgent["ProductName"] + " (" + urgent["ProductID"] + ")"
    
    # Create y indices for side-by-side comparison
    y_pos = np.arange(len(urgent))
    height = 0.35
    
    plt.barh(y_pos - height/2, urgent["CurrentStock"], height, label="Current Stock", color=COLORS["danger"])
    plt.barh(y_pos + height/2, urgent["ReorderPoint"], height, label="Reorder Point Trigger", color=COLORS["neutral_dark"], alpha=0.6)
    
    plt.yticks(y_pos, urgent["DisplayName"])
    plt.title("Reorder Point Analysis: Critical Stock Levels vs. Reorder Triggers", pad=15)
    plt.xlabel("Stock Volume (Units)")
    plt.ylabel("Product")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(output_dir / "inventory_reorder_point.png", dpi=120)
    plt.close()
