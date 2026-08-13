"""
==============================================================================
Customer Analysis Module: customer_analysis.py
==============================================================================
Importance of Customer Analysis:
    Customer analysis profiles the store's buyer persona. Understanding the
    demographics, buying frequency, and spend habits of customers allows
    marketing and customer relationship management (CRM) teams to target
    promotions and design loyalty programs effectively.

Business Insights Provided:
    1. Demographic Profile: Visualizes Age and Gender splits to determine if the
       primary buyer profile is younger fashion-seekers or older traditionalists.
    2. Preferred Choices: Maps customer preferences in Category and Fabric, providing
       essential signals for personalized recommendation systems.
    3. Customer Segmentation: Correlates customer tenure, membership tier, and loyalty
       points to identify high-value customer clusters.
    4. Top Spenders: Identifies VIP customers who drive disproportionate revenues,
       helping CRM plan exclusive rewards.

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

logger = logging.getLogger("analytics.customer")

def run_customer_analysis(master_df: pd.DataFrame, customers_df: pd.DataFrame, output_dir: Path) -> None:
    """
    Orchestrates the customer analysis, generates all 8 requested plots,
    and saves them in the output directory.

    Parameters
    ----------
    master_df : pd.DataFrame
        The transaction-level dataset (sales merged with products and customers).
        Used for transaction-dependent metrics (e.g. top spending customers).
    customers_df : pd.DataFrame
        The unique customer profile dataset (from customers_clean.csv).
        Used for demographic profiling to avoid transaction frequency bias.
    output_dir : Path
        Directory where generated charts will be saved.
    """
    logger.info("Starting Customer Analysis...")
    set_plot_style()
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Age Distribution
    plot_age_distribution(customers_df, output_dir)

    # 2. Gender Distribution
    plot_gender_distribution(customers_df, output_dir)

    # 3. Membership Distribution
    plot_membership_distribution(customers_df, output_dir)

    # 4. Preferred Category
    plot_preferred_category(customers_df, output_dir)

    # 5. Preferred Fabric
    plot_preferred_fabric(customers_df, output_dir)

    # 6. Top Spending Customers
    plot_top_spending_customers(master_df, output_dir)

    # 7. Customer Segmentation Overview
    plot_customer_segmentation(customers_df, output_dir)

    # 8. Loyalty Point Distribution
    plot_loyalty_distribution(customers_df, output_dir)

    logger.info("Customer Analysis complete. All charts saved successfully.")


def plot_age_distribution(customers_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates customer age distribution histogram with a KDE curve."""
    plt.figure(figsize=(8, 5))
    
    sns.histplot(data=customers_df, x="Age", kde=True, color=COLORS["primary"], bins=15, edgecolor="white")
    plt.title("Customer Age Distribution", pad=15)
    plt.xlabel("Age")
    plt.ylabel("Number of Customers")
    plt.tight_layout()
    plt.savefig(output_dir / "customer_age_distribution.png", dpi=120)
    plt.close()


