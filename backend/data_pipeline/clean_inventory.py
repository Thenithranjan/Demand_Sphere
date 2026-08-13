"""
==============================================================================
Script: clean_inventory.py
==============================================================================
Purpose:
    Cleans and standardises the raw inventory dataset
    (inventory_500_textile_dataset.xlsx) after validation.

Cleaning Operations:
    1. Strip whitespace from all text columns
    2. Normalise Warehouse, InventoryStatus to canonical values
    3. Parse LastRestocked to datetime and format as YYYY-MM-DD
    4. Ensure all stock columns are non-negative integers
    5. Fix logical inconsistencies (MinStock >= MaxStock)
    6. Recalculate InventoryStatus based on actual CurrentStock levels
    7. Drop fully duplicated rows
    8. Drop rows with null ProductID
    9. Add StockUtilisation and DaysSinceRestock derived columns

Output:
    data/processed/inventory_clean.csv
==============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import os
import sys
import logging
from typing import List

import pandas as pd

# =============================================================================
# CONSTANTS
# =============================================================================
RAW_FILE_PATH: str = os.path.join("data", "raw", "inventory_500_textile_dataset.xlsx")
OUTPUT_DIR: str = os.path.join("data", "processed")
OUTPUT_FILE: str = os.path.join(OUTPUT_DIR, "inventory_clean.csv")

TEXT_COLUMNS: List[str] = [
    "ProductID", "Warehouse", "SupplierID", "InventoryStatus"
]

STOCK_COLUMNS: List[str] = [
    "CurrentStock", "MinimumStock", "MaximumStock",
    "SafetyStock", "ReorderPoint", "LeadTimeDays"
]

VALID_WAREHOUSES = ["Chennai WH", "Madurai WH", "Coimbatore WH"]
VALID_STATUSES = ["Healthy", "Reorder Required", "Out of Stock", "Overstock"]

# =============================================================================
# LOGGING
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# =============================================================================
# CLEANING FUNCTIONS
# =============================================================================
def load_raw_data(file_path: str) -> pd.DataFrame:
    """Load the raw Excel file."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Raw data file not found: {file_path}")

    df = pd.read_excel(file_path, engine="openpyxl")
    logger.info(f"Loaded '{file_path}' → {df.shape[0]} rows × {df.shape[1]} columns")
    return df


def strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from all text columns."""
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    logger.info("Stripped whitespace from text columns")
    return df


def normalise_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise Warehouse and InventoryStatus to canonical values."""
    if "Warehouse" in df.columns:
        df["Warehouse"] = df["Warehouse"].str.strip().str.title()
        # Fix title-case for "WH" → should remain uppercase
        df["Warehouse"] = df["Warehouse"].str.replace(" Wh", " WH", regex=False)

    if "InventoryStatus" in df.columns:
        df["InventoryStatus"] = df["InventoryStatus"].str.strip().str.title()
        status_map = {
            "Out Of Stock": "Out of Stock",
            "Reorder Required": "Reorder Required",
        }
        df["InventoryStatus"] = df["InventoryStatus"].replace(status_map)

    logger.info("Normalised categorical columns")
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse LastRestocked to datetime and format as YYYY-MM-DD."""
    if "LastRestocked" in df.columns:
        df["LastRestocked"] = pd.to_datetime(df["LastRestocked"], errors="coerce")
        unparseable = int(df["LastRestocked"].isna().sum())
        if unparseable > 0:
            logger.warning(f"{unparseable} unparseable LastRestocked value(s)")
        df["LastRestocked"] = df["LastRestocked"].dt.strftime("%Y-%m-%d")
        logger.info("Parsed and formatted LastRestocked → YYYY-MM-DD")
    return df


def fix_stock_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix stock-related columns:
    - Convert to numeric
    - Clamp negative values to 0
    - Ensure LeadTimeDays >= 1
    """
    for col in STOCK_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Clamp negatives to 0
    for col in ["CurrentStock", "MinimumStock", "MaximumStock", "SafetyStock", "ReorderPoint"]:
        if col in df.columns:
            negatives = int((df[col] < 0).sum())
            df[col] = df[col].clip(lower=0)
            if negatives > 0:
                logger.warning(f"Clamped {negatives} negative {col} value(s) to 0")

    # Ensure LeadTimeDays >= 1
    if "LeadTimeDays" in df.columns:
        clamped = int((df["LeadTimeDays"] < 1).sum())
        df["LeadTimeDays"] = df["LeadTimeDays"].clip(lower=1)
        if clamped > 0:
            logger.warning(f"Clamped {clamped} LeadTimeDays value(s) to minimum 1")

    logger.info("Fixed stock column values and types")
    return df


