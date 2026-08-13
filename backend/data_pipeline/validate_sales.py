"""
==============================================================================
Script 3: validate_sales.py
==============================================================================
Purpose:
    Validates the raw sales transactions dataset
    (sales_transactions_50000_textile_dataset.xlsx) to ensure data quality.

Why this script is needed:
    Sales transactions are the LARGEST and MOST CRITICAL dataset in this
    project (50,000 rows). Every AI module depends heavily on this data:

    - Product Recommendation: Learns "customers who bought X also bought Y"
      patterns FROM sales data. Bad sales data = bad recommendations.
    - Demand Forecasting: Predicts future demand from HISTORICAL sales.
      One corrupted month of data can skew predictions for the whole year.
    - Inventory Management: Calculates how fast products sell (velocity)
      to decide when to reorder. Wrong quantities = wrong reorder points.

    This script also performs REFERENTIAL INTEGRITY checks — it verifies
    that every CustomerID and ProductID in sales actually exists in the
    customers and products datasets. This is the same concept as foreign
    keys in databases.

Which AI modules use this:
    ALL THREE modules — this is the backbone dataset of the entire system.

Output:
    - Console log summary (via Python logging)
    - Detailed report saved to: reports/validation_report_sales.txt
==============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List

import pandas as pd


# =============================================================================
# CONSTANTS
# =============================================================================
# Path to the raw sales Excel file
RAW_FILE_PATH: str = os.path.join(
    "data", "raw", "sales_transactions_50000_textile_dataset.xlsx"
)

# Paths to related datasets for referential integrity checks.
# Sales records reference customers (who bought) and products (what was bought).
PRODUCTS_FILE: str = os.path.join("data", "raw", "products_500_textile_dataset.xlsx")
CUSTOMERS_FILE: str = os.path.join("data", "raw", "customers_2000_textile_dataset.xlsx")

# Report output path
REPORT_DIR: str = "reports"
REPORT_FILE: str = os.path.join(REPORT_DIR, "validation_report_sales.txt")

# Expected columns in the sales dataset
REQUIRED_COLUMNS: List[str] = [
    "SaleID", "InvoiceID", "CustomerID", "ProductID", "SubCategory",
    "SaleDate", "Quantity", "MRP", "DiscountPercent", "FinalPrice",
    "Festival", "Season", "DayOfWeek"
]

# Valid categorical values from the business domain
VALID_FESTIVALS: List[str] = [
    "Regular", "Pongal", "Diwali", "Navratri", "Summer",
    "Aadi Sale", "Independence Day", "Wedding Season", "School Season"
]
VALID_SEASONS: List[str] = ["Summer", "Winter", "Monsoon"]
VALID_DAYS: List[str] = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]

# Business rule thresholds
MAX_DISCOUNT_PERCENT: int = 100
MIN_QUANTITY: int = 1


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# =============================================================================
# FUNCTION 1: load_data()
# =============================================================================
def load_data(file_path: str) -> pd.DataFrame:
    """
    Load an Excel file into a pandas DataFrame.

    For sales data (50,000 rows), this may take a few seconds longer
    than the other datasets. The openpyxl engine processes each row
    from the XML-based .xlsx format.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Raw data file not found: {file_path}")

    try:
        df = pd.read_excel(file_path, engine="openpyxl")
        logger.info(
            f"Successfully loaded '{file_path}' → "
            f"{df.shape[0]:,} rows × {df.shape[1]} columns"
        )
        return df
    except Exception as e:
        logger.error(f"Failed to read '{file_path}': {e}")
        raise


# =============================================================================
# FUNCTION 2: validate_schema()
# =============================================================================
def validate_schema(df: pd.DataFrame, required_columns: List[str]) -> Dict[str, object]:
    """
    Check if the DataFrame contains all 13 required sales columns.
    """
    actual = set(df.columns)
    expected = set(required_columns)
    missing = list(expected - actual)
    extra = list(actual - expected)
    passed = len(missing) == 0

    if passed:
        logger.info("✅ Schema validation PASSED — all 13 required columns present")
    else:
        logger.warning(f"❌ Schema validation FAILED — missing: {missing}")

    if extra:
        logger.info(f"ℹ️  Extra columns found: {extra}")

    return {"passed": passed, "missing": missing, "extra": extra}


