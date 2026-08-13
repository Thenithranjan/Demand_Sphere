"""
==============================================================================
Inventory Reporting Module: reports.py
==============================================================================
Why this file is needed:
    A supply chain department requires structured reports to execute purchasing
    and warehouse replenishment. This file acts as our **reporting engine**.
    It aggregates the optimized inventory decisions, segments them into standard SCM
    sub-reports (Low Stock, High Demand, Category, Brand, Warehouse, and Supplier),
    and exports them to `reports/inventory/` in both CSV and Markdown formats.

Business Reports Generated:
    1. Low Stock Report: Products that have breached ROP and safety lines.
    2. High Demand Report: Products facing stockouts due to forecast spikes.
    3. Warehouse Summary: Stock distributions and risk metrics per warehouse.
    4. Category Stock Report: Aggregates category performance and reorders.
    5. Brand Stock Report: Aggregates brand performance and reorders.
    6. Supplier Report: Grouped purchase order value and quantities per vendor.
==============================================================================
"""

import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Set path relative to project root
INVENTORY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = INVENTORY_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.inventory import REPORTS_DIR, logger

def generate_inventory_reports(df: pd.DataFrame) -> None:
    """
    Orchestrates the generation of all 6 operational reports.
    Saves CSV files and compiles a unified executive summary markdown report.
    """
    logger.info("Initializing inventory reporting pipeline...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Low Stock Report
    low_stock_df = df[df["InventoryStatus"].isin(["Out of Stock", "Critical Stock", "Low Stock"])].copy()
    low_stock_path = REPORTS_DIR / "low_stock_report.csv"
    low_stock_df[[
        "ProductID", "ProductName", "Category", "Warehouse", 
        "CurrentStock", "SafetyStock", "ReorderPoint", "SuggestedPurchaseQuantity", "RiskLevel"
    ]].sort_values(by="CurrentStock").to_csv(low_stock_path, index=False)
    logger.info(f"Saved Low Stock Report -> {low_stock_path} ({len(low_stock_df)} items)")
    
    # 2. High Demand Report
    high_demand_df = df[df["HighDemandAlert"] == True].copy()
    high_demand_path = REPORTS_DIR / "high_demand_report.csv"
    high_demand_df[[
        "ProductID", "ProductName", "Category", "CurrentStock", 
        "ForecastDemand", "SuggestedPurchaseQuantity", "RiskLevel"
    ]].sort_values(by="ForecastDemand", ascending=False).to_csv(high_demand_path, index=False)
    logger.info(f"Saved High Demand Report -> {high_demand_path} ({len(high_demand_df)} items)")
    
    # 3. Warehouse Summary
    # Group by warehouse and aggregate totals
    warehouse_summary = df.groupby("Warehouse").agg(
        TotalProducts=("ProductID", "count"),
        TotalCurrentStock=("CurrentStock", "sum"),
        AverageSafetyStock=("SafetyStock", "mean"),
        SuggestedOrderVolume=("SuggestedPurchaseQuantity", "sum"),
        LowStockItemsCount=("InventoryStatus", lambda x: x.isin(["Out of Stock", "Critical Stock", "Low Stock"]).sum())
    ).reset_index()
    warehouse_path = REPORTS_DIR / "warehouse_summary.csv"
    warehouse_summary.to_csv(warehouse_path, index=False)
    logger.info(f"Saved Warehouse Summary -> {warehouse_path}")
    
    # 4. Category Stock Report
    category_summary = df.groupby("Category").agg(
        TotalProducts=("ProductID", "count"),
        TotalCurrentStock=("CurrentStock", "sum"),
        TotalForecastDemand=("ForecastDemand", "sum"),
        SuggestedOrderVolume=("SuggestedPurchaseQuantity", "sum"),
        AverageUnitCost=("CostPrice", "mean"),
        EstimatedOrderCost=("SuggestedPurchaseQuantity", lambda x: (x * df.loc[x.index, "CostPrice"]).sum())
    ).reset_index()
    category_path = REPORTS_DIR / "category_stock_report.csv"
    category_summary.to_csv(category_path, index=False)
    logger.info(f"Saved Category Stock Report -> {category_path}")
    
    # 5. Brand Stock Report
    brand_summary = df.groupby("Brand").agg(
        TotalProducts=("ProductID", "count"),
        TotalCurrentStock=("CurrentStock", "sum"),
        TotalForecastDemand=("ForecastDemand", "sum"),
        SuggestedOrderVolume=("SuggestedPurchaseQuantity", "sum")
    ).reset_index().sort_values(by="SuggestedOrderVolume", ascending=False)
    brand_path = REPORTS_DIR / "brand_stock_report.csv"
    brand_summary.to_csv(brand_path, index=False)
    logger.info(f"Saved Brand Stock Report -> {brand_path}")
    
    # 6. Supplier Report (Purchase Order aggregation per vendor)
    df_copy = df.copy()
    df_copy["PurchaseOrderCost"] = df_copy["SuggestedPurchaseQuantity"] * df_copy["CostPrice"]
    
    supplier_summary = df_copy.groupby("SupplierID").agg(
        TotalItemsToOrder=("ProductID", lambda x: (df_copy.loc[x.index, "SuggestedPurchaseQuantity"] > 0).sum()),
        TotalOrderUnits=("SuggestedPurchaseQuantity", "sum"),
        TotalPurchaseOrderCost=("PurchaseOrderCost", "sum")
    ).reset_index().sort_values(by="TotalPurchaseOrderCost", ascending=False)
    supplier_path = REPORTS_DIR / "supplier_report.csv"
    supplier_summary.to_csv(supplier_path, index=False)
    logger.info(f"Saved Supplier Purchase Report -> {supplier_path}")
    
    # 7. Compile Markdown Summary
    compile_markdown_report(
        low_stock_df, high_demand_df, warehouse_summary, 
        category_summary, supplier_summary, REPORTS_DIR / "inventory_summary.md"
    )

def compile_markdown_report(
    low_stock_df: pd.DataFrame,
    high_demand_df: pd.DataFrame,
    warehouse_summary: pd.DataFrame,
    category_summary: pd.DataFrame,
    supplier_summary: pd.DataFrame,
    output_path: Path
) -> None:
    """Writes a structured markdown summary detailing SCM KPIs."""
    
    # Calculate core values
    total_suggested_units = int(category_summary["SuggestedOrderVolume"].sum())
    total_suggested_cost = float(category_summary["EstimatedOrderCost"].sum())
    total_critical_items = len(low_stock_df[low_stock_df["RiskLevel"].isin(["Critical", "High"])])
    
    md_content = f"""# Executive Inventory Optimization Summary

This report aggregates automated decisions generated by the **Smart Inventory Optimization** module.

---

## 🔑 Operational KPIs

* **Total Recommended Order Volume**: {total_suggested_units:,} Units
* **Estimated Procurement Budget Required**: ₹{total_suggested_cost:,.2f}
* **Critical Replenishment Alerts**: {total_critical_items} Products (Risk Level: Critical/High)

---

## 📦 Warehouse Inventory Allocation

| Warehouse | Total Products | Total Stock (Units) | Suggested Reorder (Units) | Low Stock SKUs |
| :--- | :--- | :--- | :--- | :--- |
"""
    # Append warehouse details
    for _, r in warehouse_summary.iterrows():
        md_content += f"| **{r['Warehouse']}** | {r['TotalProducts']} | {r['TotalCurrentStock']:,} | {r['SuggestedOrderVolume']:,} | {r['LowStockItemsCount']} |\n"
        
    md_content += """
---

## 👕 Category Breakdown

| Category | Total Stock (Units) | Next Month Forecast | Suggested Order (Units) | Est. Cost (₹) |
| :--- | :--- | :--- | :--- | :--- |
"""
    # Append category details
    for _, r in category_summary.iterrows():
        md_content += f"| {r['Category']} | {r['TotalCurrentStock']:,} | {r['TotalForecastDemand']:,} | {r['SuggestedOrderVolume']:,} | ₹{r['EstimatedOrderCost']:,.2f} |\n"

    md_content += """
---

## 🚚 Top Supplier Purchase Orders

| Supplier ID | Items to Order | Total Units | Purchase Cost (₹) |
| :--- | :--- | :--- | :--- |
"""
    # Append supplier details (Top 10)
    for _, r in supplier_summary.head(10).iterrows():
        if r["TotalOrderUnits"] > 0:
            md_content += f"| **{r['SupplierID']}** | {r['TotalItemsToOrder']} | {r['TotalOrderUnits']:,} | ₹{r['TotalPurchaseOrderCost']:,.2f} |\n"

    md_content += """
---

## 🚨 Top 10 Critical Low-Stock Products

| Product ID | Product Name | Category | Current Stock | Safety Stock | Risk Level | Suggested Order |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    # Append top 10 low stock products
    for _, r in low_stock_df.head(10).iterrows():
        md_content += f"| {r['ProductID']} | {r['ProductName']} | {r['Category']} | {r['CurrentStock']} | {r['SafetyStock']} | **{r['RiskLevel']}** | {r['SuggestedPurchaseQuantity']} |\n"

    md_content += "\n*Detailed CSV reports have been successfully generated under `reports/inventory/`.*"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    logger.info(f"Unified Markdown inventory summary report saved -> {output_path}")

if __name__ == "__main__":
    from backend.inventory.inventory_service import get_integrated_inventory_state
    from backend.inventory.reorder_engine import compute_reorder_metrics
    from backend.inventory.stock_monitor import monitor_stock_levels
    from backend.inventory.inventory_optimizer import optimize_inventory_decisions
    
    state = get_integrated_inventory_state()
    enriched = compute_reorder_metrics(state)
    monitored = monitor_stock_levels(enriched)
    optimized = optimize_inventory_decisions(monitored)
    
    generate_inventory_reports(optimized)
