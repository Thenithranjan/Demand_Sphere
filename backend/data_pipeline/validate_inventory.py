"""
==============================================================================
Script 4: validate_inventory.py
==============================================================================
Purpose:
    Validates the raw inventory dataset (inventory_500_textile_dataset.xlsx)
    to ensure data quality before cleaning and feature engineering.

Why this script is needed:
    Inventory data tracks HOW MUCH stock is available for each product
    across warehouses. Invalid inventory data causes real business damage:

    - Wrong CurrentStock → store thinks it has items it doesn't (overselling)
    - Wrong ReorderPoint → products run out before new stock arrives
    - MinStock > MaxStock → logically impossible, indicates data corruption
    - Missing SupplierID → can't reorder from the right supplier

    This is also the ONLY dataset that links to physical warehouses
    (Chennai WH, Madurai WH, Coimbatore WH), making it critical for
    the Inventory Management AI module.

Which AI modules use this:
    - Inventory Management (PRIMARY): Directly manages stock levels,
      reorder timing, and warehouse allocation.
    - Demand Forecasting: Uses current stock and restock dates to
      understand supply constraints that affect sales.
    - Product Recommendation: Uses stock availability to avoid
      recommending out-of-stock products.

Output:
    - Console log summary (via Python logging)
    - Detailed report saved to: reports/validation_report_inventory.txt
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
# Path to the raw inventory Excel file
RAW_FILE_PATH: str = os.path.join("data", "raw", "inventory_500_textile_dataset.xlsx")

# Path to products file for referential integrity check
PRODUCTS_FILE: str = os.path.join("data", "raw", "products_500_textile_dataset.xlsx")

# Report output path
REPORT_DIR: str = "reports"
REPORT_FILE: str = os.path.join(REPORT_DIR, "validation_report_inventory.txt")

# Expected columns — the "contract" for inventory data
REQUIRED_COLUMNS: List[str] = [
    "ProductID", "Warehouse", "CurrentStock", "MinimumStock",
    "MaximumStock", "SafetyStock", "ReorderPoint", "LeadTimeDays",
    "SupplierID", "LastRestocked", "InventoryStatus"
]

# Valid categorical values
VALID_WAREHOUSES: List[str] = ["Chennai WH", "Madurai WH", "Coimbatore WH"]
VALID_STATUSES: List[str] = ["Healthy", "Reorder Required", "Out of Stock", "Overstock"]


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
    """Load an Excel file into a pandas DataFrame."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Raw data file not found: {file_path}")

    try:
        df = pd.read_excel(file_path, engine="openpyxl")
        logger.info(f"Successfully loaded '{file_path}' → {df.shape[0]} rows × {df.shape[1]} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to read '{file_path}': {e}")
        raise


# =============================================================================
# FUNCTION 2: validate_schema()
# =============================================================================
def validate_schema(df: pd.DataFrame, required_columns: List[str]) -> Dict[str, object]:
    """Check if the DataFrame contains all 11 required inventory columns."""
    actual = set(df.columns)
    expected = set(required_columns)
    missing = list(expected - actual)
    extra = list(actual - expected)
    passed = len(missing) == 0

    if passed:
        logger.info("✅ Schema validation PASSED — all 11 required columns present")
    else:
        logger.warning(f"❌ Schema validation FAILED — missing: {missing}")

    return {"passed": passed, "missing": missing, "extra": extra}


