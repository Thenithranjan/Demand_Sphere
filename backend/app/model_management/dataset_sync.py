"""
Dataset Synchronisation Service
================================
Exports the latest data from MySQL tables into CSV files before every
training run, ensuring the ML pipeline always trains on fresh data.

MySQL is the PRIMARY SOURCE OF TRUTH. CSV files are generated from MySQL before training.
Includes backup rotation and synchronization statistics.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from app import models
from . import DATA_DIR, PROJECT_ROOT

logger = logging.getLogger("model_management.dataset_sync")

BACKUP_DIR = PROJECT_ROOT / "data" / "backups"
MAX_BACKUPS = 5

def create_csv_backup(file_path: Path):
    """
    Create a timestamped backup of the CSV file in data/backups/
    and enforce a retention policy keeping at most MAX_BACKUPS files.
    """
    if not file_path.exists():
        return
        
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d")
        backup_filename = f"{file_path.stem}_{timestamp}.csv"
        backup_path = BACKUP_DIR / backup_filename
        
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created CSV backup: {backup_path}")
        
        # Enforce retention policy: keep only the last MAX_BACKUPS for this file stem
        prefix = f"{file_path.stem}_"
        backups = sorted(
            [f for f in BACKUP_DIR.glob(f"{prefix}*.csv")],
            key=lambda x: x.stat().st_mtime
        )
        while len(backups) > MAX_BACKUPS:
            oldest = backups.pop(0)
            try:
                oldest.unlink()
                logger.info(f"Deleted old backup: {oldest}")
            except Exception as e:
                logger.warning(f"Failed to delete old backup {oldest}: {e}")
                
    except Exception as e:
        logger.error(f"Failed to create backup for {file_path.name}: {e}")


def _compare_and_sync(
    new_df: pd.DataFrame,
    file_path: Path,
    pk_cols: Any,
) -> Dict[str, int]:
    """
    Compare new DataFrame from DB with existing CSV file and compute sync stats.
    Saves new DataFrame to CSV after creating a backup.
    """
    stats = {"added": 0, "updated": 0, "deleted": 0, "total": len(new_df)}
    
    # 1. Handle missing/empty existing CSV
    if not file_path.exists():
        stats["added"] = len(new_df)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        new_df.to_csv(file_path, index=False)
        return stats
        
    try:
        old_df = pd.read_csv(file_path)
    except Exception as e:
        logger.warning(f"Could not read existing CSV {file_path.name}: {e}. Treating as all new.")
        stats["added"] = len(new_df)
        create_csv_backup(file_path)
        new_df.to_csv(file_path, index=False)
        return stats

    # 2. Check for duplicate primary keys in new data and drop them
    new_df = new_df.drop_duplicates(subset=pk_cols, keep="first")
    old_df = old_df.drop_duplicates(subset=pk_cols, keep="first")

    # 3. Create Backup
    create_csv_backup(file_path)

    # 4. Compare old vs new
    try:
        if isinstance(pk_cols, list):
            # Composite keys: convert to string tuples for set operations
            old_keys = set(tuple(x) for x in old_df[pk_cols].to_numpy())
            new_keys = set(tuple(x) for x in new_df[pk_cols].to_numpy())
        else:
            old_keys = set(old_df[pk_cols].to_numpy())
            new_keys = set(new_df[pk_cols].to_numpy())
            
        added_keys = new_keys - old_keys
        deleted_keys = old_keys - new_keys
        common_keys = old_keys & new_keys
        
        stats["added"] = len(added_keys)
        stats["deleted"] = len(deleted_keys)
        
        # Calculate updated rows
        if common_keys:
            old_indexed = old_df.set_index(pk_cols)
            new_indexed = new_df.set_index(pk_cols)
            
            # Keep common columns to compare
            common_cols = [c for c in new_indexed.columns if c in old_indexed.columns]
            
            # Align rows
            common_old_rows = old_indexed.loc[list(common_keys), common_cols].sort_index()
            common_new_rows = new_indexed.loc[list(common_keys), common_cols].sort_index()
            
            # Compare value equality (fillna to avoid NaN mismatch)
            diff_mask = (common_old_rows.fillna("") != common_new_rows.fillna("")).any(axis=1)
            stats["updated"] = int(diff_mask.sum())
            
    except Exception as e:
        logger.warning(f"Error comparing datasets for {file_path.name}: {e}. Overwriting without full diff stats.")
        stats["added"] = max(0, len(new_df) - len(old_df))

    # 5. Overwrite CSV file with the updated MySQL data
    new_df.to_csv(file_path, index=False)
    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# Individual Sync Functions
# ═══════════════════════════════════════════════════════════════════════════════

def sync_products(db: Session) -> Dict[str, int]:
    """Sync products table to data/processed/products_clean.csv"""
    logger.info("Synchronizing Products table...")
    products = db.query(models.Product).all()
    if not products:
        raise RuntimeError("Products table in MySQL is empty — sync halted.")
        
    data = [
        {
            "ProductID": p.ProductID,
            "SKU": p.SKU,
            "ProductName": p.ProductName,
            "Category": p.Category,
            "SubCategory": p.SubCategory,
            "Brand": p.Brand,
            "Color": p.Color,
            "Size": p.Size,
            "Fabric": p.Fabric,
            "SeasonalDemandTag": p.SeasonalDemandTag,
            "Gender": p.Gender,
            "Price": p.Price,
            "CostPrice": p.CostPrice,
            "SupplierID": p.SupplierID,
            "ProductStatus": p.ProductStatus,
            "ImageURL": p.ImageURL,
            "ProfitMargin": p.ProfitMargin,
        }
        for p in products
    ]
    df = pd.DataFrame(data)
    file_path = DATA_DIR / "products_clean.csv"
    return _compare_and_sync(df, file_path, "ProductID")


def sync_customers(db: Session) -> Dict[str, int]:
    """Sync customers table to data/processed/customers_clean.csv"""
    logger.info("Synchronizing Customers table...")
    customers = db.query(models.Customer).all()
    if not customers:
        raise RuntimeError("Customers table in MySQL is empty — sync halted.")
        
    data = [
        {
            "CustomerID": c.CustomerID,
            "FullName": c.FullName,
            "Gender": c.Gender,
            "Age": c.Age,
            "City": c.City,
            "State": c.State,
            "Membership": c.Membership,
            "JoinDate": c.JoinDate,
            "PreferredCategory": c.PreferredCategory,
            "PreferredFabric": c.PreferredFabric,
            "PreferredPriceRange": c.PreferredPriceRange,
            "LoyaltyPoints": c.LoyaltyPoints,
            "CustomerTenureDays": c.CustomerTenureDays,
        }
        for c in customers
    ]
    df = pd.DataFrame(data)
    file_path = DATA_DIR / "customers_clean.csv"
    return _compare_and_sync(df, file_path, "CustomerID")


def sync_sales(db: Session) -> Dict[str, int]:
    """Sync sales table to data/processed/sales_clean.csv"""
    logger.info("Synchronizing Sales table...")
    sales = db.query(models.Sale).all()
    if not sales:
        raise RuntimeError("Sales table in MySQL is empty — sync halted.")
        
    data = [
        {
            "SaleID": s.SaleID,
            "InvoiceID": s.InvoiceID,
            "CustomerID": s.CustomerID,
            "ProductID": s.ProductID,
            "SubCategory": s.SubCategory,
            "SaleDate": s.SaleDate,
            "Quantity": s.Quantity,
            "MRP": s.MRP,
            "DiscountPercent": s.DiscountPercent,
            "FinalPrice": s.FinalPrice,
            "Festival": s.Festival,
            "Season": s.Season,
            "DayOfWeek": s.DayOfWeek,
            "SaleMonth": s.SaleMonth,
            "SaleYear": s.SaleYear,
        }
        for s in sales
    ]
    df = pd.DataFrame(data)
    file_path = DATA_DIR / "sales_clean.csv"
    return _compare_and_sync(df, file_path, "SaleID")


def sync_inventory(db: Session) -> Dict[str, int]:
    """Sync inventory table to data/processed/inventory_clean.csv"""
    logger.info("Synchronizing Inventory table...")
    inventory = db.query(models.Inventory).all()
    
    data = [
        {
            "ProductID": i.ProductID,
            "Warehouse": i.Warehouse,
            "CurrentStock": i.CurrentStock,
            "MinimumStock": i.MinimumStock,
            "MaximumStock": i.MaximumStock,
            "SafetyStock": i.SafetyStock,
            "ReorderPoint": i.ReorderPoint,
            "LeadTimeDays": i.LeadTimeDays,
            "SupplierID": i.SupplierID,
            "LastRestocked": i.LastRestocked,
            "InventoryStatus": i.InventoryStatus,
            "StockUtilisation": i.StockUtilisation,
            "DaysSinceRestock": i.DaysSinceRestock,
        }
        for i in inventory
    ]
    df = pd.DataFrame(data)
    file_path = DATA_DIR / "inventory_clean.csv"
    return _compare_and_sync(df, file_path, "ProductID")


def sync_forecast_results(db: Session) -> Dict[str, int]:
    """Sync forecast results to data/processed/forecast_results.csv"""
    logger.info("Synchronizing ForecastResults table...")
    forecasts = db.query(models.ForecastResult).all()
    
    data = [
        {
            "ProductID": fr.ProductID,
            "YearMonth": fr.YearMonth,
            "Quantity": fr.Quantity,
            "Revenue": fr.Revenue,
            "Category": fr.Category,
            "SubCategory": fr.SubCategory,
            "Brand": fr.Brand,
            "Price": fr.Price,
            "Year": fr.Year,
            "Month": fr.Month,
            "Quarter": fr.Quarter,
            "Week": fr.Week,
            "Day": fr.Day,
            "AveragePrice": fr.AveragePrice,
            "Season": fr.Season,
            "Festival": fr.Festival,
            "TargetQuantity": fr.TargetQuantity,
            "TargetRevenue": fr.TargetRevenue,
        }
        for fr in forecasts
    ]
    df = pd.DataFrame(data)
    file_path = DATA_DIR / "forecast_results.csv"
    # Composite PK
    return _compare_and_sync(df, file_path, ["ProductID", "YearMonth"])


# ═══════════════════════════════════════════════════════════════════════════════
# Aggregate Sync Orchestrator & Status checks
# ═══════════════════════════════════════════════════════════════════════════════

def sync_datasets_from_db(
    db: Session,
    progress: Any = None,
) -> Dict[str, int]:
    """
    Synchronizes all five tables and returns the consolidated row counts.
    """
    if progress:
        progress.update("Synchronizing CSV")
        
    p_stats = sync_products(db)
    c_stats = sync_customers(db)
    s_stats = sync_sales(db)
    i_stats = sync_inventory(db)
    f_stats = sync_forecast_results(db)
    
    return {
        "products": p_stats["total"],
        "customers": c_stats["total"],
        "sales": s_stats["total"],
        "inventory": i_stats["total"],
        "forecast_results": f_stats["total"],
    }


def get_dataset_status(db: Session) -> Dict[str, Any]:
    """
    Compares the row counts of MySQL tables vs processed CSV files.
    Returns status mapping for Products, Customers, Sales, Inventory, and ForecastResults.
    """
    datasets = [
        ("Products", models.Product, DATA_DIR / "products_clean.csv"),
        ("Customers", models.Customer, DATA_DIR / "customers_clean.csv"),
        ("Sales", models.Sale, DATA_DIR / "sales_clean.csv"),
        ("Inventory", models.Inventory, DATA_DIR / "inventory_clean.csv"),
        ("ForecastResults", models.ForecastResult, DATA_DIR / "forecast_results.csv"),
    ]
    
    status_details = {}
    
    for name, orm_model, csv_path in datasets:
        db_count = db.query(orm_model).count()
        
        csv_count = 0
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                csv_count = len(df)
            except Exception:
                csv_count = 0
                
        diff = abs(db_count - csv_count)
        
        if not csv_path.exists():
            status = "Sync Required"
        elif diff == 0:
            status = "Synchronized"
        else:
            status = "Sync Required"
            
        status_details[name] = {
            "database_count": db_count,
            "csv_count": csv_count,
            "difference": diff,
            "status": status,
        }
        
    return status_details
