"""
Analytics Router
================
Exposes analytical dashboards and business intelligence endpoints.
All KPI calculations and data aggregations are performed in the Service Layer.
"""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import analytics_service

router = APIRouter(
    prefix="/analytics",
    tags=["Retail Analytics"],
)

logger = logging.getLogger("analytics_router")


@router.get(
    "/dashboard",
    status_code=status.HTTP_200_OK,
    summary="Get Retail Intelligence Dashboard Summary",
    description=(
        "Retrieves high-level performance indicators (KPIs) for the textile store:\n"
        "- **Total Revenue & Sales Volume:** Summed transaction value and quantity from MySQL.\n"
        "- **Average Order Value (AOV):** Average spent per invoice.\n"
        "- **Profit Margin & Stock Utilization:** Aggregate performance metrics.\n"
        "- **Inventory Turnover Ratio:** Product throughput compared to warehouse stock capacity.\n"
        "- **Top Products & Categories:** Ranked revenue generators."
    ),
)
def get_dashboard_kpis(db: Session = Depends(get_db)):
    """HTTP GET endpoint for dashboard summary metrics."""
    return analytics_service.get_dashboard_summary(db)


@router.get(
    "/sales",
    status_code=status.HTTP_200_OK,
    summary="Get Detailed Sales Trend Analytics",
    description=(
        "Retrieves month-over-month sales trends and revenue distribution by subcategories."
    ),
)
def get_sales_analytics(db: Session = Depends(get_db)):
    """HTTP GET endpoint for sales trend charts."""
    return analytics_service.get_sales_analytics(db)


@router.get(
    "/customers",
    status_code=status.HTTP_200_OK,
    summary="Get Customer Segment and Lifetime Value Analytics",
    description=(
        "Retrieves the store's highest spending VIP customers and membership distribution breakdown."
    ),
)
def get_customer_analytics(db: Session = Depends(get_db)):
    """HTTP GET endpoint for customer demographics and LTV segments."""
    return analytics_service.get_customer_analytics(db)


@router.get(
    "/inventory",
    status_code=status.HTTP_200_OK,
    summary="Get Warehouse Inventory Capacity Analytics",
    description=(
        "Retrieves stock quantities and utilization metrics across warehouses and stock health statuses."
    ),
)
def get_inventory_analytics(db: Session = Depends(get_db)):
    """HTTP GET endpoint for warehouse stock capacities."""
    return analytics_service.get_inventory_analytics(db)
