"""
==============================================================================
EDA Orchestrator Script: run_eda.py
==============================================================================
Importance of the Orchestrator:
    A centralized orchestrator provides a single entry point for running the
    entire analytical pipeline. It guarantees execution order, aggregates data
    dependencies, saves the master dataset, and creates a consolidated executive
    report.

Business Insights Provided:
    1. Key Business Metrics: Programmatically calculates core retail indicators
       (total revenue, active customers, product count, and inventory risks)
       and includes them in a dynamic summary report.
    2. Document Consolidation: Generates `eda_summary.md` with embedded charts,
       connecting technical figures with actionable business strategies.

==============================================================================
"""

import os
import sys
import logging
import time
from pathlib import Path
import pandas as pd

# Ensure project root is in sys.path
ANALYTICS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ANALYTICS_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import individual analysis modules
from backend.analytics import DATA_DIR, REPORTS_DIR, logger
from backend.analytics.sales_analysis import run_sales_analysis
from backend.analytics.customer_analysis import run_customer_analysis
from backend.analytics.product_analysis import run_product_analysis
from backend.analytics.inventory_analysis import run_inventory_analysis
from backend.analytics.recommendation_analysis import run_recommendation_analysis

def create_master_dataset(sales_df: pd.DataFrame, products_df: pd.DataFrame, customers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates and saves the merged master dataset from transactions, products, and customers.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Cleaned transactions table.
    products_df : pd.DataFrame
        Cleaned product table.
    customers_df : pd.DataFrame
        Cleaned customer profiles.

    Returns
    -------
    pd.DataFrame
        Merged master dataset.
    """
    logger.info("Merging datasets to create master_dataset.csv...")

    # Rename clashing columns to maintain semantic clarity
    # 'Gender' exists in both products (target gender) and customers (customer's gender)
    products_for_merge = products_df.rename(columns={"Gender": "ProductGender"})
    customers_for_merge = customers_df.rename(columns={"Gender": "CustomerGender"})

    # Drop 'SubCategory' from products since it is already present in sales_df.
    # Alternatively, drop it from sales and keep the products master metadata.
    sales_for_merge = sales_df.drop(columns=["SubCategory"])

    # Merge tables: transactions -> products -> customers
    master_df = pd.merge(sales_for_merge, products_for_merge, on="ProductID", how="left")
    master_df = pd.merge(master_df, customers_for_merge, on="CustomerID", how="left")

    # Save to data/processed
    master_path = DATA_DIR / "master_dataset.csv"
    master_df.to_csv(master_path, index=False)
    logger.info(f"Master dataset successfully created and saved -> {master_path}")
    logger.info(f"Shape of master dataset: {master_df.shape}")

    return master_df

def generate_summary_report(
    master_df: pd.DataFrame, 
    customers_df: pd.DataFrame, 
    products_df: pd.DataFrame, 
    inventory_df: pd.DataFrame,
    output_path: Path
) -> None:
    """
    Programmatically compiles the final business markdown report (eda_summary.md),
    embedding statistics and links to generated charts.
    """
    logger.info("Generating final executive summary report...")

    # Calculate actual statistics for the report
    total_revenue = master_df["FinalPrice"].sum()
    total_transactions = master_df["SaleID"].nunique()
    total_customers = customers_df["CustomerID"].nunique()
    total_products = products_df["ProductID"].nunique()
    avg_age = customers_df["Age"].mean()
    avg_profit_margin = products_df["ProfitMargin"].mean()
    
    low_stock_count = inventory_df[inventory_df["CurrentStock"] <= inventory_df["MinimumStock"]].shape[0]
    reorder_count = inventory_df[inventory_df["CurrentStock"] <= inventory_df["ReorderPoint"]].shape[0]
    total_stock = inventory_df["CurrentStock"].sum()

    # Define markdown content with dynamic statistics and images
    report_content = f"""# Executive EDA Summary: Retail Intelligence System

This report summarizes the findings of the Exploratory Data Analysis (EDA) module for the **AI-Powered Retail Intelligence System for Textile Stores**. All calculations are compiled dynamically from the processed retail datasets.

---

## 📊 Core Business KPIs

| Metric | Value | Business Significance |
| :--- | :--- | :--- |
| **Total Sales Revenue** | ₹{total_revenue:,.2f} | Represents the gross sales volume across the entire transactional history. |
| **Total Transactions** | {total_transactions:,} | Total count of sales invoices, showing customer traffic volume. |
| **Active Customers Profiled** | {total_customers:,} | Total unique customers logged in the CRM profile database. |
| **Active Products in Catalog** | {total_products:,} | Size of the catalog variety across category segments. |
| **Average Customer Age** | {avg_age:.1f} Years | Average demographic age profile of the stores' shoppers. |
| **Average Product Profit Margin** | {avg_profit_margin:.2f}% | Expected margin buffer to absorb discounts and promotions. |
| **Low-Stock Alert Items** | {low_stock_count} Products | Catalog items currently sitting at or below minimum stock thresholds. |
| **Reorder Triggers Reached** | {reorder_count} Products | Items that have breached reorder thresholds and require restock orders. |
| **Total Inventory Volume** | {total_stock:,} Units | Total stock units currently held across all warehouses. |

---

## 📈 Sales Insights

### Key Trends & Observations
1. **Monthly Sales Performance**: The time-series graphs trace transaction volumes and revenue growth. Spike periods highlight promotional success.
2. **Seasonal & Festival Dynamics**: Festivals like Diwali and Pongal drive massive revenue contribution, confirming the critical role of seasonal apparel stocks.
3. **Weekend Traffic spikes**: Sales volume on weekends compared to weekdays highlights the need for active staffing and real-time weekend promotions.

### Visualizations
`carousel
![Monthly Sales Trend](sales_monthly_trend.png)
<!-- slide -->
![Revenue Trend](sales_revenue_trend.png)
<!-- slide -->
![Quantity Sold Trend](sales_quantity_trend.png)
<!-- slide -->
![Festival Sales Contribution](sales_festival.png)
<!-- slide -->
![Seasonal Sales Contribution](sales_seasonal.png)
<!-- slide -->
![Top Products](sales_top_products.png)
<!-- slide -->
![Top Categories](sales_top_categories.png)
<!-- slide -->
![Top Brands](sales_top_brands.png)
<!-- slide -->
![Daily Distribution](sales_daily_distribution.png)
<!-- slide -->
![Weekend vs Weekday](sales_weekend_weekday.png)
`

---

## 👥 Customer Insights

### Key Trends & Observations
1. **Demographic Target**: Age distributions reveal whether the buyer profile skew is youthful or mature, letting marketing adjust catalog campaigns.
2. **Membership Loyalty**: Loyalty program distribution details the sizes of Silver, Gold, and Platinum cohorts, proving the value of loyalty points.
3. **Customer Value Segmentation**: The Tenure vs. Loyalty Points scatter plot identifies the highest value VIP groups who have long tenures and high loyalty scores.

### Visualizations
`carousel
![Age Distribution](customer_age_distribution.png)
<!-- slide -->
![Gender Distribution](customer_gender_distribution.png)
<!-- slide -->
![Membership Distribution](customer_membership_distribution.png)
<!-- slide -->
![Preferred Category](customer_preferred_category.png)
<!-- slide -->
![Preferred Fabric](customer_preferred_fabric.png)
<!-- slide -->
![Top Spenders](customer_top_spenders.png)
<!-- slide -->
![Loyalty Distribution](customer_loyalty_distribution.png)
<!-- slide -->
![Segmentation Scatter](customer_segmentation_overview.png)
`

---

## 👕 Product Insights

### Key Trends & Observations
1. **Catalog Density**: Product counts across category, brand, and fabric groupings show where inventory investments are focused.
2. **Pricing Structure**: The retail price distribution displays whether product offerings align with budget, premium, or luxury categories.
3. **Profit Margins**: Profit margin distributions show where margins concentrate, helping plan catalog markdowns.

### Visualizations
`carousel
![Product Category Distribution](product_category_distribution.png)
<!-- slide -->
![Product Brand Distribution](product_brand_distribution.png)
<!-- slide -->
![Product Fabric Distribution](product_fabric_distribution.png)
<!-- slide -->
![Product Price Distribution](product_price_distribution.png)
<!-- slide -->
![Product Profit Distribution](product_profit_distribution.png)
<!-- slide -->
![Product Seasonal Demand](product_seasonal_distribution.png)
`

---

## 📦 Inventory Insights

### Key Trends & Observations
1. **Low Stock Risks**: Highlights products that have breached safety lines, indicating potential stockout loss if not replinished.
2. **Overstock Assets**: Pinpoints products exceeding maximum thresholds, which ties up warehouse space and cash flow.
3. **Warehouse Allocation**: Distribution of current stock across Chennai, Madurai, and Coimbatore locations.
4. **Reorder Urgency**: Comparative visual check of current stock against reorder points flags critical procurement needs.

### Visualizations
`carousel
![Stock Distribution](inventory_stock_distribution.png)
<!-- slide -->
![Low Stock Products](inventory_low_stock.png)
<!-- slide -->
![Overstock Products](inventory_overstock.png)
<!-- slide -->
![Warehouse Stocks](inventory_warehouse_stock.png)
<!-- slide -->
![Safety Stock Analysis](inventory_safety_stock.png)
<!-- slide -->
![Reorder Point Analysis](inventory_reorder_point.png)
`

---

## 🤖 Recommendation Insights

### Key Trends & Observations
1. **Catalog Coverage Bias**: Tracks the most frequently recommended products to see if recommendation models have a popularity bias.
2. **Empirical Cross-Sell Co-occurrences**: Shows which item subcategories (e.g. Shirts + Pants) are bought together in historical sales invoices, validating complementary rules.
3. **Score Distribution**: The distribution of hybrid recommendation scores verifies the confidence of customer match rates.

### Visualizations
`carousel
![Most Recommended Products](recs_most_recommended.png)
<!-- slide -->
![Cross-Sell Co-occurrences](recs_cross_sell_frequency.png)
<!-- slide -->
![Score Distribution](recs_score_distribution.png)
`
"""
    # Write report content to file (replacing backticks in carousel strings with actual backticks)
    processed_content = report_content.replace("`carousel", "````carousel").replace("`\n", "````\n")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(processed_content)
        
    logger.info(f"Executive report generated successfully -> {output_path}")


def main() -> int:
    """
    Main orchestrator function for EDA.
    Loads datasets, creates master, executes sub-analyses, and generates the final report.
    """
    start_time = time.time()
    logger.info("=" * 70)
    logger.info("🎬 RETAIL PRODUCT RECOMMENDATION — EXPLORATORY DATA ANALYSIS (EDA)")
    logger.info("=" * 70)

    try:
        # Step 1: Load individual cleaned datasets
        sales_path = DATA_DIR / "sales_clean.csv"
        products_path = DATA_DIR / "products_clean.csv"
        customers_path = DATA_DIR / "customers_clean.csv"
        inventory_path = DATA_DIR / "inventory_clean.csv"

        for p in [sales_path, products_path, customers_path, inventory_path]:
            if not p.exists():
                raise FileNotFoundError(f"Required clean dataset missing: {p}")

        logger.info("Loading cleaned datasets from data/processed/...")
        sales_df = pd.read_csv(sales_path)
        products_df = pd.read_csv(products_path)
        customers_df = pd.read_csv(customers_path)
        inventory_df = pd.read_csv(inventory_path)

        # Step 2: Create master aggregation dataset
        master_df = create_master_dataset(sales_df, products_df, customers_df)

        # Step 3: Run Sales Analysis
        logger.info("Running Sales Analysis module...")
        run_sales_analysis(master_df, REPORTS_DIR)

        # Step 4: Run Customer Analysis
        logger.info("Running Customer Analysis module...")
        run_customer_analysis(master_df, customers_df, REPORTS_DIR)

        # Step 5: Run Product Analysis
        logger.info("Running Product Analysis module...")
        run_product_analysis(products_df, REPORTS_DIR)

        # Step 6: Run Inventory Analysis
        logger.info("Running Inventory Analysis module...")
        run_inventory_analysis(inventory_df, products_df, REPORTS_DIR)

        # Step 7: Run Recommendation Analysis
        logger.info("Running Recommendation Analysis module...")
        run_recommendation_analysis(sales_df, customers_df, products_df, REPORTS_DIR, sample_size=100)

        # Step 8: Generate summary executive report
        report_path = REPORTS_DIR / "eda_summary.md"
        generate_summary_report(master_df, customers_df, products_df, inventory_df, report_path)

        duration = time.time() - start_time
        logger.info("=" * 70)
        logger.info(f"🎉 EDA RUN COMPLETED SUCCESSFULLY in {duration:.2f} seconds!")
        logger.info(f"All graphs and summary report are saved under: {REPORTS_DIR}")
        logger.info("=" * 70)
        return 0

    except Exception as e:
        logger.error(f"Critical error during EDA execution: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
