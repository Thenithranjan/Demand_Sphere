"""
==============================================================================
Sales Analysis Module: sales_analysis.py
==============================================================================
Importance of Sales Analysis:
    Sales analysis is the cornerstone of retail intelligence. It allows
    business operations to monitor financial health, track performance against
    targets, and map out growth trajectories.

Business Insights Provided:
    1. Seasonal & Festival Trends: Highlights which periods (like Diwali or
       Pongal) drive the highest transaction volumes, helping in seasonal pricing
       and demand planning.
    2. Product & Category Demand: Uncovers the top performers (brands, categories,
       and specific products), allowing stores to optimize shelf space and catalog
       decisions.
    3. Day-of-week Sales Distribution: Determines whether customer traffic spikes
       on weekends or stays steady, allowing for efficient staff allocation.

==============================================================================
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Import shared configurations
from backend.analytics import COLORS, set_plot_style

logger = logging.getLogger("analytics.sales")

def run_sales_analysis(master_df: pd.DataFrame, output_dir: Path) -> None:
    """
    Orchestrates the sales analysis, generates all 10 requested plots,
    and saves them in the output directory.

    Parameters
    ----------
    master_df : pd.DataFrame
        The merged transaction dataset (sales joined with products and customers).
    output_dir : Path
        Directory where generated charts will be saved.
    """
    logger.info("Starting Sales Analysis...")
    set_plot_style()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure date column is datetime format for correct time-series plotting
    df = master_df.copy()
    df["SaleDate"] = pd.to_datetime(df["SaleDate"])
    df["YearMonth"] = df["SaleDate"].dt.to_period("M")
    
    # 1. Monthly Sales Trend (Transaction count)
    plot_monthly_sales_trend(df, output_dir)
    
    # 2. Revenue Trend
    plot_revenue_trend(df, output_dir)
    
    # 3. Quantity Sold Trend
    plot_quantity_trend(df, output_dir)
    
    # 4. Festival Sales
    plot_festival_sales(df, output_dir)
    
    # 5. Seasonal Sales
    plot_seasonal_sales(df, output_dir)
    
    # 6. Top Selling Products
    plot_top_selling_products(df, output_dir)
    
    # 7. Top Selling Categories
    plot_top_selling_categories(df, output_dir)
    
    # 8. Top Selling Brands
    plot_top_selling_brands(df, output_dir)
    
    # 9. Daily Sales Distribution
    plot_daily_sales_distribution(df, output_dir)
    
    # 10. Weekend vs Weekday Sales
    plot_weekend_weekday_sales(df, output_dir)

    logger.info("Sales Analysis complete. All charts saved successfully.")


def plot_monthly_sales_trend(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates monthly sales count trend line chart."""
    plt.figure(figsize=(10, 5))
    monthly_sales = df.groupby("YearMonth").size()
    
    # Convert Period to string for plotting
    x_labels = [str(period) for period in monthly_sales.index]
    
    plt.plot(x_labels, monthly_sales.values, marker='o', color=COLORS["primary"], linewidth=2, label="Transactions")
    plt.title("Monthly Sales Trend (Transaction Volume)", pad=15)
    plt.xlabel("Month")
    plt.ylabel("Number of Transactions")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "sales_monthly_trend.png", dpi=120)
    plt.close()


