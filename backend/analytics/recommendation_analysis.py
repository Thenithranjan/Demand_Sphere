"""
==============================================================================
Recommendation Analysis Module: recommendation_analysis.py
==============================================================================
Importance of Recommendation Analysis:
    Recommendation systems are key revenue drivers in modern e-commerce and retail
    (often contributing 10% to 35% of total sales). Analyzing recommendations
    offline allows data scientists to identify catalog coverage issues, inspect
    popular items for bias, and verify the distribution of confidence scores.

Business Insights Provided:
    1. Recommendation Popularity Bias (Most Recommended): Identifies whether
       the hybrid engine over-recommends a small set of popular items (superstars)
       or maintains a healthy catalog coverage.
    2. Recommendation Score Confidence: Visualizes the distribution of hybrid
       matching scores. A distribution skewed towards higher scores indicates
       high recommendation confidence.
    3. Empirical Cross-Sell Insights (Market Basket): Employs transaction co-occurrence
       counts (Market Basket Analysis) to show which textile items are actually
       purchased together, validating and improving business cross-sell rules.

==============================================================================
"""

import os
import logging
from pathlib import Path
from collections import Counter
from itertools import combinations
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Import shared configurations
from backend.analytics import COLORS, set_plot_style
# Import the recommendation engine
from backend.recommendation.hybrid_model import hybrid_recommend_for_customer

logger = logging.getLogger("analytics.recommendation")

def run_recommendation_analysis(
    sales_df: pd.DataFrame, 
    customers_df: pd.DataFrame, 
    products_df: pd.DataFrame, 
    output_dir: Path,
    sample_size: int = 100
) -> None:
    """
    Orchestrates recommendation analytics. Generates 3 charts:
    1. Most Recommended Products
    2. Empirical Cross-Sell Frequencies (Market Basket Analysis)
    3. Recommendation Score Distribution

    Parameters
    ----------
    sales_df : pd.DataFrame
        Cleaned transactions dataset (from sales_clean.csv).
    customers_df : pd.DataFrame
        Cleaned customer dataset (from customers_clean.csv).
    products_df : pd.DataFrame
        Cleaned product catalog (from products_clean.csv).
    output_dir : Path
        Directory where generated charts will be saved.
    sample_size : int, default 100
        Number of random customers to run recommendations for.
    """
    logger.info("Starting Recommendation Analysis...")
    set_plot_style()
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Run hybrid recommendations for a random sample of customers to collect diagnostic data
    recs_collected = []
    scores_collected = []

    # Get a list of customers who have purchase records in sales
    active_customer_ids = sales_df["CustomerID"].unique()
    
    # Filter the customer master list to active customers
    active_customers = customers_df[customers_df["CustomerID"].isin(active_customer_ids)]
    
    if active_customers.empty:
        logger.warning("No active customers found. Sampling from full customer list.")
        sample_pool = customers_df
    else:
        sample_pool = active_customers

    # Select random sample for performance and statistical representativeness
    sample_size = min(sample_size, len(sample_pool))
    sampled_cids = sample_pool["CustomerID"].sample(n=sample_size, random_state=42).tolist()

    logger.info(f"Running recommendation simulations for a sample of {sample_size} customers...")
    
    for count, cid in enumerate(sampled_cids, 1):
        try:
            # Generate top 10 recommendations
            recommendations = hybrid_recommend_for_customer(cid, products_df, top_n=10)
            for rec in recommendations:
                recs_collected.append(rec)
                scores_collected.append(rec["HybridScore"])
        except Exception as e:
            logger.debug(f"Failed to generate recommendations for customer {cid}: {e}")

        if count % 20 == 0:
            logger.info(f"  Processed {count}/{sample_size} customers...")

    # Create recommendations analysis dataframe
    recs_df = pd.DataFrame(recs_collected)

    # 2. Most Recommended Products chart
    plot_most_recommended(recs_df, output_dir)

    # 3. Cross-Sell Frequency chart (Market Basket Analysis on sales invoices)
    plot_cross_sell_frequency(sales_df, output_dir)

    # 4. Recommendation Score Distribution chart
    plot_score_distribution(scores_collected, output_dir)

    logger.info("Recommendation Analysis complete. All charts saved successfully.")