def plot_gender_distribution(customers_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates customer gender distribution pie chart."""
    plt.figure(figsize=(6, 6))
    
    gender_counts = customers_df["Gender"].value_counts()
    
    # Custom colors matching brand guide
    colors_pie = [COLORS["primary"], COLORS["teal"], COLORS["secondary"]]
    
    plt.pie(
        gender_counts.values,
        labels=gender_counts.index,
        autopct='%1.1f%%',
        startangle=140,
        colors=colors_pie[:len(gender_counts)],
        textprops={'fontsize': 11, 'color': COLORS["neutral_dark"]},
        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
    )
    plt.title("Customer Gender Distribution", pad=15)
    plt.tight_layout()
    plt.savefig(output_dir / "customer_gender_distribution.png", dpi=120)
    plt.close()


def plot_membership_distribution(customers_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates membership level bar chart."""
    plt.figure(figsize=(7, 5))
    
    # Sort membership order logically
    member_order = ["Bronze", "Silver", "Gold", "Platinum"]
    member_counts = customers_df["Membership"].value_counts().reindex(member_order)
    
    sns.barplot(
        x=member_counts.index,
        y=member_counts.values,
        hue=member_counts.index,
        palette="Blues_r",
        legend=False
    )
    plt.title("Customer Membership Tier Distribution", pad=15)
    plt.xlabel("Membership Tier")
    plt.ylabel("Number of Customers")
    plt.tight_layout()
    plt.savefig(output_dir / "customer_membership_distribution.png", dpi=120)
    plt.close()


def plot_preferred_category(customers_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates chart showing preferred category distribution."""
    plt.figure(figsize=(8, 5))
    pref_cat = customers_df["PreferredCategory"].value_counts()
    
    sns.barplot(
        x=pref_cat.values,
        y=pref_cat.index,
        hue=pref_cat.index,
        palette="viridis",
        legend=False
    )
    plt.title("Preferred Categories of Customers", pad=15)
    plt.xlabel("Number of Customers")
    plt.ylabel("Preferred Category")
    plt.tight_layout()
    plt.savefig(output_dir / "customer_preferred_category.png", dpi=120)
    plt.close()


def plot_preferred_fabric(customers_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates preferred fabric distribution bar chart."""
    plt.figure(figsize=(8, 5))
    pref_fab = customers_df["PreferredFabric"].value_counts()
    
    sns.barplot(
        x=pref_fab.values,
        y=pref_fab.index,
        hue=pref_fab.index,
        palette="crest",
        legend=False
    )
    plt.title("Preferred Fabrics of Customers", pad=15)
    plt.xlabel("Number of Customers")
    plt.ylabel("Preferred Fabric")
    plt.tight_layout()
    plt.savefig(output_dir / "customer_preferred_fabric.png", dpi=120)
    plt.close()


def plot_top_spending_customers(master_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates chart showing the top 10 spending customers by transaction aggregation."""
    plt.figure(figsize=(10, 6))
    
    # Group by customer detail and sum the sales final price
    top_spenders = master_df.groupby(["CustomerID", "FullName"])["FinalPrice"].sum().reset_index()
    top_spenders = top_spenders.sort_values(by="FinalPrice", ascending=False).head(10)
    
    # Use FullName with CustomerID in brackets to handle duplicate names
    top_spenders["DisplayName"] = top_spenders["FullName"] + " (" + top_spenders["CustomerID"] + ")"
    
    sns.barplot(
        x=top_spenders["FinalPrice"] / 1e3,  # Convert to thousands ₹
        y=top_spenders["DisplayName"],
        hue=top_spenders["DisplayName"],
        palette="flare",
        legend=False
    )
    plt.title("Top 10 Spending Customers (Total Revenue contribution in Thousands ₹)", pad=15)
    plt.xlabel("Total Spend (Thousands ₹)")
    plt.ylabel("Customer Profile")
    plt.tight_layout()
    plt.savefig(output_dir / "customer_top_spenders.png", dpi=120)
    plt.close()


def plot_customer_segmentation(customers_df: pd.DataFrame, output_dir: Path) -> None:
    """
    Generates a premium segmentation scatter plot of Loyalty Points vs. Customer Tenure,
    colored by Membership Level.
    """
    plt.figure(figsize=(9, 6))
    
    # Sort membership categories for consistent legend
    hue_order = ["Bronze", "Silver", "Gold", "Platinum"]
    
    sns.scatterplot(
        data=customers_df,
        x="CustomerTenureDays",
        y="LoyaltyPoints",
        hue="Membership",
        hue_order=hue_order,
        palette="Set1",
        alpha=0.6,
        edgecolor=None
    )
    
    plt.title("Customer Segmentation Overview (Tenure vs. Loyalty Points)", pad=15)
    plt.xlabel("Customer Tenure (Days)")
    plt.ylabel("Loyalty Points")
    plt.legend(title="Membership Level", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(output_dir / "customer_segmentation_overview.png", dpi=120)
    plt.close()


def plot_loyalty_distribution(customers_df: pd.DataFrame, output_dir: Path) -> None:
    """Generates loyalty points distribution histogram."""
    plt.figure(figsize=(8, 5))
    
    sns.histplot(data=customers_df, x="LoyaltyPoints", kde=True, color=COLORS["secondary"], bins=15, edgecolor="white")
    plt.title("Distribution of Customer Loyalty Points", pad=15)
    plt.xlabel("Loyalty Points")
    plt.ylabel("Number of Customers")
    plt.tight_layout()
    plt.savefig(output_dir / "customer_loyalty_distribution.png", dpi=120)
    plt.close()
