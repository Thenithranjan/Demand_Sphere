"""
Retail Analytics Service
========================
Handles business logic for the retail intelligence dashboard.
Runs high-performance database aggregations on Sales, Inventory, Customers,
and Products to extract revenue trends, stock turnovers, and customer lifetime value.
"""

import logging
from typing import Dict, Any, List
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app import models

logger = logging.getLogger("analytics_service")


def get_dashboard_summary(db: Session) -> Dict[str, Any]:
    """
    Computes high-level KPI metrics for the retail intelligence dashboard.
    
    Metrics:
        - Total Revenue
        - Total Sales Quantity
        - Average Order Value (AOV)
        - Average Profit Margin (%)
        - Average Stock Utilisation (%)
        - Overall Inventory Turnover Ratio
    """
    # 1. Total Revenue and Quantity
    sales_kpis = db.query(
        func.sum(models.Sale.FinalPrice).label("total_revenue"),
        func.sum(models.Sale.Quantity).label("total_quantity"),
        func.count(models.Sale.SaleID).label("total_orders")
    ).first()

    total_revenue = float(sales_kpis.total_revenue or 0.0)
    total_quantity = int(sales_kpis.total_quantity or 0)
    total_orders = int(sales_kpis.total_orders or 0)
    
    aov = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    # 2. Average Profit Margin from Products
    avg_margin_row = db.query(func.avg(models.Product.ProfitMargin)).scalar()
    avg_margin = round(float(avg_margin_row or 0.0), 2)

    # 3. Stock Utilisation and Turnover
    inv_stats = db.query(
        func.avg(models.Inventory.StockUtilisation).label("avg_utilisation"),
        func.sum(models.Inventory.CurrentStock).label("total_stock")
    ).first()

    avg_utilisation = round(float(inv_stats.avg_utilisation or 0.0), 2)
    total_stock = int(inv_stats.total_stock or 0)
    
    # Inventory Turnover = Total Quantity Sold / Average Stock Level
    inventory_turnover = round(total_quantity / total_stock, 2) if total_stock > 0 else 0.0

    # 4. Top 5 Selling Products
    top_products_query = db.query(
        models.Product.ProductID,
        models.Product.ProductName,
        func.sum(models.Sale.Quantity).label("sold_qty"),
        func.sum(models.Sale.FinalPrice).label("revenue")
    ).join(models.Sale, models.Product.ProductID == models.Sale.ProductID)\
     .group_by(models.Product.ProductID, models.Product.ProductName)\
     .order_by(desc("sold_qty"))\
     .limit(5).all()

    top_products = [
        {
            "ProductID": row.ProductID,
            "ProductName": row.ProductName,
            "QuantitySold": int(row.sold_qty),
            "revenue": round(float(row.revenue), 2)
        }
        for row in top_products_query
    ]

    # 5. Top Categories by Revenue
    top_categories_query = db.query(
        models.Product.Category,
        func.sum(models.Sale.FinalPrice).label("revenue")
    ).join(models.Sale, models.Product.ProductID == models.Sale.ProductID)\
     .group_by(models.Product.Category)\
     .order_by(desc("revenue"))\
     .limit(5).all()

    top_categories = [
        {
            "Category": row.Category or "Uncategorized",
            "revenue": round(float(row.revenue), 2)
        }
        for row in top_categories_query
    ]

    return {
        "total_revenue": total_revenue,
        "total_quantity_sold": total_quantity,
        "average_order_value": aov,
        "average_profit_margin": avg_margin,
        "average_stock_utilisation": avg_utilisation,
        "inventory_turnover_ratio": inventory_turnover,
        "top_products": top_products,
        "top_categories": top_categories
    }