# =============================================================================
# FUNCTION 3: validate_missing_values()
# =============================================================================
def validate_missing_values(df: pd.DataFrame) -> Dict[str, object]:
    """
    Check for null/missing values across all sales columns.

    Why this is especially critical for sales data
    -----------------------------------------------
    - Missing Quantity → revenue calculations are wrong
    - Missing FinalPrice → total sales figures are inaccurate
    - Missing CustomerID → can't link the sale to a customer (orphan record)
    - Missing SaleDate → time-series forecasting has gaps
    """
    null_counts = df.isnull().sum()
    columns_with_nulls = null_counts[null_counts > 0]
    total_nulls = int(null_counts.sum())
    passed = total_nulls == 0

    if passed:
        logger.info(f"✅ Missing values check PASSED — no nulls in {df.shape[0]:,} records")
    else:
        logger.warning(f"❌ Missing values check FAILED — {total_nulls:,} null(s) found")
        for col, count in columns_with_nulls.items():
            logger.warning(f"   Column '{col}': {count:,} null(s)")

    return {
        "passed": passed,
        "total_nulls": total_nulls,
        "null_counts": columns_with_nulls.to_dict()
    }


# =============================================================================
# FUNCTION 4: validate_duplicates()
# =============================================================================
def validate_duplicates(df: pd.DataFrame) -> Dict[str, object]:
    """
    Check for duplicate sales records.

    Why duplicates are especially dangerous in sales data
    -----------------------------------------------------
    Every duplicate sale:
    - Inflates revenue by the FinalPrice of that transaction
    - Skews demand forecasting (model thinks a product sells more than it does)
    - Causes wrong reorder quantities in inventory management
    - Makes recommendation patterns unreliable

    We check:
    1. Duplicate SaleID (primary key — MUST be unique)
    2. Fully identical rows (exact copy-paste errors)
    """
    dup_sale_ids = int(df["SaleID"].duplicated().sum())
    full_dups = int(df.duplicated().sum())

    passed = (dup_sale_ids == 0) and (full_dups == 0)

    if passed:
        logger.info("✅ Duplicate check PASSED — all SaleIDs are unique")
    else:
        logger.warning(f"❌ Duplicate check FAILED")
        if dup_sale_ids > 0:
            logger.warning(f"   Duplicate SaleIDs: {dup_sale_ids:,}")
        if full_dups > 0:
            logger.warning(f"   Fully duplicated rows: {full_dups:,}")

    return {
        "passed": passed,
        "duplicate_sale_ids": dup_sale_ids,
        "full_duplicates": full_dups
    }


# =============================================================================
# FUNCTION 5: validate_data_types()
# =============================================================================
def validate_data_types(df: pd.DataFrame) -> Dict[str, object]:
    """
    Validate that sales columns have the expected data types.

    Expected:
    - Quantity, MRP, DiscountPercent → numeric (int)
    - FinalPrice → numeric (float)
    - SaleDate → parseable as date
    - SaleID, InvoiceID, CustomerID, ProductID → text
    """
    issues: List[str] = []

    # --- Numeric columns ---
    numeric_cols = ["Quantity", "MRP", "DiscountPercent", "FinalPrice"]
    for col in numeric_cols:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            issues.append(f"Column '{col}' should be numeric but is {df[col].dtype}")

    # --- Date column ---
    if "SaleDate" in df.columns:
        try:
            parsed = pd.to_datetime(df["SaleDate"], errors="coerce")
            unparseable = int(parsed.isna().sum())
            if unparseable > 0:
                issues.append(
                    f"Column 'SaleDate' has {unparseable:,} unparseable date(s)"
                )
        except Exception as e:
            issues.append(f"Column 'SaleDate' parsing error: {e}")

    # --- String/ID columns ---
    string_cols = ["SaleID", "InvoiceID", "CustomerID", "ProductID",
                   "SubCategory", "Festival", "Season", "DayOfWeek"]
    for col in string_cols:
        if col in df.columns and df[col].dtype not in ["object", "string", "str"]:
            issues.append(f"Column '{col}' should be text but is {df[col].dtype}")

    passed = len(issues) == 0

    if passed:
        logger.info("✅ Data type validation PASSED")
    else:
        logger.warning(f"❌ Data type validation FAILED — {len(issues)} issue(s)")
        for issue in issues:
            logger.warning(f"   {issue}")

    return {"passed": passed, "issues": issues}