# =============================================================================
# FUNCTION 3: validate_missing_values()
# =============================================================================
def validate_missing_values(df: pd.DataFrame) -> Dict[str, object]:
    """
    Check for null/missing values in inventory data.

    Every column in inventory is critical:
    - Missing CurrentStock → don't know what's on the shelves
    - Missing ReorderPoint → don't know when to reorder
    - Missing LeadTimeDays → don't know how long restocking takes
    """
    null_counts = df.isnull().sum()
    columns_with_nulls = null_counts[null_counts > 0]
    total_nulls = int(null_counts.sum())
    passed = total_nulls == 0

    if passed:
        logger.info("✅ Missing values check PASSED — no nulls in 500 inventory records")
    else:
        logger.warning(f"❌ Missing values check FAILED — {total_nulls} null(s)")
        for col, count in columns_with_nulls.items():
            logger.warning(f"   Column '{col}': {count} null(s)")

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
    Check for duplicate inventory records.

    Each ProductID should appear exactly ONCE in inventory.
    If P0001 appears twice, we don't know which stock count is correct.
    """
    dup_product_ids = int(df["ProductID"].duplicated().sum())
    full_dups = int(df.duplicated().sum())

    passed = (dup_product_ids == 0) and (full_dups == 0)

    if passed:
        logger.info("✅ Duplicate check PASSED — each product has one inventory record")
    else:
        logger.warning("❌ Duplicate check FAILED")
        if dup_product_ids > 0:
            logger.warning(f"   Duplicate ProductIDs: {dup_product_ids}")
        if full_dups > 0:
            logger.warning(f"   Fully duplicated rows: {full_dups}")

    return {
        "passed": passed,
        "duplicate_product_ids": dup_product_ids,
        "full_duplicates": full_dups
    }


# =============================================================================
# FUNCTION 5: validate_data_types()
# =============================================================================
def validate_data_types(df: pd.DataFrame) -> Dict[str, object]:
    """
    Validate data types for inventory columns.

    All stock-related columns must be numeric (integers):
    - CurrentStock, MinimumStock, MaximumStock, SafetyStock, ReorderPoint, LeadTimeDays
    """
    issues: List[str] = []

    # --- Numeric columns (all stock levels and lead time) ---
    numeric_cols = [
        "CurrentStock", "MinimumStock", "MaximumStock",
        "SafetyStock", "ReorderPoint", "LeadTimeDays"
    ]
    for col in numeric_cols:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            issues.append(f"Column '{col}' should be numeric but is {df[col].dtype}")

    # --- Date column ---
    if "LastRestocked" in df.columns:
        try:
            parsed = pd.to_datetime(df["LastRestocked"], errors="coerce")
            unparseable = int(parsed.isna().sum())
            if unparseable > 0:
                issues.append(f"'LastRestocked' has {unparseable} unparseable date(s)")
        except Exception as e:
            issues.append(f"'LastRestocked' parsing error: {e}")

    # --- String columns ---
    string_cols = ["ProductID", "Warehouse", "SupplierID", "InventoryStatus"]
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
    Validate inventory-specific business rules.

    Inventory rules are particularly LOGICAL — they involve relationships
    between multiple columns (e.g., MinimumStock MUST be less than MaximumStock).
    """
    violations: Dict[str, int] = {}
    details: Dict[str, object] = {}

    # -------------------------------------------------------------------------
    # Rule 1: All stock values must be non-negative (≥ 0)
    # -------------------------------------------------------------------------
    # You can have 0 items (out of stock), but not -5 items.
    stock_cols = ["CurrentStock", "MinimumStock", "MaximumStock",
                  "SafetyStock", "ReorderPoint"]
    for col in stock_cols:
        negative = df[df[col] < 0]
        if len(negative) > 0:
            violations[f"{col} < 0 (negative stock)"] = len(negative)
            details[f"Negative {col}"] = negative["ProductID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Rule 2: MinimumStock must be less than MaximumStock
    # -------------------------------------------------------------------------
    # If MinimumStock ≥ MaximumStock, the range is invalid.
    # Example: MinStock=200, MaxStock=100 is logically impossible.
    invalid_range = df[df["MinimumStock"] >= df["MaximumStock"]]
    if len(invalid_range) > 0:
        violations["MinimumStock >= MaximumStock"] = len(invalid_range)
        details["MinStock >= MaxStock"] = invalid_range["ProductID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Rule 3: SafetyStock should be ≤ MaximumStock
    # -------------------------------------------------------------------------
    # Safety stock is a BUFFER — it can't exceed the maximum capacity.
    invalid_safety = df[df["SafetyStock"] > df["MaximumStock"]]
    if len(invalid_safety) > 0:
        violations["SafetyStock > MaximumStock"] = len(invalid_safety)
        details["SafetyStock > MaxStock"] = invalid_safety["ProductID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Rule 4: ReorderPoint should be between MinimumStock and MaximumStock
    # -------------------------------------------------------------------------
    # The reorder point triggers a new order. It should be within the
    # operating range of the inventory.
    invalid_reorder = df[
        (df["ReorderPoint"] < df["MinimumStock"]) |
        (df["ReorderPoint"] > df["MaximumStock"])
    ]
    if len(invalid_reorder) > 0:
        violations["ReorderPoint outside Min-Max range"] = len(invalid_reorder)
        details["ReorderPoint out of range"] = invalid_reorder["ProductID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Rule 5: LeadTimeDays must be positive (≥ 1)
    # -------------------------------------------------------------------------
    # It always takes at least 1 day to receive a new shipment.
    invalid_lead = df[df["LeadTimeDays"] < 1]
    if len(invalid_lead) > 0:
        violations["LeadTimeDays < 1"] = len(invalid_lead)
        details["Invalid LeadTime"] = invalid_lead["ProductID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Rule 6: Warehouse must be a valid warehouse
    # -------------------------------------------------------------------------
    invalid_wh = df[~df["Warehouse"].isin(VALID_WAREHOUSES)]
    if len(invalid_wh) > 0:
        violations["Invalid Warehouse"] = len(invalid_wh)
        details["Invalid Warehouse"] = invalid_wh["Warehouse"].unique().tolist()

    # -------------------------------------------------------------------------
    # Rule 7: InventoryStatus must be a valid status
    # -------------------------------------------------------------------------
    invalid_status = df[~df["InventoryStatus"].isin(VALID_STATUSES)]
    if len(invalid_status) > 0:
        violations["Invalid InventoryStatus"] = len(invalid_status)
        details["Invalid InventoryStatus"] = invalid_status["InventoryStatus"].unique().tolist()

    # -------------------------------------------------------------------------
    # Rule 8: InventoryStatus consistency
    # -------------------------------------------------------------------------
    # If CurrentStock = 0, status should be "Out of Stock"
    # This checks if the status LABEL matches the actual stock level.
    zero_stock_wrong_status = df[
        (df["CurrentStock"] == 0) & (df["InventoryStatus"] != "Out of Stock")
    ]
    if len(zero_stock_wrong_status) > 0:
        violations["CurrentStock=0 but status != 'Out of Stock'"] = len(zero_stock_wrong_status)
        details["Zero stock status mismatch"] = {
            "ids": zero_stock_wrong_status["ProductID"].tolist()[:5],
            "statuses": zero_stock_wrong_status["InventoryStatus"].tolist()[:5]
        }

    # -------------------------------------------------------------------------
    # Rule 9: ProductID format (P followed by 4 digits)
    # -------------------------------------------------------------------------
    invalid_id = df[~df["ProductID"].str.match(r"^P\d{4}$")]
    if len(invalid_id) > 0:
        violations["Invalid ProductID format"] = len(invalid_id)
        details["Invalid ProductID"] = invalid_id["ProductID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Summarize
    # -------------------------------------------------------------------------
    passed = len(violations) == 0

    if passed:
        logger.info("✅ Business rules validation PASSED — all 9 rules satisfied")
    else:
        logger.warning(f"❌ Business rules validation FAILED — {len(violations)} rule(s) violated")
        for rule, count in violations.items():
            logger.warning(f"   {rule}: {count} violation(s)")

    return {"passed": passed, "violations": violations, "details": details}


# =============================================================================
# FUNCTION 7: validate_referential_integrity()
# =============================================================================
def validate_referential_integrity(df: pd.DataFrame) -> Dict[str, object]:
    """
    Validate that every ProductID in inventory exists in the products dataset.

    Each inventory record tracks stock for a specific product.
    If a ProductID doesn't match any product, we're tracking stock
    for a product that doesn't exist — a phantom inventory record.
    """
    issues: Dict[str, object] = {}

    try:
        products_df = pd.read_excel(PRODUCTS_FILE, engine="openpyxl")
        valid_product_ids = set(products_df["ProductID"].unique())
        inventory_product_ids = set(df["ProductID"].unique())

        orphan_products = inventory_product_ids - valid_product_ids

        if len(orphan_products) > 0:
            issues["Orphan ProductIDs (not in products file)"] = {
                "count": len(orphan_products),
                "samples": list(orphan_products)[:10]
            }
            logger.warning(
                f"❌ {len(orphan_products)} ProductID(s) in inventory "
                f"not found in products dataset"
            )
        else:
            logger.info(
                f"✅ ProductID integrity PASSED — all {len(inventory_product_ids)} "
                f"products found in products dataset"
            )

        # Also check: do all products HAVE an inventory record?
        # Products without inventory records are "untracked" products.
        missing_inventory = valid_product_ids - inventory_product_ids
        if len(missing_inventory) > 0:
            issues["Products without inventory records"] = {
                "count": len(missing_inventory),
                "samples": list(missing_inventory)[:10]
            }
            logger.warning(
                f"⚠️  {len(missing_inventory)} product(s) have no inventory record"
            )

    except Exception as e:
        issues["ProductID check error"] = str(e)
        logger.error(f"Could not verify ProductIDs: {e}")

    passed = len(issues) == 0

    if passed:
        logger.info("✅ Referential integrity PASSED")

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
    """Generate and save a detailed validation report for the inventory dataset."""
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    lines: List[str] = []

    # --- Header ---
    lines.append("=" * 70)
    lines.append("VALIDATION REPORT — INVENTORY DATASET")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Source File: {RAW_FILE_PATH}")
    lines.append("=" * 70)
    lines.append("")

    # --- Dataset Summary ---
    lines.append("📊 DATASET SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  Total Rows        : {df.shape[0]}")
    lines.append(f"  Total Columns     : {df.shape[1]}")
    lines.append(f"  Unique Warehouses : {df['Warehouse'].nunique()}")
    lines.append(f"  Warehouses        : {df['Warehouse'].unique().tolist()}")
    lines.append(f"  Status Distribution:")
    for status, count in df["InventoryStatus"].value_counts().items():
        lines.append(f"    {status}: {count}")
    lines.append(f"  CurrentStock Range: {df['CurrentStock'].min()} — {df['CurrentStock'].max()}")
    lines.append(f"  Total Stock Units : {df['CurrentStock'].sum():,}")
    lines.append("")

    # --- 1. Schema ---
    lines.append("1️⃣  SCHEMA VALIDATION")
    lines.append("-" * 40)
    lines.append(f"  Status : {'✅ PASSED' if schema_result['passed'] else '❌ FAILED'}")
    if schema_result["missing"]:
        lines.append(f"  Missing: {schema_result['missing']}")
    lines.append("")

    # --- 2. Missing Values ---
    lines.append("2️⃣  MISSING VALUES CHECK")
    lines.append("-" * 40)
    lines.append(f"  Status      : {'✅ PASSED' if missing_result['passed'] else '❌ FAILED'}")
    lines.append(f"  Total Nulls : {missing_result['total_nulls']}")
    if missing_result["null_counts"]:
        for col, count in missing_result["null_counts"].items():
            lines.append(f"  → {col}: {count} null(s)")
    lines.append("")

    # --- 3. Duplicates ---
    lines.append("3️⃣  DUPLICATE CHECK")
    lines.append("-" * 40)
    lines.append(f"  Status             : {'✅ PASSED' if duplicate_result['passed'] else '❌ FAILED'}")
    lines.append(f"  Duplicate ProductIDs: {duplicate_result['duplicate_product_ids']}")
    lines.append(f"  Full Duplicates     : {duplicate_result['full_duplicates']}")
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
            lines.append(f"  → {rule}: {count} violation(s)")
    if business_result["details"]:
        lines.append("  Sample violating records:")
        for rule, detail in business_result["details"].items():
            lines.append(f"    {rule}: {detail}")
    lines.append("")

    # --- 6. Referential Integrity ---
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
    Run the complete validation pipeline for the inventory dataset.
    """
    logger.info("=" * 60)
    logger.info("STARTING VALIDATION: Inventory Dataset")
    logger.info("=" * 60)

    # Step 1: Load raw data
    try:
        df = load_data(RAW_FILE_PATH)
    except (FileNotFoundError, Exception) as e:
        logger.error(f"Cannot proceed with validation: {e}")
        return False

    # Step 2: Run all validations
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
        logger.info("🎉 Inventory validation COMPLETED — ALL CHECKS PASSED")
    else:
        logger.warning("⚠️  Inventory validation COMPLETED — SOME CHECKS FAILED")
        logger.warning("   Review the report: " + REPORT_FILE)

    return all_passed


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