def plot_most_recommended(recs_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates bar chart showing the frequency of product recommendations."""
    plt.figure(figsize=(10, 6))

    if recs_df.empty:
        logger.warning("No recommendations collected. Skipping most recommended plot.")
        plt.text(0.5, 0.5, "No Recommendation Data Collected", ha='center', va='center')
        plt.title("Most Recommended Products (Sample Users)", pad=15)
        plt.tight_layout()
        plt.savefig(output_dir / "recs_most_recommended.png", dpi=120)
        plt.close()
        return

    # Count how many times each product was recommended
    top_recommended = recs_df.groupby(["ProductID", "ProductName"]).size().reset_index(name="RecommendCount")
    top_recommended = top_recommended.sort_values(by="RecommendCount", ascending=False).head(10)
    top_recommended["DisplayName"] = top_recommended["ProductName"] + " (" + top_recommended["ProductID"] + ")"

    sns.barplot(
        x="RecommendCount",
        y="DisplayName",
        hue="DisplayName",
        data=top_recommended,
        palette="flare",
        legend=False
    )
    plt.title("Top 10 Most Recommended Products (Sampled Customers)", pad=15)
    plt.xlabel("Recommendation Frequency (Counts)")
    plt.ylabel("Product Details")
    plt.tight_layout()
    plt.savefig(output_dir / "recs_most_recommended.png", dpi=120)
    plt.close()


def plot_cross_sell_frequency(sales_df: pd.DataFrame, output_dir: Path) -> None:
    """
    Generates Cross-Sell Frequency chart using Market Basket Analysis.
    Finds pairs of subcategories purchased together in the same invoice.
    """
    plt.figure(figsize=(10, 6))

    # Group sales transactions by InvoiceID to get lists of items purchased together
    invoice_groups = sales_df.groupby("InvoiceID")["SubCategory"].apply(list)

    # Count pairs co-purchased in the same invoice
    pair_counts = Counter()
    for subcats in invoice_groups:
        # Get unique subcategories per invoice to count co-purchase events (ignoring quantities)
        unique_subcats = sorted(list(set(subcats)))
        if len(unique_subcats) > 1:
            for pair in combinations(unique_subcats, 2):
                pair_counts[pair] += 1

    # Convert to DataFrame
    pairs_df = pd.DataFrame(pair_counts.items(), columns=["Pair", "Frequency"])
    
    if pairs_df.empty:
        logger.warning("No cross-sell pairs found in sales. Skipping plot.")
        plt.text(0.5, 0.5, "No Multi-item Invoices Found", ha='center', va='center')
        plt.title("Top Cross-Sell Subcategory Pairs", pad=15)
        plt.savefig(output_dir / "recs_cross_sell_frequency.png", dpi=120)
        plt.close()
        return

    pairs_df["PairName"] = pairs_df["Pair"].apply(lambda x: f"{x[0]} + {x[1]}")
    top_pairs = pairs_df.sort_values(by="Frequency", ascending=False).head(12)

    sns.barplot(
        x="Frequency",
        y="PairName",
        hue="PairName",
        data=top_pairs,
        palette="mako",
        legend=False
    )
    plt.title("Top 12 Empirically Co-purchased Subcategory Pairs (Cross-Sell Volume)", pad=15)
    plt.xlabel("Co-purchase Frequency (Invoices)")
    plt.ylabel("Product Subcategory Pairs")
    plt.tight_layout()
    plt.savefig(output_dir / "recs_cross_sell_frequency.png", dpi=120)
    plt.close()


def plot_score_distribution(scores: list, output_dir: Path) -> None:
    """Generates histogram of recommendation score distributions."""
    plt.figure(figsize=(8, 5))

    if not scores:
        logger.warning("No recommendation scores collected. Skipping score plot.")
        plt.text(0.5, 0.5, "No Score Data Collected", ha='center', va='center')
        plt.title("Recommendation Score Distribution", pad=15)
        plt.savefig(output_dir / "recs_score_distribution.png", dpi=120)
        plt.close()
        return

    sns.histplot(scores, kde=True, color=COLORS["accent"], bins=15, edgecolor="white")
    plt.title("Distribution of Recommendation Hybrid Scores", pad=15)
    plt.xlabel("Hybrid Recommendation Score")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(output_dir / "recs_score_distribution.png", dpi=120)
    plt.close()