# =============================================================================
# FUNCTION 6: validate_business_rules()
# =============================================================================
def validate_business_rules(df: pd.DataFrame) -> Dict[str, object]:
    """
    Validate domain-specific business rules for sales transactions.

    These rules ensure the sales data makes sense from a retail perspective.
    """
    violations: Dict[str, int] = {}
    details: Dict[str, object] = {}

    # -------------------------------------------------------------------------
    # Rule 1: Quantity must be positive (≥ 1)
    # -------------------------------------------------------------------------
    # You can't sell 0 or negative items. Minimum 1 item per line.
    invalid_qty = df[df["Quantity"] < MIN_QUANTITY]
    if len(invalid_qty) > 0:
        violations["Quantity < 1"] = len(invalid_qty)
        details["Quantity < 1"] = invalid_qty["SaleID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Rule 2: MRP (Maximum Retail Price) must be positive
    # -------------------------------------------------------------------------
    invalid_mrp = df[df["MRP"] <= 0]
    if len(invalid_mrp) > 0:
        violations["MRP <= 0"] = len(invalid_mrp)
        details["MRP <= 0"] = invalid_mrp["SaleID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Rule 3: DiscountPercent must be between 0 and 100
    # -------------------------------------------------------------------------
    # A discount can't be negative (that would mean surcharge).
    # A discount can't exceed 100% (you can't pay less than ₹0).
    invalid_discount = df[
        (df["DiscountPercent"] < 0) | (df["DiscountPercent"] > MAX_DISCOUNT_PERCENT)
    ]
    if len(invalid_discount) > 0:
        violations["DiscountPercent out of range (0-100)"] = len(invalid_discount)
        details["DiscountPercent out of range"] = (
            invalid_discount["DiscountPercent"].unique().tolist()[:5]
        )

    # -------------------------------------------------------------------------
    # Rule 4: FinalPrice must be positive
    # -------------------------------------------------------------------------
    invalid_final = df[df["FinalPrice"] <= 0]
    if len(invalid_final) > 0:
        violations["FinalPrice <= 0"] = len(invalid_final)
        details["FinalPrice <= 0"] = invalid_final["SaleID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Rule 5: FinalPrice consistency check
    # -------------------------------------------------------------------------
    # FinalPrice should approximately equal: Quantity * MRP * (1 - Discount/100)
    # We allow a small tolerance (₹1) for floating-point rounding.
    expected_price = df["Quantity"] * df["MRP"] * (1 - df["DiscountPercent"] / 100)
    price_diff = (df["FinalPrice"] - expected_price).abs()
    inconsistent_price = df[price_diff > 1.0]
    if len(inconsistent_price) > 0:
        violations["FinalPrice inconsistent with Qty*MRP*(1-Disc%)"] = len(inconsistent_price)
        details["FinalPrice inconsistency"] = {
            "sample_ids": inconsistent_price["SaleID"].tolist()[:5],
            "max_difference": float(price_diff.max())
        }

    # -------------------------------------------------------------------------
    # Rule 6: Festival must be a valid value
    # -------------------------------------------------------------------------
    invalid_festival = df[~df["Festival"].isin(VALID_FESTIVALS)]
    if len(invalid_festival) > 0:
        violations["Invalid Festival value"] = len(invalid_festival)
        details["Invalid Festival"] = invalid_festival["Festival"].unique().tolist()

    # -------------------------------------------------------------------------
    # Rule 7: Season must be a valid value
    # -------------------------------------------------------------------------
    invalid_season = df[~df["Season"].isin(VALID_SEASONS)]
    if len(invalid_season) > 0:
        violations["Invalid Season value"] = len(invalid_season)
        details["Invalid Season"] = invalid_season["Season"].unique().tolist()

    # -------------------------------------------------------------------------
    # Rule 8: DayOfWeek must be a valid day name
    # -------------------------------------------------------------------------
    invalid_day = df[~df["DayOfWeek"].isin(VALID_DAYS)]
    if len(invalid_day) > 0:
        violations["Invalid DayOfWeek value"] = len(invalid_day)
        details["Invalid DayOfWeek"] = invalid_day["DayOfWeek"].unique().tolist()

    # -------------------------------------------------------------------------
    # Rule 9: SaleID format should be S followed by 6 digits (S000001)
    # -------------------------------------------------------------------------
    invalid_id = df[~df["SaleID"].str.match(r"^S\d{6}$")]
    if len(invalid_id) > 0:
        violations["Invalid SaleID format"] = len(invalid_id)
        details["Invalid SaleID format"] = invalid_id["SaleID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Summarize
    # -------------------------------------------------------------------------
    passed = len(violations) == 0

    if passed:
        logger.info("✅ Business rules validation PASSED — all 9 rules satisfied")
    else:
        logger.warning(f"❌ Business rules validation FAILED — {len(violations)} rule(s) violated")
        for rule, count in violations.items():
            logger.warning(f"   {rule}: {count:,} violation(s)")

    return {"passed": passed, "violations": violations, "details": details}


# =============================================================================
# FUNCTION 7: validate_referential_integrity()
# =============================================================================
def validate_referential_integrity(df: pd.DataFrame) -> Dict[str, object]:
    """
    Validate that foreign keys in sales data reference valid records.

    What is referential integrity?
    ------------------------------
    In databases, a "foreign key" is a column that points to a record in
    another table. For example, CustomerID in sales points to a specific
    customer in the customers table.

    If a sales record says CustomerID = "C99999" but that customer doesn't
    exist in the customers dataset, we have an "orphan record" — a sale
    with no customer. This would break joins and cause NaN values in the
    master dataset.

    We check two foreign keys:
    1. CustomerID → must exist in customers dataset
    2. ProductID  → must exist in products dataset
    """
    issues: Dict[str, object] = {}

    # -------------------------------------------------------------------------
    # Check 1: All CustomerIDs in sales exist in the customers file
    # -------------------------------------------------------------------------
    try:
        customers_df = pd.read_excel(CUSTOMERS_FILE, engine="openpyxl")
        valid_customer_ids = set(customers_df["CustomerID"].unique())
        sales_customer_ids = set(df["CustomerID"].unique())

        # Find CustomerIDs that appear in sales but NOT in customers
        orphan_customers = sales_customer_ids - valid_customer_ids

        if len(orphan_customers) > 0:
            issues["Orphan CustomerIDs (not in customers file)"] = {
                "count": len(orphan_customers),
                "samples": list(orphan_customers)[:10]
            }
            logger.warning(
                f"❌ {len(orphan_customers)} CustomerID(s) in sales "
                f"not found in customers dataset"
            )
        else:
            logger.info(
                f"✅ CustomerID integrity PASSED — all {len(sales_customer_ids):,} "
                f"customers found in customers dataset"
            )
    except Exception as e:
        issues["CustomerID check error"] = str(e)
        logger.error(f"Could not verify CustomerIDs: {e}")

    # -------------------------------------------------------------------------
    # Check 2: All ProductIDs in sales exist in the products file
    # -------------------------------------------------------------------------
    try:
        products_df = pd.read_excel(PRODUCTS_FILE, engine="openpyxl")
        valid_product_ids = set(products_df["ProductID"].unique())
        sales_product_ids = set(df["ProductID"].unique())

        # Find ProductIDs that appear in sales but NOT in products
        orphan_products = sales_product_ids - valid_product_ids

        if len(orphan_products) > 0:
            issues["Orphan ProductIDs (not in products file)"] = {
                "count": len(orphan_products),
                "samples": list(orphan_products)[:10]
            }
            logger.warning(
                f"❌ {len(orphan_products)} ProductID(s) in sales "
                f"not found in products dataset"
            )
        else:
            logger.info(
                f"✅ ProductID integrity PASSED — all {len(sales_product_ids)} "
                f"products found in products dataset"
            )
    except Exception as e:
        issues["ProductID check error"] = str(e)
        logger.error(f"Could not verify ProductIDs: {e}")

    passed = len(issues) == 0

    if passed:
        logger.info("✅ Referential integrity PASSED — all foreign keys valid")

    return {"passed": passed, "issues": issues}


# =============================================================================
# FUNCTION 8: generate_report()
# =============================================================================
def generate_report(
    df: pd.DataFrame,
    schema_result: Dict,
    missing_result: Dict,
    duplicate_result: Dict,
    dtype_result: Dict,
    business_result: Dict,
    integrity_result: Dict,
    report_path: str
) -> None:
    """
    Generate a detailed validation report for the sales dataset.

    This report has an EXTRA section compared to products/customers:
    Section 6 — Referential Integrity. This is because sales data
    has foreign keys pointing to other datasets.
    """
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    lines: List[str] = []

    # --- Header ---
    lines.append("=" * 70)
    lines.append("VALIDATION REPORT — SALES TRANSACTIONS DATASET")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Source File: {RAW_FILE_PATH}")
    lines.append("=" * 70)
    lines.append("")

    # --- Dataset Summary ---
    lines.append("📊 DATASET SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  Total Rows       : {df.shape[0]:,}")
    lines.append(f"  Total Columns    : {df.shape[1]}")
    lines.append(f"  Unique Customers : {df['CustomerID'].nunique():,}")
    lines.append(f"  Unique Products  : {df['ProductID'].nunique()}")
    lines.append(f"  Unique Invoices  : {df['InvoiceID'].nunique():,}")
    lines.append(f"  Quantity Range   : {df['Quantity'].min()} — {df['Quantity'].max()}")
    lines.append(f"  FinalPrice Range : ₹{df['FinalPrice'].min():,.2f} — ₹{df['FinalPrice'].max():,.2f}")
    lines.append(f"  Total Revenue    : ₹{df['FinalPrice'].sum():,.2f}")
    lines.append("")

    # --- 1. Schema ---
    lines.append("1️⃣  SCHEMA VALIDATION")
    lines.append("-" * 40)
    lines.append(f"  Status  : {'✅ PASSED' if schema_result['passed'] else '❌ FAILED'}")
    if schema_result["missing"]:
        lines.append(f"  Missing : {schema_result['missing']}")
    lines.append("")

    # --- 2. Missing Values ---
    lines.append("2️⃣  MISSING VALUES CHECK")
    lines.append("-" * 40)
    lines.append(f"  Status      : {'✅ PASSED' if missing_result['passed'] else '❌ FAILED'}")
    lines.append(f"  Total Nulls : {missing_result['total_nulls']:,}")
    if missing_result["null_counts"]:
        for col, count in missing_result["null_counts"].items():
            lines.append(f"  → {col}: {count:,} null(s)")
    lines.append("")

    # --- 3. Duplicates ---
    lines.append("3️⃣  DUPLICATE CHECK")
    lines.append("-" * 40)
    lines.append(f"  Status           : {'✅ PASSED' if duplicate_result['passed'] else '❌ FAILED'}")
    lines.append(f"  Duplicate SaleIDs: {duplicate_result['duplicate_sale_ids']:,}")
    lines.append(f"  Full Duplicates  : {duplicate_result['full_duplicates']:,}")
    lines.append("")

    # --- 4. Data Types ---
    lines.append("4️⃣  DATA TYPE VALIDATION")
    lines.append("-" * 40)
    lines.append(f"  Status : {'✅ PASSED' if dtype_result['passed'] else '❌ FAILED'}")
    if dtype_result["issues"]:
        for issue in dtype_result["issues"]:
            lines.append(f"  → {issue}")
    lines.append("")

    # --- 5. Business Rules ---
    lines.append("5️⃣  BUSINESS RULES VALIDATION")
    lines.append("-" * 40)
    lines.append(f"  Status : {'✅ PASSED' if business_result['passed'] else '❌ FAILED'}")
    if business_result["violations"]:
        for rule, count in business_result["violations"].items():
            lines.append(f"  → {rule}: {count:,} violation(s)")
    lines.append("")

    # --- 6. Referential Integrity (NEW section for sales) ---
    lines.append("6️⃣  REFERENTIAL INTEGRITY")
    lines.append("-" * 40)
    lines.append(f"  Status : {'✅ PASSED' if integrity_result['passed'] else '❌ FAILED'}")
    if integrity_result["issues"]:
        for issue_name, issue_detail in integrity_result["issues"].items():
            lines.append(f"  → {issue_name}: {issue_detail}")
    lines.append("")

    # --- Overall ---
    all_passed = all([
        schema_result["passed"], missing_result["passed"],
        duplicate_result["passed"], dtype_result["passed"],
        business_result["passed"], integrity_result["passed"]
    ])
    lines.append("=" * 70)
    lines.append(f"OVERALL RESULT: {'✅ ALL CHECKS PASSED' if all_passed else '⚠️  SOME CHECKS FAILED'}")
    lines.append("=" * 70)

    report_text = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    logger.info(f"📄 Validation report saved to: {report_path}")


# =============================================================================
# FUNCTION 9: run_validation() — The Orchestrator
# =============================================================================
def run_validation() -> bool:
    """
    Run the complete validation pipeline for the sales dataset.

    This orchestrator has 6 validation steps (one more than products/customers)
    because sales data requires referential integrity checks.
    """
    logger.info("=" * 60)
    logger.info("STARTING VALIDATION: Sales Transactions Dataset")
    logger.info("=" * 60)

    # Step 1: Load raw data
    try:
        df = load_data(RAW_FILE_PATH)
    except (FileNotFoundError, Exception) as e:
        logger.error(f"Cannot proceed with validation: {e}")
        return False

    # Step 2: Run all validation checks
    schema_result = validate_schema(df, REQUIRED_COLUMNS)
    missing_result = validate_missing_values(df)
    duplicate_result = validate_duplicates(df)
    dtype_result = validate_data_types(df)
    business_result = validate_business_rules(df)
    integrity_result = validate_referential_integrity(df)

    # Step 3: Generate report
    generate_report(
        df=df,
        schema_result=schema_result,
        missing_result=missing_result,
        duplicate_result=duplicate_result,
        dtype_result=dtype_result,
        business_result=business_result,
        integrity_result=integrity_result,
        report_path=REPORT_FILE
    )

    # Step 4: Return overall result
    all_passed = all([
        schema_result["passed"], missing_result["passed"],
        duplicate_result["passed"], dtype_result["passed"],
        business_result["passed"], integrity_result["passed"]
    ])

    if all_passed:
        logger.info("🎉 Sales validation COMPLETED — ALL CHECKS PASSED")
    else:
        logger.warning("⚠️  Sales validation COMPLETED — SOME CHECKS FAILED")
        logger.warning("   Review the report: " + REPORT_FILE)

    return all_passed


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
