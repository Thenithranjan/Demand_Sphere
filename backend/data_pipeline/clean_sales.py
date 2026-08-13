"""
==============================================================================
Script: clean_sales.py
==============================================================================
Purpose:
    Cleans and standardises the raw sales transactions dataset
    (sales_transactions_50000_textile_dataset.xlsx) after validation.

Cleaning Operations:
    1. Strip whitespace from all text columns
    2. Normalise Festival, Season, DayOfWeek to canonical values
    3. Parse SaleDate to datetime and format as YYYY-MM-DD
    4. Ensure Quantity, MRP, DiscountPercent, FinalPrice are numeric
    5. Clamp DiscountPercent to [0, 100]
    6. Recalculate FinalPrice if inconsistent with Qty * MRP * (1 - Disc/100)
    7. Drop fully duplicated rows
    8. Drop rows with null SaleID
    9. Add TotalRevenue and Month/Year derived columns

Output:
    data/processed/sales_clean.csv
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
RAW_FILE_PATH: str = os.path.join(
    "data", "raw", "sales_transactions_50000_textile_dataset.xlsx"
)
OUTPUT_DIR: str = os.path.join("data", "processed")
OUTPUT_FILE: str = os.path.join(OUTPUT_DIR, "sales_clean.csv")

TEXT_COLUMNS: List[str] = [
    "SaleID", "InvoiceID", "CustomerID", "ProductID",
    "SubCategory", "Festival", "Season", "DayOfWeek"
]

VALID_FESTIVALS = [
    "Regular", "Pongal", "Diwali", "Navratri", "Summer",
    "Aadi Sale", "Independence Day", "Wedding Season", "School Season"
]
VALID_SEASONS = ["Summer", "Winter", "Monsoon"]
VALID_DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]

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
    logger.info(f"Loaded '{file_path}' → {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


def strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from all text columns."""
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    logger.info("Stripped whitespace from text columns")
    return df


def normalise_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise categorical text columns."""
    if "Festival" in df.columns:
        df["Festival"] = df["Festival"].str.strip().str.title()
        # Fix known title-case anomalies
        festival_map = {
            "Aadi Sale": "Aadi Sale",
            "Independence Day": "Independence Day",
            "Wedding Season": "Wedding Season",
            "School Season": "School Season",
        }
        df["Festival"] = df["Festival"].replace(festival_map)

    if "Season" in df.columns:
        df["Season"] = df["Season"].str.strip().str.title()

    if "DayOfWeek" in df.columns:
        df["DayOfWeek"] = df["DayOfWeek"].str.strip().str.title()

    if "SubCategory" in df.columns:
        df["SubCategory"] = df["SubCategory"].str.strip().str.title()

    logger.info("Normalised categorical columns")
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse SaleDate to datetime and format as YYYY-MM-DD."""
    if "SaleDate" in df.columns:
        df["SaleDate"] = pd.to_datetime(df["SaleDate"], errors="coerce")
        unparseable = int(df["SaleDate"].isna().sum())
        if unparseable > 0:
            logger.warning(f"{unparseable:,} unparseable SaleDate value(s) set to NaT")
        df["SaleDate"] = df["SaleDate"].dt.strftime("%Y-%m-%d")
        logger.info("Parsed and formatted SaleDate → YYYY-MM-DD")
    return df


def fix_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all numeric columns are properly typed."""
    for col in ["Quantity", "MRP", "DiscountPercent", "FinalPrice"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Clamp Quantity to minimum of 1
    if "Quantity" in df.columns:
        clamped_qty = int((df["Quantity"] < 1).sum())
        df["Quantity"] = df["Quantity"].clip(lower=1)
        if clamped_qty > 0:
            logger.warning(f"Clamped {clamped_qty:,} Quantity value(s) to minimum 1")

    # Clamp DiscountPercent to [0, 100]
    if "DiscountPercent" in df.columns:
        clamped_disc = int(
            ((df["DiscountPercent"] < 0) | (df["DiscountPercent"] > 100)).sum()
        )
        df["DiscountPercent"] = df["DiscountPercent"].clip(lower=0, upper=100)
        if clamped_disc > 0:
            logger.warning(f"Clamped {clamped_disc:,} DiscountPercent value(s) to [0, 100]")

    logger.info("Fixed numeric data types and ranges")
    return df


def recalculate_final_price(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recalculate FinalPrice = Quantity * MRP * (1 - DiscountPercent/100).

    If the stored FinalPrice differs from the computed value by more than ₹1,
    we overwrite it with the correct calculation.
    """
    if all(col in df.columns for col in ["Quantity", "MRP", "DiscountPercent", "FinalPrice"]):
        expected = df["Quantity"] * df["MRP"] * (1 - df["DiscountPercent"] / 100)
        diff = (df["FinalPrice"] - expected).abs()
        inconsistent = int((diff > 1.0).sum())

        if inconsistent > 0:
            logger.warning(
                f"Recalculated {inconsistent:,} inconsistent FinalPrice value(s)"
            )
            df.loc[diff > 1.0, "FinalPrice"] = expected[diff > 1.0].round(2)
        else:
            logger.info("All FinalPrice values are consistent")

        df["FinalPrice"] = df["FinalPrice"].round(2)
    return df


def handle_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Drop fully duplicated rows."""
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    if removed > 0:
        logger.warning(f"Removed {removed:,} fully duplicated row(s)")
    else:
        logger.info("No duplicate rows found")
    return df


def handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Handle null values — drop rows with null SaleID, fill others."""
    before = len(df)
    df = df.dropna(subset=["SaleID"])
    dropped = before - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped:,} row(s) with null SaleID")

    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    for col in ["Quantity", "MRP", "DiscountPercent", "FinalPrice"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    total_nulls = int(df.isnull().sum().sum())
    logger.info(f"Null handling complete — {total_nulls} null(s) remaining")
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add SaleMonth and SaleYear for time-series analytics."""
    if "SaleDate" in df.columns:
        try:
            sale_dates = pd.to_datetime(df["SaleDate"], errors="coerce")
            df["SaleMonth"] = sale_dates.dt.month
            df["SaleYear"] = sale_dates.dt.year
            df["SaleMonth"] = df["SaleMonth"].fillna(0).astype(int)
            df["SaleYear"] = df["SaleYear"].fillna(0).astype(int)
            logger.info("Added SaleMonth and SaleYear columns")
        except Exception as e:
            logger.warning(f"Could not add date-derived columns: {e}")
    return df


def save_clean_data(df: pd.DataFrame, output_path: str) -> None:
    """Save the cleaned DataFrame to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"Saved cleaned data → '{output_path}' ({df.shape[0]:,} rows × {df.shape[1]} columns)")


# =============================================================================
# ORCHESTRATOR
# =============================================================================
def run_cleaning() -> bool:
    """Run the complete cleaning pipeline for sales transactions."""
    logger.info("=" * 60)
    logger.info("STARTING CLEANING: Sales Transactions Dataset")
    logger.info("=" * 60)

    try:
        df = load_raw_data(RAW_FILE_PATH)
        df = strip_whitespace(df)
        df = normalise_categoricals(df)
        df = parse_dates(df)
        df = fix_numeric_columns(df)
        df = recalculate_final_price(df)
        df = handle_duplicates(df)
        df = handle_nulls(df)
        df = add_derived_columns(df)
        save_clean_data(df, OUTPUT_FILE)

        logger.info("🎉 Sales cleaning COMPLETED successfully")
        return True

    except Exception as e:
        logger.error(f"Sales cleaning FAILED: {e}")
        return False


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    success = run_cleaning()
    sys.exit(0 if success else 1)
