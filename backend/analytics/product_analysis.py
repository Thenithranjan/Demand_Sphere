"""
==============================================================================
Product Analysis Module: product_analysis.py
==============================================================================
Importance of Product Analysis:
    Product analysis evaluates the structure of the inventory catalog. It helps
    sourcing, inventory, and category managers analyze whether the product mix
    is balanced, profitable, and aligned with market seasonality.

Business Insights Provided:
    1. Catalog Diversity: Evaluates catalog distribution across categories, brands,
       and fabrics to ensure the store is not over-indexed on a single product type.
    2. Pricing Strategy: Plots the distribution of prices to verify if the store's
       product positioning leans towards budget, standard, premium, or luxury categories.
    3. Profitability Mapping: Analyzes profit margins across the inventory, helping
       identify which products or brands yield the highest returns.
    4. Seasonality Tagging: Maps products to specific seasonal events (e.g., Summer,
       Diwali, Aadi Sale) to coordinate production and supply schedules.

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

logger = logging.getLogger("analytics.product")

def run_product_analysis(products_df: pd.DataFrame, output_dir: Path) -> None:
    """
    Orchestrates product catalog analysis, generates all 6 requested plots,
    and saves them in the output directory.

    Parameters
    ----------
    products_df : pd.DataFrame
        The cleaned product profile dataset (from products_clean.csv).
    output_dir : Path
        Directory where generated charts will be saved.
    """
    logger.info("Starting Product Analysis...")
    set_plot_style()
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Category Distribution
    plot_category_distribution(products_df, output_dir)

    # 2. Brand Distribution
    plot_brand_distribution(products_df, output_dir)

    # 3. Fabric Distribution
    plot_fabric_distribution(products_df, output_dir)

    # 4. Price Distribution
    plot_price_distribution(products_df, output_dir)

    # 5. Profit Distribution
    plot_profit_distribution(products_df, output_dir)

    # 6. Seasonal Product Distribution
    plot_seasonal_product_distribution(products_df, output_dir)

    logger.info("Product Analysis complete. All charts saved successfully.")


def plot_category_distribution(products_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates a bar chart showing the frequency of products in each category."""
    plt.figure(figsize=(8, 5))
    cat_counts = products_df["Category"].value_counts()
    
    sns.barplot(
        x=cat_counts.values,
        y=cat_counts.index,
        hue=cat_counts.index,
        palette="mako",
        legend=False
    )
    plt.title("Product Catalog Distribution by Category", pad=15)
    plt.xlabel("Number of Products")
    plt.ylabel("Category")
    plt.tight_layout()
    plt.savefig(output_dir / "product_category_distribution.png", dpi=120)
    plt.close()


def plot_brand_distribution(products_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates a bar chart showing product count per brand (top 15)."""
    plt.figure(figsize=(9, 5))
    brand_counts = products_df["Brand"].value_counts().head(15)
    
    sns.barplot(
        x=brand_counts.values,
        y=brand_counts.index,
        hue=brand_counts.index,
        palette="viridis",
        legend=False
    )
    plt.title("Top Brands in Product Catalog", pad=15)
    plt.xlabel("Number of Products")
    plt.ylabel("Brand")
    plt.tight_layout()
    plt.savefig(output_dir / "product_brand_distribution.png", dpi=120)
    plt.close()


def plot_fabric_distribution(products_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates a bar chart showing product count per fabric type."""
    plt.figure(figsize=(8, 5))
    fabric_counts = products_df["Fabric"].value_counts()
    
    sns.barplot(
        x=fabric_counts.values,
        y=fabric_counts.index,
        hue=fabric_counts.index,
        palette="crest",
        legend=False
    )
    plt.title("Product Catalog Distribution by Fabric Type", pad=15)
    plt.xlabel("Number of Products")
    plt.ylabel("Fabric Type")
    plt.tight_layout()
    plt.savefig(output_dir / "product_fabric_distribution.png", dpi=120)
    plt.close()


def plot_price_distribution(products_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates a histogram with KDE for product prices."""
    plt.figure(figsize=(8, 5))
    
    sns.histplot(data=products_df, x="Price", kde=True, color=COLORS["primary"], bins=20, edgecolor="white")
    plt.title("Distribution of Product Retail Prices (₹)", pad=15)
    plt.xlabel("Retail Price (₹)")
    plt.ylabel("Number of Products")
    plt.tight_layout()
    plt.savefig(output_dir / "product_price_distribution.png", dpi=120)
    plt.close()


def plot_profit_distribution(products_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates a histogram of product profit margin percentages."""
    plt.figure(figsize=(8, 5))
    
    # Plot distribution of ProfitMargin (which represents profit margin percentage)
    sns.histplot(data=products_df, x="ProfitMargin", kde=True, color=COLORS["accent"], bins=15, edgecolor="white")
    plt.title("Distribution of Product Profit Margins (%)", pad=15)
    plt.xlabel("Profit Margin Percentage (%)")
    plt.ylabel("Number of Products")
    plt.tight_layout()
    plt.savefig(output_dir / "product_profit_distribution.png", dpi=120)
    plt.close()


def plot_seasonal_product_distribution(products_df: pd.DataFrame, output_dir: Path) -> None:
    """
    Generates a bar chart showing product counts per seasonal demand tag.
    Handles comma-separated tags by splitting them and counting unique occurrences.
    """
    plt.figure(figsize=(9, 5))
    
    # Drop nulls and split tags by comma, strip whitespace, and create flat list
    tags = products_df["SeasonalDemandTag"].dropna().str.split(",")
    flat_tags = [tag.strip() for sublist in tags for tag in sublist if tag.strip()]
    
    # Create a frequency series
    tag_counts = pd.Series(flat_tags).value_counts()
    
    sns.barplot(
        x=tag_counts.values,
        y=tag_counts.index,
        hue=tag_counts.index,
        palette="flare",
        legend=False
    )
    plt.title("Product Distribution by Seasonal Demand Tag", pad=15)
    plt.xlabel("Number of Associated Products")
    plt.ylabel("Seasonal Tag")
    plt.tight_layout()
    plt.savefig(output_dir / "product_seasonal_distribution.png", dpi=120)
    plt.close()
