"""
==============================================================================
Script: clean_customers.py
==============================================================================
Purpose:
    Cleans and standardises the raw customers dataset
    (customers_2000_textile_dataset.xlsx) after validation.

Cleaning Operations:
    1. Strip whitespace from all text columns
    2. Normalise Gender, Membership, PreferredCategory, PreferredFabric,
       PreferredPriceRange to canonical values
    3. Parse JoinDate to datetime and reformat as YYYY-MM-DD string
    4. Clamp Age to valid range (18-100)
    5. Ensure LoyaltyPoints is non-negative
    6. Drop rows with null CustomerID
    7. Drop fully duplicated rows
    8. Add CustomerTenureDays derived column

Output:
    data/processed/customers_clean.csv
==============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import os
import sys
import logging
from datetime import datetime
from typing import List

import pandas as pd

# =============================================================================
# CONSTANTS
# =============================================================================
RAW_FILE_PATH: str = os.path.join("data", "raw", "customers_2000_textile_dataset.xlsx")
OUTPUT_DIR: str = os.path.join("data", "processed")
OUTPUT_FILE: str = os.path.join(OUTPUT_DIR, "customers_clean.csv")

TEXT_COLUMNS: List[str] = [
    "CustomerID", "FullName", "Gender", "City", "State",
    "Membership", "PreferredCategory", "PreferredFabric", "PreferredPriceRange"
]

VALID_GENDERS = ["Male", "Female"]
VALID_MEMBERSHIPS = ["Bronze", "Silver", "Gold", "Platinum"]
VALID_CATEGORIES = ["Men", "Women", "Kids", "Accessories", "Home & Lifestyle"]
VALID_FABRICS = ["Cotton", "Silk", "Handloom", "Polyester", "Linen"]
VALID_PRICE_RANGES = ["Budget", "Standard", "Premium", "Luxury"]

MIN_AGE = 18
MAX_AGE = 100

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
    """Normalise categorical columns to canonical values."""
    if "Gender" in df.columns:
        df["Gender"] = df["Gender"].str.strip().str.title()

    if "Membership" in df.columns:
        df["Membership"] = df["Membership"].str.strip().str.title()

    if "PreferredCategory" in df.columns:
        df["PreferredCategory"] = df["PreferredCategory"].str.strip().str.title()
        df["PreferredCategory"] = df["PreferredCategory"].replace({
            "Home And Lifestyle": "Home & Lifestyle",
            "Home & Lifestyle": "Home & Lifestyle"
        })

    if "PreferredFabric" in df.columns:
        df["PreferredFabric"] = df["PreferredFabric"].str.strip().str.title()

    if "PreferredPriceRange" in df.columns:
        df["PreferredPriceRange"] = df["PreferredPriceRange"].str.strip().str.title()

    logger.info("Normalised categorical columns")
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse JoinDate to datetime, then format as YYYY-MM-DD string for CSV."""
    if "JoinDate" in df.columns:
        df["JoinDate"] = pd.to_datetime(df["JoinDate"], errors="coerce")
        unparseable = int(df["JoinDate"].isna().sum())
        if unparseable > 0:
            logger.warning(f"{unparseable} unparseable JoinDate value(s) set to NaT")
        # Format back to string for CSV output
        df["JoinDate"] = df["JoinDate"].dt.strftime("%Y-%m-%d")
        logger.info("Parsed and formatted JoinDate → YYYY-MM-DD")
    return df


def clamp_age(df: pd.DataFrame) -> pd.DataFrame:
    """Clamp Age to the valid range [18, 100]."""
    if "Age" in df.columns:
        df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
        before_min = int((df["Age"] < MIN_AGE).sum())
        before_max = int((df["Age"] > MAX_AGE).sum())
        df["Age"] = df["Age"].clip(lower=MIN_AGE, upper=MAX_AGE)
        if before_min > 0 or before_max > 0:
            logger.warning(f"Clamped {before_min + before_max} age value(s) to [{MIN_AGE}, {MAX_AGE}]")
        else:
            logger.info("All ages within valid range")
    return df


def fix_loyalty_points(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure LoyaltyPoints is non-negative."""
    if "LoyaltyPoints" in df.columns:
        df["LoyaltyPoints"] = pd.to_numeric(df["LoyaltyPoints"], errors="coerce")
        negatives = int((df["LoyaltyPoints"] < 0).sum())
        df["LoyaltyPoints"] = df["LoyaltyPoints"].clip(lower=0)
        if negatives > 0:
            logger.warning(f"Clamped {negatives} negative LoyaltyPoints to 0")
        else:
            logger.info("All LoyaltyPoints are non-negative")
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
    """Handle null values — drop rows with null CustomerID, fill others."""
    before = len(df)
    df = df.dropna(subset=["CustomerID"])
    dropped = before - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} row(s) with null CustomerID")

    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    for col in ["Age", "LoyaltyPoints"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    total_nulls = int(df.isnull().sum().sum())
    logger.info(f"Null handling complete — {total_nulls} null(s) remaining")
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add CustomerTenureDays = days since JoinDate."""
    if "JoinDate" in df.columns:
        try:
            join_dates = pd.to_datetime(df["JoinDate"], errors="coerce")
            today = pd.Timestamp.now()
            df["CustomerTenureDays"] = (today - join_dates).dt.days
            df["CustomerTenureDays"] = df["CustomerTenureDays"].fillna(0).astype(int)
            logger.info("Added CustomerTenureDays column")
        except Exception as e:
            logger.warning(f"Could not compute CustomerTenureDays: {e}")
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
    """Run the complete cleaning pipeline for customers."""
    logger.info("=" * 60)
    logger.info("STARTING CLEANING: Customers Dataset")
    logger.info("=" * 60)

    try:
        df = load_raw_data(RAW_FILE_PATH)
        df = strip_whitespace(df)
        df = normalise_categoricals(df)
        df = parse_dates(df)
        df = clamp_age(df)
        df = fix_loyalty_points(df)
        df = handle_duplicates(df)
        df = handle_nulls(df)
        df = add_derived_columns(df)
        save_clean_data(df, OUTPUT_FILE)

        logger.info("🎉 Customers cleaning COMPLETED successfully")
        return True

    except Exception as e:
        logger.error(f"Customers cleaning FAILED: {e}")
        return False


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    success = run_cleaning()
    sys.exit(0 if success else 1)