def plot_revenue_trend(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates revenue trend over months."""
    plt.figure(figsize=(10, 5))
    monthly_revenue = df.groupby("YearMonth")["FinalPrice"].sum()
    x_labels = [str(period) for period in monthly_revenue.index]
    
    plt.plot(x_labels, monthly_revenue.values / 1e5, marker='s', color=COLORS["accent"], linewidth=2, label="Revenue (Lakhs)")
    plt.title("Revenue Trend (in Lakhs ₹)", pad=15)
    plt.xlabel("Month")
    plt.ylabel("Revenue (Lakhs ₹)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "sales_revenue_trend.png", dpi=120)
    plt.close()


def plot_quantity_trend(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates quantity sold trend over months."""
    plt.figure(figsize=(10, 5))
    monthly_quantity = df.groupby("YearMonth")["Quantity"].sum()
    x_labels = [str(period) for period in monthly_quantity.index]
    
    plt.plot(x_labels, monthly_quantity.values, marker='^', color=COLORS["secondary"], linewidth=2, label="Quantity Sold")
    plt.title("Quantity Sold Trend", pad=15)
    plt.xlabel("Month")
    plt.ylabel("Total Quantity Sold (Units)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "sales_quantity_trend.png", dpi=120)
    plt.close()


def plot_festival_sales(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates festival sales comparison chart."""
    plt.figure(figsize=(8, 5))
    fest_sales = df.groupby("Festival")["FinalPrice"].sum().sort_values(ascending=False)
    
    # Render premium horizontal bar chart
    sns.barplot(x=fest_sales.values / 1e5, y=fest_sales.index, hue=fest_sales.index, palette="viridis", legend=False)
    plt.title("Revenue Contribution by Festival (in Lakhs ₹)", pad=15)
    plt.xlabel("Revenue (Lakhs ₹)")
    plt.ylabel("Festival")
    plt.tight_layout()
    plt.savefig(output_dir / "sales_festival.png", dpi=120)
    plt.close()


def plot_seasonal_sales(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates seasonal sales distribution chart."""
    plt.figure(figsize=(8, 5))
    seasonal_sales = df.groupby("Season")["FinalPrice"].sum().sort_values(ascending=False)
    
    sns.barplot(x=seasonal_sales.index, y=seasonal_sales.values / 1e5, hue=seasonal_sales.index, palette="crest", legend=False)
    plt.title("Revenue Contribution by Season (in Lakhs ₹)", pad=15)
    plt.xlabel("Season")
    plt.ylabel("Revenue (Lakhs ₹)")
    plt.tight_layout()
    plt.savefig(output_dir / "sales_seasonal.png", dpi=120)
    plt.close()


def plot_top_selling_products(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates chart showing the top 10 selling products by quantity."""
    plt.figure(figsize=(10, 6))
    
    # Fallback to ProductID if ProductName is missing
    name_col = "ProductName" if "ProductName" in df.columns else "ProductID"
    top_prod = df.groupby(name_col)["Quantity"].sum().sort_values(ascending=False).head(10)
    
    sns.barplot(x=top_prod.values, y=top_prod.index, hue=top_prod.index, palette="flare", legend=False)
    plt.title("Top 10 Selling Products by Quantity Sold", pad=15)
    plt.xlabel("Quantity Sold (Units)")
    plt.ylabel("Product")
    plt.tight_layout()
    plt.savefig(output_dir / "sales_top_products.png", dpi=120)
    plt.close()


def plot_top_selling_categories(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates chart showing top selling product categories by revenue."""
    plt.figure(figsize=(8, 5))
    cat_col = "Category" if "Category" in df.columns else "SubCategory"
    top_cat = df.groupby(cat_col)["FinalPrice"].sum().sort_values(ascending=False)
    
    sns.barplot(x=top_cat.values / 1e5, y=top_cat.index, hue=top_cat.index, palette="mako", legend=False)
    plt.title("Revenue Contribution by Product Category (in Lakhs ₹)", pad=15)
    plt.xlabel("Revenue (Lakhs ₹)")
    plt.ylabel("Category")
    plt.tight_layout()
    plt.savefig(output_dir / "sales_top_categories.png", dpi=120)
    plt.close()


def plot_top_selling_brands(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates chart showing top selling product brands by revenue."""
    plt.figure(figsize=(9, 5))
    brand_col = "Brand" if "Brand" in df.columns else "SubCategory"
    top_brand = df.groupby(brand_col)["FinalPrice"].sum().sort_values(ascending=False).head(10)
    
    sns.barplot(x=top_brand.values / 1e5, y=top_brand.index, hue=top_brand.index, palette="magma", legend=False)
    plt.title("Top 10 Selling Brands by Revenue (in Lakhs ₹)", pad=15)
    plt.xlabel("Revenue (Lakhs ₹)")
    plt.ylabel("Brand")
    plt.tight_layout()
    plt.savefig(output_dir / "sales_top_brands.png", dpi=120)
    plt.close()


def plot_daily_sales_distribution(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates sales distribution chart across days of the week."""
    plt.figure(figsize=(8, 5))
    
    # Establish ordering for days of the week
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    daily_sales = df.groupby("DayOfWeek").size().reindex(day_order)
    
    sns.barplot(x=daily_sales.index, y=daily_sales.values, hue=daily_sales.index, palette="Blues_r", legend=False)
    plt.title("Sales Transaction Distribution by Day of Week", pad=15)
    plt.xlabel("Day of Week")
    plt.ylabel("Number of Transactions")
    plt.tight_layout()
    plt.savefig(output_dir / "sales_daily_distribution.png", dpi=120)
    plt.close()


def plot_weekend_weekday_sales(df: pd.DataFrame, output_dir: Path) -> None:
    """Generates a comparison chart between average daily sales on Weekdays vs Weekends."""
    plt.figure(figsize=(6, 5))
    
    # Map days of the week to Weekend vs Weekday
    df["DayType"] = np.where(df["DayOfWeek"].isin(["Saturday", "Sunday"]), "Weekend", "Weekday")
    
    # Group by transaction date to get daily totals
    daily_totals = df.groupby(["SaleDate", "DayType"])["FinalPrice"].sum().reset_index()
    avg_sales = daily_totals.groupby("DayType")["FinalPrice"].mean()
    
    sns.barplot(x=avg_sales.index, y=avg_sales.values, hue=avg_sales.index, palette=[COLORS["primary"], COLORS["secondary"]], legend=False)
    plt.title("Average Daily Sales: Weekdays vs. Weekends", pad=15)
    plt.xlabel("Day Type")
    plt.ylabel("Average Daily Revenue (₹)")
    plt.tight_layout()
    plt.savefig(output_dir / "sales_weekend_weekday.png", dpi=120)
    plt.close()