def get_sales_analytics(db: Session) -> Dict[str, Any]:
    """
    Computes monthly sales trends and product category distributions.
    """
    # 1. Monthly Sales Trend
    monthly_sales_query = db.query(
        models.Sale.SaleYear,
        models.Sale.SaleMonth,
        func.sum(models.Sale.FinalPrice).label("revenue"),
        func.sum(models.Sale.Quantity).label("quantity")
    ).group_by(models.Sale.SaleYear, models.Sale.SaleMonth)\
     .order_by(models.Sale.SaleYear, models.Sale.SaleMonth).all()

    monthly_sales = [
        {
            "month": f"{int(row.SaleYear)}-{int(row.SaleMonth):02d}",
            "total_revenue": round(float(row.revenue), 2),
            "total_quantity": int(row.quantity)
        }
        for row in monthly_sales_query if row.SaleYear and row.SaleMonth
    ]

    # 2. Sales by Subcategory
    subcat_sales_query = db.query(
        models.Product.SubCategory,
        func.sum(models.Sale.FinalPrice).label("revenue"),
        func.sum(models.Sale.Quantity).label("quantity")
    ).join(models.Sale, models.Product.ProductID == models.Sale.ProductID)\
     .group_by(models.Product.SubCategory)\
     .order_by(desc("revenue")).all()

    subcategory_distribution = [
        {
            "SubCategory": row.SubCategory or "Other",
            "total_revenue": round(float(row.revenue), 2),
            "total_quantity": int(row.quantity)
        }
        for row in subcat_sales_query
    ]

    return {
        "monthly_sales_trend": monthly_sales,
        "subcategory_sales": subcategory_distribution
    }


def get_customer_analytics(db: Session) -> Dict[str, Any]:
    """
    Analyzes customer buying power, demographics, and membership stats.
    """
    # 1. Best Customers (by total spend)
    best_customers_query = db.query(
        models.Customer.CustomerID,
        models.Customer.FullName,
        models.Customer.Membership,
        func.sum(models.Sale.FinalPrice).label("total_spend"),
        func.count(models.Sale.SaleID).label("order_count")
    ).join(models.Sale, models.Customer.CustomerID == models.Sale.CustomerID)\
     .group_by(models.Customer.CustomerID, models.Customer.FullName, models.Customer.Membership)\
     .order_by(desc("total_spend"))\
     .limit(10).all()

    best_customers = [
        {
            "CustomerID": row.CustomerID,
            "FullName": row.FullName,
            "Membership": row.Membership or "Regular",
            "total_spent": round(float(row.total_spend), 2),
            "total_orders": int(row.order_count)
        }
        for row in best_customers_query
    ]

    # 2. Membership Segment Distribution
    membership_query = db.query(
        models.Customer.Membership,
        func.count(models.Customer.CustomerID).label("count")
    ).group_by(models.Customer.Membership).all()

    membership_segments = [
        {
            "Membership": row.Membership or "Regular",
            "count": int(row.count)
        }
        for row in membership_query
    ]

    return {
        "best_customers": best_customers,
        "membership_segments": membership_segments
    }


def get_inventory_analytics(db: Session) -> Dict[str, Any]:
    """
    Analyzes inventory efficiency across warehouses and product groups.
    """
    # 1. Warehouse Stock Levels and Utilisation
    warehouse_query = db.query(
        models.Inventory.Warehouse,
        func.sum(models.Inventory.CurrentStock).label("total_stock"),
        func.avg(models.Inventory.StockUtilisation).label("avg_utilisation"),
        func.count(models.Inventory.ProductID).label("product_count")
    ).group_by(models.Inventory.Warehouse).all()

    warehouse_metrics = [
        {
            "Warehouse": row.Warehouse,
            "total_stock": int(row.total_stock or 0),
            "avg_utilisation": round(float(row.avg_utilisation or 0.0), 2),
            "product_count": int(row.product_count or 0)
        }
        for row in warehouse_query
    ]

    # 2. Stock Health Distribution (Count of Low Stock, Healthy, etc.)
    inventory_items = db.query(models.Inventory.InventoryStatus, func.count(models.Inventory.ProductID).label("count"))\
                        .group_by(models.Inventory.InventoryStatus).all()
    
    stock_health = [
        {
            "InventoryStatus": row.InventoryStatus or "Unknown",
            "count": int(row.count)
        }
        for row in inventory_items
    ]

    return {
        "warehouse_metrics": warehouse_metrics,
        "stock_health_distribution": stock_health
    }
