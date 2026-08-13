"""
==============================================================================
Script: clean_products.py
==============================================================================
Purpose:
    Cleans and standardises the raw products dataset
    (products_500_textile_dataset.xlsx) after validation.

Cleaning Operations:
    1. Strip leading/trailing whitespace from all text columns
    2. Normalise categorical columns (title case, map known variants)
    3. Ensure numeric columns (Price, CostPrice) are float64
    4. Drop fully duplicated rows (if any)
    5. Drop rows with null ProductID (primary key)
    6. Fill remaining nulls with sensible defaults
    7. Add a ProfitMargin derived column for downstream analytics

Output:
    data/processed/products_clean.csv
==============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import os
import sys
import logging
from pathlib import Path
from typing import List

import pandas as pd

# =============================================================================
# CONSTANTS
# =============================================================================
RAW_FILE_PATH: str = os.path.join("data", "raw", "products_500_textile_dataset.xlsx")
OUTPUT_DIR: str = os.path.join("data", "processed")
OUTPUT_FILE: str = os.path.join(OUTPUT_DIR, "products_clean.csv")

TEXT_COLUMNS: List[str] = [
    "ProductID", "SKU", "ProductName", "Category", "SubCategory",
    "Brand", "Color", "Size", "Fabric", "SeasonalDemandTag",
    "Gender", "ProductStatus", "ImageURL"
]

VALID_CATEGORIES = ["Men", "Women", "Kids", "Accessories", "Home & Lifestyle"]
VALID_GENDERS = ["Men", "Women", "Unisex", "Kids"]
VALID_FABRICS = ["Cotton", "Silk", "Handloom", "Polyester", "Polyester Blend", "Linen", "Leather"]
VALID_STATUSES = ["Active", "Inactive", "Discontinued"]

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
    """Strip leading/trailing whitespace from all text columns."""
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    logger.info("Stripped whitespace from text columns")
    return df


def normalise_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise categorical columns to their canonical values.

    Uses str.title() first, then maps any known variants to the
    correct canonical value.  Unknown values are left as-is so
    downstream analysis can flag them.
    """
    # --- Category ---
    if "Category" in df.columns:
        df["Category"] = df["Category"].str.strip().str.title()
        cat_map = {"Home & Lifestyle": "Home & Lifestyle", "Home And Lifestyle": "Home & Lifestyle"}
        df["Category"] = df["Category"].replace(cat_map)

    # --- Gender ---
    if "Gender" in df.columns:
        df["Gender"] = df["Gender"].str.strip().str.title()

    # --- Fabric ---
    if "Fabric" in df.columns:
        df["Fabric"] = df["Fabric"].str.strip().str.title()
        fabric_map = {"Polyester Blend": "Polyester Blend"}
        df["Fabric"] = df["Fabric"].replace(fabric_map)

    # --- ProductStatus ---
    if "ProductStatus" in df.columns:
        df["ProductStatus"] = df["ProductStatus"].str.strip().str.title()

    logger.info("Normalised categorical columns")
    return df


def fix_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure numeric columns are float64."""
    for col in ["Price", "CostPrice"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    logger.info("Fixed numeric data types (Price, CostPrice → float64)")
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
    """
    Handle null values:
    - Drop rows where ProductID is null (can't identify the product)
    - Fill text nulls with 'Unknown'
    - Fill numeric nulls with 0.0
    """
    before = len(df)
    df = df.dropna(subset=["ProductID"])
    dropped = before - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} row(s) with null ProductID")

    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    for col in ["Price", "CostPrice"]:
        if col in df.columns:
            df[col] = df[col].fillna(0.0)

    total_nulls = int(df.isnull().sum().sum())
    logger.info(f"Null handling complete — {total_nulls} null(s) remaining")
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add ProfitMargin = (Price - CostPrice) / Price * 100."""
    if "Price" in df.columns and "CostPrice" in df.columns:
        df["ProfitMargin"] = ((df["Price"] - df["CostPrice"]) / df["Price"] * 100).round(2)
        # Clamp negative margins to 0 (data issue — don't propagate)
        df["ProfitMargin"] = df["ProfitMargin"].clip(lower=0)
        logger.info("Added ProfitMargin column")
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
    """
    Run the complete cleaning pipeline for products.

    Returns True if cleaning completed successfully, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("STARTING CLEANING: Products Dataset")
    logger.info("=" * 60)

    try:
        df = load_raw_data(RAW_FILE_PATH)
        df = strip_whitespace(df)
        df = normalise_categoricals(df)
        df = fix_data_types(df)
        df = handle_duplicates(df)
        df = handle_nulls(df)
        df = add_derived_columns(df)
        save_clean_data(df, OUTPUT_FILE)

        logger.info("🎉 Products cleaning COMPLETED successfully")
        return True

    except Exception as e:
        logger.error(f"Products cleaning FAILED: {e}")
        return False


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    success = run_cleaning()
    sys.exit(0 if success else 1)
