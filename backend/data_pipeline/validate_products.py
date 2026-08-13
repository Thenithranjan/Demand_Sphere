"""
==============================================================================
Script 1: validate_products.py
==============================================================================
Purpose:
    Validates the raw products dataset (products_500_textile_dataset.xlsx)
    to ensure data quality BEFORE any cleaning or transformation.

Why this script is needed:
    In professional data engineering, you NEVER trust raw data. Even if you
    created the dataset yourself, validation catches:
    - Missing columns (schema drift)
    - Null values (incomplete records)
    - Duplicate records (data entry errors)
    - Wrong data types (text in numeric fields)
    - Business rule violations (price < 0, cost > price)

    This is the FIRST step in any data pipeline. If validation fails,
    you stop the pipeline — you don't feed bad data to AI models.

Which AI modules use this:
    ALL THREE modules depend on clean product data:
    - Product Recommendation: needs accurate categories, prices, fabrics
    - Demand Forecasting: needs valid seasonal tags and product status
    - Inventory Management: needs correct supplier IDs and pricing

Output:
    - Console log summary (via Python logging)
    - Detailed report saved to: reports/validation_report_products.txt
==============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# 'os' provides functions to interact with the operating system (paths, dirs)
import os

# 'sys' provides access to system-specific parameters (we use it for exit codes)
import sys

# 'logging' is Python's built-in module for tracking events during execution.
# Unlike print(), logging lets you control severity levels (DEBUG, INFO, WARNING,
# ERROR, CRITICAL) and output destinations (console, file, etc.)
import logging

# 'datetime' helps us timestamp our validation reports
from datetime import datetime

# 'pathlib.Path' is a modern, object-oriented way to handle file paths.
# It works across Windows, Mac, and Linux without worrying about / vs \
from pathlib import Path

# 'typing' provides type hint utilities. Type hints don't affect runtime
# but make your code self-documenting and help IDEs catch bugs early.
from typing import Dict, List, Tuple

# 'pandas' is the core data manipulation library. We alias it as 'pd'
# by convention — every data engineer in the world uses this alias.
import pandas as pd


# =============================================================================
# CONSTANTS
# =============================================================================
# Constants are values that NEVER change during program execution.
# By convention, they are written in UPPER_CASE.
# Keeping them at the top of the file makes them easy to find and update.

# Path to the raw products Excel file (relative to project root)
RAW_FILE_PATH: str = os.path.join("data", "raw", "products_500_textile_dataset.xlsx")

# Path where validation reports will be saved
REPORT_DIR: str = "reports"
REPORT_FILE: str = os.path.join(REPORT_DIR, "validation_report_products.txt")

# These are the columns we EXPECT to find in the products dataset.
# If any column is missing, the data source has changed (schema drift).
REQUIRED_COLUMNS: List[str] = [
    "ProductID", "SKU", "ProductName", "Category", "SubCategory",
    "Brand", "Color", "Size", "Fabric", "SeasonalDemandTag",
    "Gender", "Price", "CostPrice", "SupplierID", "ProductStatus",
    "ImageURL"
]

# Valid values for categorical columns.
# These come from business domain knowledge — what values SHOULD exist.
VALID_CATEGORIES: List[str] = ["Men", "Women", "Kids", "Accessories", "Home & Lifestyle"]
VALID_GENDERS: List[str] = ["Men", "Women", "Unisex", "Kids"]
VALID_FABRICS: List[str] = [
    "Cotton", "Silk", "Handloom", "Polyester", "Polyester Blend", "Linen", "Leather"
]
VALID_STATUSES: List[str] = ["Active", "Inactive", "Discontinued"]


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
# We configure logging ONCE at module level. All functions in this file
# will use the same logger instance.
#
# logging.basicConfig() sets up the root logger with:
#   - level=logging.INFO  → show INFO, WARNING, ERROR, CRITICAL (hide DEBUG)
#   - format              → how each log message looks
#     %(asctime)s         → timestamp (e.g., 2026-07-20 20:30:00)
#     %(levelname)-8s     → severity level, padded to 8 chars (e.g., "INFO    ")
#     %(message)s         → the actual message you pass to logger.info(), etc.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Create a logger specific to this module.
# __name__ automatically becomes "validate_products" when run directly,
# or "backend.data_pipeline.validate_products" when imported as a package.
logger = logging.getLogger(__name__)


# =============================================================================
# FUNCTION 1: load_data()
# =============================================================================
def load_data(file_path: str) -> pd.DataFrame:
    """
    Load an Excel file into a pandas DataFrame.

    Parameters
    ----------
    file_path : str
        Path to the Excel file (relative or absolute).

    Returns
    -------
    pd.DataFrame
        The loaded data as a table (rows and columns).

    Raises
    ------
    FileNotFoundError
        If the file does not exist at the given path.
    Exception
        If the file cannot be read (corrupted, wrong format, etc.)

    How it works
    ------------
    1. We first check if the file exists using os.path.exists().
       This gives a clear error message instead of a cryptic pandas error.
    2. pd.read_excel() reads the .xlsx file and returns a DataFrame.
       The openpyxl engine (installed via requirements.txt) handles the
       Excel format parsing behind the scenes.
    3. We log the shape (rows × columns) as a quick sanity check.
    """
    # Check if the file actually exists before trying to read it.
    # This is a DEFENSIVE PROGRAMMING practice — always validate inputs.
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Raw data file not found: {file_path}")

    # Try to read the Excel file. If anything goes wrong (corrupted file,
    # wrong format, missing openpyxl), the except block catches it.
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
        logger.info(f"Successfully loaded '{file_path}' → {df.shape[0]} rows × {df.shape[1]} columns")
        return df
    except Exception as e:
        # 'e' contains the original error message from pandas/openpyxl
        logger.error(f"Failed to read '{file_path}': {e}")
        raise


# =============================================================================
# FUNCTION 2: validate_schema()
# =============================================================================
def validate_schema(df: pd.DataFrame, required_columns: List[str]) -> Dict[str, object]:
    """
    Check if the DataFrame contains all required columns.

    Parameters
    ----------
    df : pd.DataFrame
        The loaded products data.
    required_columns : List[str]
        List of column names that MUST be present.

    Returns
    -------
    Dict with keys:
        - "passed" (bool): True if all required columns are present.
        - "missing" (List[str]): Columns that are required but not found.
        - "extra" (List[str]): Columns found but not in required list.

    Why this matters
    ----------------
    Schema drift happens when upstream data sources change their format.
    For example, someone renames "Price" to "UnitPrice" in the Excel file.
    Without schema validation, your pipeline would crash with a confusing
    KeyError deep inside the code. This function catches it early.
    """
    # set() converts a list to a set, which supports mathematical operations
    # like difference (-) and intersection (&). Sets also ignore duplicates.
    actual_columns = set(df.columns)
    expected_columns = set(required_columns)

    # Columns that should exist but don't
    missing = expected_columns - actual_columns

    # Columns that exist but weren't expected (not necessarily bad, just noted)
    extra = actual_columns - expected_columns

    passed = len(missing) == 0

    if passed:
        logger.info("✅ Schema validation PASSED — all required columns present")
    else:
        logger.warning(f"❌ Schema validation FAILED — missing columns: {missing}")

    if extra:
        logger.info(f"ℹ️  Extra columns found (not required): {extra}")

    return {"passed": passed, "missing": list(missing), "extra": list(extra)}


# =============================================================================
# FUNCTION 3: validate_missing_values()
# =============================================================================
def validate_missing_values(df: pd.DataFrame) -> Dict[str, object]:
    """
    Check for null/missing values in every column.

    Returns
    -------
    Dict with keys:
        - "passed" (bool): True if NO nulls found anywhere.
        - "total_nulls" (int): Total number of null cells.
        - "null_counts" (Dict[str, int]): Per-column null counts (only cols with nulls).

    Why this matters
    ----------------
    Missing values can cause:
    - AI models to crash (most ML algorithms can't handle NaN)
    - Incorrect calculations (mean of [10, NaN, 20] isn't 15 in some libraries)
    - Silent data loss (rows with nulls get dropped during joins)
    """
    # df.isnull() returns a DataFrame of True/False (True where value is null)
    # .sum() adds up the True values per column (True=1, False=0)
    null_counts = df.isnull().sum()

    # Filter to only show columns that have at least 1 null
    columns_with_nulls = null_counts[null_counts > 0]

    # .sum() on null_counts gives the grand total across all columns
    total_nulls = int(null_counts.sum())

    passed = total_nulls == 0

    if passed:
        logger.info("✅ Missing values check PASSED — no nulls found")
    else:
        logger.warning(f"❌ Missing values check FAILED — {total_nulls} null(s) found")
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
    Check for duplicate records based on key columns (ProductID, SKU).

    Returns
    -------
    Dict with keys:
        - "passed" (bool): True if NO duplicates found.
        - "duplicate_product_ids" (int): Count of duplicate ProductID values.
        - "duplicate_skus" (int): Count of duplicate SKU values.
        - "full_duplicates" (int): Count of entirely duplicated rows.

    Why this matters
    ----------------
    Duplicates cause:
    - Double-counting in sales analytics
    - Inflated inventory numbers
    - Recommendation model confusion (same product appears twice)
    """
    # df.duplicated() marks True for rows that are exact copies of an earlier row.
    # This checks ALL columns — a row must match in every single field to be flagged.
    full_duplicates = int(df.duplicated().sum())

    # Check specifically for duplicate ProductIDs — this is the primary key.
    # In databases, primary keys must be unique. Same rule applies here.
    dup_product_ids = int(df["ProductID"].duplicated().sum())

    # SKU (Stock Keeping Unit) should also be unique per product.
    dup_skus = int(df["SKU"].duplicated().sum())

    passed = (full_duplicates == 0) and (dup_product_ids == 0) and (dup_skus == 0)

    if passed:
        logger.info("✅ Duplicate check PASSED — no duplicates found")
    else:
        logger.warning(f"❌ Duplicate check FAILED")
        if dup_product_ids > 0:
            logger.warning(f"   Duplicate ProductIDs: {dup_product_ids}")
        if dup_skus > 0:
            logger.warning(f"   Duplicate SKUs: {dup_skus}")
        if full_duplicates > 0:
            logger.warning(f"   Fully duplicated rows: {full_duplicates}")

    return {
        "passed": passed,
        "duplicate_product_ids": dup_product_ids,
        "duplicate_skus": dup_skus,
        "full_duplicates": full_duplicates
    }


# =============================================================================
# FUNCTION 5: validate_data_types()
# =============================================================================
def validate_data_types(df: pd.DataFrame) -> Dict[str, object]:
    """
    Validate that columns have the expected data types.

    Returns
    -------
    Dict with keys:
        - "passed" (bool): True if all critical types are correct.
        - "issues" (List[str]): Description of any type mismatches.

    Why this matters
    ----------------
    If Price is stored as text ("1500" instead of 1500), mathematical
    operations like mean(), sum(), and comparisons (Price > CostPrice)
    will either fail or produce wrong results.
    """
    issues: List[str] = []

    # --- Numeric columns must be int or float ---
    # pd.api.types.is_numeric_dtype() returns True for int64, float64, etc.
    numeric_columns = ["Price", "CostPrice"]
    for col in numeric_columns:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            issues.append(f"Column '{col}' should be numeric but is {df[col].dtype}")

    # --- String columns must be object or string dtype ---
    string_columns = [
        "ProductID", "SKU", "ProductName", "Category", "SubCategory",
        "Brand", "Color", "Size", "Fabric", "Gender", "ProductStatus"
    ]
    for col in string_columns:
        if col in df.columns:
            # In pandas, text data is stored as 'object' or 'string' dtype
            if df[col].dtype not in ["object", "string", "str"]:
                issues.append(f"Column '{col}' should be text but is {df[col].dtype}")

    passed = len(issues) == 0

    if passed:
        logger.info("✅ Data type validation PASSED — all types correct")
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
    Validate domain-specific business rules for textile products.

    Business rules are constraints that come from real-world knowledge,
    NOT from the data itself. For example:
    - A product's price can't be negative (you can't pay -₹500 for a saree)
    - Cost price should be less than selling price (or you're losing money)
    - Category must be one of the known categories (not "Xyz123")

    Returns
    -------
    Dict with keys:
        - "passed" (bool): True if all business rules are satisfied.
        - "violations" (Dict[str, int]): Count of violations per rule.
        - "details" (Dict[str, pd.DataFrame]): Sample violating rows.
    """
    violations: Dict[str, int] = {}
    details: Dict[str, str] = {}

    # -------------------------------------------------------------------------
    # Rule 1: Price must be positive (Price > 0)
    # -------------------------------------------------------------------------
    # A product cannot have zero or negative price in a retail store.
    invalid_price = df[df["Price"] <= 0]
    if len(invalid_price) > 0:
        violations["Price <= 0"] = len(invalid_price)
        details["Price <= 0"] = invalid_price["ProductID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Rule 2: CostPrice must be positive (CostPrice > 0)
    # -------------------------------------------------------------------------
    invalid_cost = df[df["CostPrice"] <= 0]
    if len(invalid_cost) > 0:
        violations["CostPrice <= 0"] = len(invalid_cost)
        details["CostPrice <= 0"] = invalid_cost["ProductID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Rule 3: Price should be greater than CostPrice
    # -------------------------------------------------------------------------
    # If cost > price, the store is selling at a loss. This is a warning,
    # not necessarily invalid (clearance sales exist), but worth flagging.
    price_below_cost = df[df["Price"] <= df["CostPrice"]]
    if len(price_below_cost) > 0:
        violations["Price <= CostPrice (negative margin)"] = len(price_below_cost)
        details["Price <= CostPrice"] = price_below_cost["ProductID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Rule 4: Category must be from the valid list
    # -------------------------------------------------------------------------
    # ~ is the NOT operator for boolean Series. isin() checks membership.
    invalid_category = df[~df["Category"].isin(VALID_CATEGORIES)]
    if len(invalid_category) > 0:
        violations["Invalid Category"] = len(invalid_category)
        details["Invalid Category"] = invalid_category["Category"].unique().tolist()

    # -------------------------------------------------------------------------
    # Rule 5: Gender must be from the valid list
    # -------------------------------------------------------------------------
    invalid_gender = df[~df["Gender"].isin(VALID_GENDERS)]
    if len(invalid_gender) > 0:
        violations["Invalid Gender"] = len(invalid_gender)
        details["Invalid Gender"] = invalid_gender["Gender"].unique().tolist()

    # -------------------------------------------------------------------------
    # Rule 6: Fabric must be from the valid list
    # -------------------------------------------------------------------------
    invalid_fabric = df[~df["Fabric"].isin(VALID_FABRICS)]
    if len(invalid_fabric) > 0:
        violations["Invalid Fabric"] = len(invalid_fabric)
        details["Invalid Fabric"] = invalid_fabric["Fabric"].unique().tolist()

    # -------------------------------------------------------------------------
    # Rule 7: ProductStatus must be from the valid list
    # -------------------------------------------------------------------------
    invalid_status = df[~df["ProductStatus"].isin(VALID_STATUSES)]
    if len(invalid_status) > 0:
        violations["Invalid ProductStatus"] = len(invalid_status)
        details["Invalid ProductStatus"] = invalid_status["ProductStatus"].unique().tolist()

    # -------------------------------------------------------------------------
    # Rule 8: ProductID should follow the pattern P0001, P0002, etc.
    # -------------------------------------------------------------------------
    # str.match() checks if each value matches a regular expression.
    # r"^P\d{4}$" means: starts with P, followed by exactly 4 digits, then ends.
    invalid_id_format = df[~df["ProductID"].str.match(r"^P\d{4}$")]
    if len(invalid_id_format) > 0:
        violations["Invalid ProductID format"] = len(invalid_id_format)
        details["Invalid ProductID format"] = invalid_id_format["ProductID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Summarize results
    # -------------------------------------------------------------------------
    passed = len(violations) == 0

    if passed:
        logger.info("✅ Business rules validation PASSED — all rules satisfied")
    else:
        logger.warning(f"❌ Business rules validation FAILED — {len(violations)} rule(s) violated")
        for rule, count in violations.items():
            logger.warning(f"   {rule}: {count} violation(s)")

    return {"passed": passed, "violations": violations, "details": details}


# =============================================================================
# FUNCTION 7: generate_report()
# =============================================================================
def generate_report(
    df: pd.DataFrame,
    schema_result: Dict,
    missing_result: Dict,
    duplicate_result: Dict,
    dtype_result: Dict,
    business_result: Dict,
    report_path: str
) -> None:
    """
    Generate a detailed text report and save it to disk.

    Parameters
    ----------
    df : pd.DataFrame
        The original data (for summary statistics).
    schema_result, missing_result, ... : Dict
        Results from each validation function.
    report_path : str
        Where to save the report file.

    Why save a report?
    ------------------
    In production data pipelines:
    - Reports create an AUDIT TRAIL (proof that data was validated)
    - QA teams review reports without running code
    - Reports help debug issues when something goes wrong downstream
    - Regulatory compliance may require documented data quality checks
    """
    # Ensure the reports directory exists.
    # os.makedirs() creates all intermediate directories.
    # exist_ok=True means "don't error if the directory already exists"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    # We build the report as a list of strings, then join them at the end.
    # This is more efficient than string concatenation (+=) in Python.
    lines: List[str] = []

    # Header
    lines.append("=" * 70)
    lines.append("VALIDATION REPORT — PRODUCTS DATASET")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Source File: {RAW_FILE_PATH}")
    lines.append("=" * 70)
    lines.append("")

    # --- Dataset Summary ---
    lines.append("📊 DATASET SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  Total Rows    : {df.shape[0]}")
    lines.append(f"  Total Columns : {df.shape[1]}")
    lines.append(f"  Column Names  : {list(df.columns)}")
    lines.append("")

    # --- Schema Validation ---
    lines.append("1️⃣  SCHEMA VALIDATION")
    lines.append("-" * 40)
    lines.append(f"  Status  : {'✅ PASSED' if schema_result['passed'] else '❌ FAILED'}")
    if schema_result["missing"]:
        lines.append(f"  Missing : {schema_result['missing']}")
    if schema_result["extra"]:
        lines.append(f"  Extra   : {schema_result['extra']}")
    lines.append("")

    # --- Missing Values ---
    lines.append("2️⃣  MISSING VALUES CHECK")
    lines.append("-" * 40)
    lines.append(f"  Status      : {'✅ PASSED' if missing_result['passed'] else '❌ FAILED'}")
    lines.append(f"  Total Nulls : {missing_result['total_nulls']}")
    if missing_result["null_counts"]:
        for col, count in missing_result["null_counts"].items():
            lines.append(f"  → {col}: {count} null(s)")
    lines.append("")

    # --- Duplicates ---
    lines.append("3️⃣  DUPLICATE CHECK")
    lines.append("-" * 40)
    lines.append(f"  Status             : {'✅ PASSED' if duplicate_result['passed'] else '❌ FAILED'}")
    lines.append(f"  Duplicate ProductIDs : {duplicate_result['duplicate_product_ids']}")
    lines.append(f"  Duplicate SKUs       : {duplicate_result['duplicate_skus']}")
    lines.append(f"  Fully Duplicated Rows: {duplicate_result['full_duplicates']}")
    lines.append("")

    # --- Data Types ---
    lines.append("4️⃣  DATA TYPE VALIDATION")
    lines.append("-" * 40)
    lines.append(f"  Status : {'✅ PASSED' if dtype_result['passed'] else '❌ FAILED'}")
    if dtype_result["issues"]:
        for issue in dtype_result["issues"]:
            lines.append(f"  → {issue}")
    lines.append("")

    # --- Business Rules ---
    lines.append("5️⃣  BUSINESS RULES VALIDATION")
    lines.append("-" * 40)
    lines.append(f"  Status : {'✅ PASSED' if business_result['passed'] else '❌ FAILED'}")
    if business_result["violations"]:
        for rule, count in business_result["violations"].items():
            lines.append(f"  → {rule}: {count} violation(s)")
    if business_result["details"]:
        lines.append("  Sample violating records:")
        for rule, samples in business_result["details"].items():
            lines.append(f"    {rule}: {samples}")
    lines.append("")

    # --- Overall Result ---
    all_passed = all([
        schema_result["passed"],
        missing_result["passed"],
        duplicate_result["passed"],
        dtype_result["passed"],
        business_result["passed"]
    ])
    lines.append("=" * 70)
    lines.append(f"OVERALL RESULT: {'✅ ALL CHECKS PASSED' if all_passed else '⚠️  SOME CHECKS FAILED'}")
    lines.append("=" * 70)

    # --- Write to file ---
    # 'w' mode creates the file if it doesn't exist, or overwrites if it does.
    # encoding='utf-8' ensures emojis and special characters are saved correctly.
    report_text = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    logger.info(f"📄 Validation report saved to: {report_path}")


# =============================================================================
# FUNCTION 8: run_validation() — The Orchestrator
# =============================================================================
def run_validation() -> bool:
    """
    Run the complete validation pipeline for the products dataset.

    This is the ORCHESTRATOR function — it calls all other functions
    in the correct order and decides whether validation passed overall.

    Returns
    -------
    bool
        True if all validations passed, False otherwise.

    Design Pattern
    --------------
    This follows the 'Pipeline' pattern:
    1. Load data
    2. Run validations (each returns a result dictionary)
    3. Generate report
    4. Return overall pass/fail

    Each step is independent — if one validation fails, we still run
    the others so the report is complete.
    """
    logger.info("=" * 60)
    logger.info("STARTING VALIDATION: Products Dataset")
    logger.info("=" * 60)

    # Step 1: Load the raw data
    try:
        df = load_data(RAW_FILE_PATH)
    except (FileNotFoundError, Exception) as e:
        logger.error(f"Cannot proceed with validation: {e}")
        return False

    # Step 2: Run all validation checks
    # Each function returns a dictionary with 'passed' key and details.
    schema_result = validate_schema(df, REQUIRED_COLUMNS)
    missing_result = validate_missing_values(df)
    duplicate_result = validate_duplicates(df)
    dtype_result = validate_data_types(df)
    business_result = validate_business_rules(df)

    # Step 3: Generate and save the report
    generate_report(
        df=df,
        schema_result=schema_result,
        missing_result=missing_result,
        duplicate_result=duplicate_result,
        dtype_result=dtype_result,
        business_result=business_result,
        report_path=REPORT_FILE
    )

    # Step 4: Determine overall pass/fail
    all_passed = all([
        schema_result["passed"],
        missing_result["passed"],
        duplicate_result["passed"],
        dtype_result["passed"],
        business_result["passed"]
    ])

    if all_passed:
        logger.info("🎉 Products validation COMPLETED — ALL CHECKS PASSED")
    else:
        logger.warning("⚠️  Products validation COMPLETED — SOME CHECKS FAILED")
        logger.warning("   Review the report for details: " + REPORT_FILE)

    return all_passed


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
# This block only runs when you execute the script directly:
#     py backend/data_pipeline/validate_products.py
#
# It does NOT run when the script is imported by another module:
#     from backend.data_pipeline.validate_products import run_validation
#
# This is a Python best practice called the "main guard" or "dunder main check".

if __name__ == "__main__":
    success = run_validation()

    # sys.exit(0) means "success", sys.exit(1) means "failure".
    # This is important for CI/CD pipelines — automated systems check
    # exit codes to decide whether to proceed or stop the pipeline.
    sys.exit(0 if success else 1)