def fix_logical_inconsistencies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix logical issues:
    - If MinimumStock >= MaximumStock, swap them
    - If SafetyStock > MaximumStock, cap SafetyStock at MaximumStock
    - If ReorderPoint outside [MinimumStock, MaximumStock], clamp it
    """
    if all(col in df.columns for col in ["MinimumStock", "MaximumStock"]):
        # Swap Min/Max where Min >= Max
        swap_mask = df["MinimumStock"] >= df["MaximumStock"]
        swap_count = int(swap_mask.sum())
        if swap_count > 0:
            df.loc[swap_mask, ["MinimumStock", "MaximumStock"]] = (
                df.loc[swap_mask, ["MaximumStock", "MinimumStock"]].values
            )
            logger.warning(f"Swapped MinimumStock/MaximumStock for {swap_count} row(s)")

    if all(col in df.columns for col in ["SafetyStock", "MaximumStock"]):
        over_max = df["SafetyStock"] > df["MaximumStock"]
        over_count = int(over_max.sum())
        if over_count > 0:
            df.loc[over_max, "SafetyStock"] = df.loc[over_max, "MaximumStock"]
            logger.warning(f"Capped SafetyStock to MaximumStock for {over_count} row(s)")

    if all(col in df.columns for col in ["ReorderPoint", "MinimumStock", "MaximumStock"]):
        df["ReorderPoint"] = df["ReorderPoint"].clip(
            lower=df["MinimumStock"], upper=df["MaximumStock"]
        )
        logger.info("Clamped ReorderPoint within [MinimumStock, MaximumStock]")

    return df


def recalculate_inventory_status(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recalculate InventoryStatus based on actual stock levels:
    - CurrentStock == 0           → 'Out of Stock'
    - CurrentStock <= ReorderPoint → 'Reorder Required'
    - CurrentStock > MaximumStock  → 'Overstock'
    - Otherwise                   → 'Healthy'
    """
    if all(col in df.columns for col in ["CurrentStock", "ReorderPoint", "MaximumStock"]):
        conditions = [
            df["CurrentStock"] == 0,
            df["CurrentStock"] <= df["ReorderPoint"],
            df["CurrentStock"] > df["MaximumStock"],
        ]
        choices = ["Out of Stock", "Reorder Required", "Overstock"]
        df["InventoryStatus"] = pd.Series(
            pd.Categorical(
                pd.cut(df["CurrentStock"], bins=[-1, 0, df["ReorderPoint"].max(), df["MaximumStock"].max(), float("inf")],
                       labels=False),
            )
        ).astype(str)

        # Use numpy-style select for clarity
        import numpy as np
        df["InventoryStatus"] = np.select(conditions, choices, default="Healthy")
        logger.info("Recalculated InventoryStatus based on stock levels")
    return df


def handle_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Drop fully duplicated rows."""
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    if removed > 0:
        logger.warning(f"Removed {removed} fully duplicated row(s)")
    else:
        logger.info("No duplicate rows found")
    return df


def handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Handle null values — drop rows with null ProductID, fill others."""
    before = len(df)
    df = df.dropna(subset=["ProductID"])
    dropped = before - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} row(s) with null ProductID")

    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    for col in STOCK_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    total_nulls = int(df.isnull().sum().sum())
    logger.info(f"Null handling complete — {total_nulls} null(s) remaining")
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived analytics columns:
    - StockUtilisation = CurrentStock / MaximumStock * 100
    - DaysSinceRestock = days since LastRestocked
    """
    if all(col in df.columns for col in ["CurrentStock", "MaximumStock"]):
        df["StockUtilisation"] = (
            (df["CurrentStock"] / df["MaximumStock"].replace(0, 1)) * 100
        ).round(2)
        logger.info("Added StockUtilisation column")

    if "LastRestocked" in df.columns:
        try:
            restock_dates = pd.to_datetime(df["LastRestocked"], errors="coerce")
            today = pd.Timestamp.now()
            df["DaysSinceRestock"] = (today - restock_dates).dt.days
            df["DaysSinceRestock"] = df["DaysSinceRestock"].fillna(0).astype(int)
            logger.info("Added DaysSinceRestock column")
        except Exception as e:
            logger.warning(f"Could not compute DaysSinceRestock: {e}")
    return df


def save_clean_data(df: pd.DataFrame, output_path: str) -> None:
    """Save the cleaned DataFrame to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"Saved cleaned data → '{output_path}' ({df.shape[0]} rows × {df.shape[1]} columns)")


# =============================================================================
# ORCHESTRATOR
# =============================================================================
def run_cleaning() -> bool:
    """Run the complete cleaning pipeline for inventory."""
    logger.info("=" * 60)
    logger.info("STARTING CLEANING: Inventory Dataset")
    logger.info("=" * 60)

    try:
        df = load_raw_data(RAW_FILE_PATH)
        df = strip_whitespace(df)
        df = normalise_categoricals(df)
        df = parse_dates(df)
        df = fix_stock_values(df)
        df = fix_logical_inconsistencies(df)
        df = recalculate_inventory_status(df)
        df = handle_duplicates(df)
        df = handle_nulls(df)
        df = add_derived_columns(df)
        save_clean_data(df, OUTPUT_FILE)

        logger.info("🎉 Inventory cleaning COMPLETED successfully")
        return True

    except Exception as e:
        logger.error(f"Inventory cleaning FAILED: {e}")
        return False


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    success = run_cleaning()
    sys.exit(0 if success else 1)
