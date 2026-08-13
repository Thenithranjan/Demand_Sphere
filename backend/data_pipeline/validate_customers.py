"""
==============================================================================
Script 2: validate_customers.py
==============================================================================
Purpose:
    Validates the raw customers dataset (customers_2000_textile_dataset.xlsx)
    to ensure data quality BEFORE any cleaning or transformation.

Why this script is needed:
    Customer data drives the Product Recommendation System. If a customer's
    age is -5, or their membership tier is "Xyz", or their preferred
    category doesn't match any real product category — the recommendation
    model will learn WRONG patterns and suggest irrelevant products.

    In real companies, customer data comes from multiple sources:
    - Website registration forms
    - Point-of-sale systems
    - Loyalty card sign-ups
    - Manual data entry by staff

    Each source can introduce different errors. Validation catches them all.

Which AI modules use this:
    - Product Recommendation System: Uses customer preferences (category,
      fabric, price range) and demographics (age, gender) to suggest products.
    - Demand Forecasting: Customer demographics help predict seasonal demand
      (e.g., young customers buy more during festive seasons).
    - Inventory Management: Customer location (city) affects which warehouse
      should stock which products.

Output:
    - Console log summary (via Python logging)
    - Detailed report saved to: reports/validation_report_customers.txt
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
# Path to the raw customers Excel file
RAW_FILE_PATH: str = os.path.join("data", "raw", "customers_2000_textile_dataset.xlsx")

# Report output path
REPORT_DIR: str = "reports"
REPORT_FILE: str = os.path.join(REPORT_DIR, "validation_report_customers.txt")

# Expected columns in the customers dataset.
# These 12 columns define the "contract" between the data source and our pipeline.
REQUIRED_COLUMNS: List[str] = [
    "CustomerID", "FullName", "Gender", "Age", "City", "State",
    "Membership", "JoinDate", "PreferredCategory", "PreferredFabric",
    "PreferredPriceRange", "LoyaltyPoints"
]

# Valid categorical values — derived from business domain knowledge.
# These must match what the textile store actually uses in their system.
VALID_GENDERS: List[str] = ["Male", "Female"]
VALID_MEMBERSHIPS: List[str] = ["Bronze", "Silver", "Gold", "Platinum"]
VALID_CATEGORIES: List[str] = ["Men", "Women", "Kids", "Accessories", "Home & Lifestyle"]
VALID_FABRICS: List[str] = ["Cotton", "Silk", "Handloom", "Polyester", "Linen"]
VALID_PRICE_RANGES: List[str] = ["Budget", "Standard", "Premium", "Luxury"]

# Age constraints — based on Indian retail industry norms.
# Minimum 18 (adults only for individual accounts), maximum 100.
MIN_AGE: int = 18
MAX_AGE: int = 100


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

    This function is intentionally similar to the one in validate_products.py.
    In a later refactoring phase, we would extract this into a shared utility
    module (backend/utils/data_loader.py) to follow the DRY principle
    (Don't Repeat Yourself). For now, keeping it here makes each script
    self-contained and easy to understand independently.

    Parameters
    ----------
    file_path : str
        Path to the Excel file.

    Returns
    -------
    pd.DataFrame
        The loaded customer data.
    """
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
    """
    Check if the DataFrame contains all 12 required customer columns.

    How it works
    ------------
    We convert both actual and expected column lists to sets, then use
    set subtraction to find:
    - Missing columns: required but not in data (schema drift)
    - Extra columns: in data but not required (usually harmless, just noted)

    Example:
        required = {"A", "B", "C"}
        actual   = {"A", "B", "D"}
        missing  = {"C"}     ← required - actual
        extra    = {"D"}     ← actual - required
    """
    actual = set(df.columns)
    expected = set(required_columns)

    missing = list(expected - actual)
    extra = list(actual - expected)
    passed = len(missing) == 0

    if passed:
        logger.info("✅ Schema validation PASSED — all 12 required columns present")
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
    Check for null/missing values across all customer columns.

    Why this is critical for customer data
    ---------------------------------------
    - Missing Gender → recommendation model can't filter by gender preferences
    - Missing Age → age-based segmentation fails
    - Missing Membership → loyalty-based pricing breaks
    - Missing City → location-based inventory decisions become inaccurate
    """
    null_counts = df.isnull().sum()
    columns_with_nulls = null_counts[null_counts > 0]
    total_nulls = int(null_counts.sum())

    passed = total_nulls == 0

    if passed:
        logger.info("✅ Missing values check PASSED — no nulls in 2000 customer records")
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
    Check for duplicate customer records.

    Why duplicates are dangerous in customer data
    ----------------------------------------------
    If customer C00042 appears twice:
    - Their purchase history is split across two records
    - Recommendation model sees two "different" customers with incomplete data
    - Loyalty points calculations become wrong
    - Marketing campaigns may send duplicate communications

    We check three things:
    1. Duplicate CustomerID (primary key — MUST be unique)
    2. Duplicate FullName (warning only — real people can share names)
    3. Fully identical rows (copy-paste errors)
    """
    # Primary key uniqueness — this is mandatory
    dup_ids = int(df["CustomerID"].duplicated().sum())

    # Full row duplicates — every single column matches
    full_dups = int(df.duplicated().sum())

    # Name duplicates — informational only (not a failure condition)
    # Two different customers can genuinely have the same name
    dup_names = int(df["FullName"].duplicated().sum())

    # We only fail on CustomerID duplicates or full row duplicates
    # Name duplicates are just warnings
    passed = (dup_ids == 0) and (full_dups == 0)

    if passed:
        logger.info("✅ Duplicate check PASSED — all CustomerIDs are unique")
    else:
        logger.warning(f"❌ Duplicate check FAILED")
        if dup_ids > 0:
            logger.warning(f"   Duplicate CustomerIDs: {dup_ids}")
        if full_dups > 0:
            logger.warning(f"   Fully duplicated rows: {full_dups}")

    if dup_names > 0:
        # This is just informational — same name doesn't mean same person
        logger.info(f"ℹ️  Duplicate FullNames (informational): {dup_names}")

    return {
        "passed": passed,
        "duplicate_customer_ids": dup_ids,
        "duplicate_names_info": dup_names,
        "full_duplicates": full_dups
    }


# =============================================================================
# FUNCTION 5: validate_data_types()
# =============================================================================
def validate_data_types(df: pd.DataFrame) -> Dict[str, object]:
    """
    Validate that customer columns have the expected data types.

    Expected types:
    - Age, LoyaltyPoints  → numeric (int or float)
    - JoinDate            → should be parseable as a date
    - Everything else     → text (object/string)

    Why JoinDate is special
    -----------------------
    JoinDate is stored as text in the Excel file (e.g., "2023-08-06").
    We check if it can be PARSED as a date, not whether pandas already
    recognizes it as datetime. The cleaning script will do the conversion.
    """
    issues: List[str] = []

    # --- Numeric columns ---
    numeric_cols = ["Age", "LoyaltyPoints"]
    for col in numeric_cols:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            issues.append(f"Column '{col}' should be numeric but is {df[col].dtype}")

    # --- Date column (check if parseable) ---
    if "JoinDate" in df.columns:
        try:
            # pd.to_datetime() attempts to parse each value as a date.
            # errors='coerce' means "if a value can't be parsed, replace it with NaT (Not a Time)"
            # We then check how many became NaT — those are unparseable dates.
            parsed_dates = pd.to_datetime(df["JoinDate"], errors="coerce")
            unparseable = int(parsed_dates.isna().sum())
            if unparseable > 0:
                issues.append(
                    f"Column 'JoinDate' has {unparseable} value(s) that cannot be parsed as dates"
                )
        except Exception as e:
            issues.append(f"Column 'JoinDate' date parsing error: {e}")

    # --- String columns ---
    string_cols = [
        "CustomerID", "FullName", "Gender", "City", "State",
        "Membership", "PreferredCategory", "PreferredFabric", "PreferredPriceRange"
    ]
    for col in string_cols:
        if col in df.columns:
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
    Validate domain-specific business rules for textile store customers.

    These rules come from real-world constraints:
    - A customer can't be -5 years old or 200 years old
    - Membership must be one of the actual tiers the store offers
    - Loyalty points can't be negative (you earn them, not owe them)
    - Preferred category should match a real product category
    - CustomerID should follow the C00001 format for consistency

    Each rule is independent — failing one doesn't skip the others.
    This gives a COMPLETE picture of all data quality issues at once.
    """
    violations: Dict[str, int] = {}
    details: Dict[str, object] = {}

    # -------------------------------------------------------------------------
    # Rule 1: Age must be between MIN_AGE and MAX_AGE (18 to 100)
    # -------------------------------------------------------------------------
    # Why this range?
    #   - Under 18: minors can't have individual retail accounts
    #   - Over 100: almost certainly a data entry error
    invalid_age = df[(df["Age"] < MIN_AGE) | (df["Age"] > MAX_AGE)]
    if len(invalid_age) > 0:
        violations["Age out of range (18-100)"] = len(invalid_age)
        details["Age out of range"] = {
            "sample_ids": invalid_age["CustomerID"].tolist()[:5],
            "sample_ages": invalid_age["Age"].tolist()[:5]
        }

    # -------------------------------------------------------------------------
    # Rule 2: LoyaltyPoints must be non-negative (≥ 0)
    # -------------------------------------------------------------------------
    # Points are earned through purchases. Zero is valid (new customer),
    # but negative points indicate a data error.
    negative_points = df[df["LoyaltyPoints"] < 0]
    if len(negative_points) > 0:
        violations["Negative LoyaltyPoints"] = len(negative_points)
        details["Negative LoyaltyPoints"] = negative_points["CustomerID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Rule 3: Gender must be Male or Female
    # -------------------------------------------------------------------------
    invalid_gender = df[~df["Gender"].isin(VALID_GENDERS)]
    if len(invalid_gender) > 0:
        violations["Invalid Gender"] = len(invalid_gender)
        details["Invalid Gender"] = invalid_gender["Gender"].unique().tolist()

    # -------------------------------------------------------------------------
    # Rule 4: Membership must be a valid tier
    # -------------------------------------------------------------------------
    invalid_membership = df[~df["Membership"].isin(VALID_MEMBERSHIPS)]
    if len(invalid_membership) > 0:
        violations["Invalid Membership tier"] = len(invalid_membership)
        details["Invalid Membership"] = invalid_membership["Membership"].unique().tolist()

    # -------------------------------------------------------------------------
    # Rule 5: PreferredCategory must match product categories
    # -------------------------------------------------------------------------
    # This is a CROSS-DATASET validation. The customer's preferred category
    # should match one of the actual product categories.
    invalid_pref_cat = df[~df["PreferredCategory"].isin(VALID_CATEGORIES)]
    if len(invalid_pref_cat) > 0:
        violations["Invalid PreferredCategory"] = len(invalid_pref_cat)
        details["Invalid PreferredCategory"] = invalid_pref_cat["PreferredCategory"].unique().tolist()

    # -------------------------------------------------------------------------
    # Rule 6: PreferredFabric must match product fabrics
    # -------------------------------------------------------------------------
    invalid_pref_fab = df[~df["PreferredFabric"].isin(VALID_FABRICS)]
    if len(invalid_pref_fab) > 0:
        violations["Invalid PreferredFabric"] = len(invalid_pref_fab)
        details["Invalid PreferredFabric"] = invalid_pref_fab["PreferredFabric"].unique().tolist()

    # -------------------------------------------------------------------------
    # Rule 7: PreferredPriceRange must be a valid segment
    # -------------------------------------------------------------------------
    invalid_pref_price = df[~df["PreferredPriceRange"].isin(VALID_PRICE_RANGES)]
    if len(invalid_pref_price) > 0:
        violations["Invalid PreferredPriceRange"] = len(invalid_pref_price)
        details["Invalid PreferredPriceRange"] = (
            invalid_pref_price["PreferredPriceRange"].unique().tolist()
        )

    # -------------------------------------------------------------------------
    # Rule 8: CustomerID format should be C followed by 5 digits (C00001)
    # -------------------------------------------------------------------------
    # Regular expression breakdown:
    #   ^      → start of string
    #   C      → literal letter C
    #   \d{5}  → exactly 5 digits (0-9)
    #   $      → end of string
    invalid_id_format = df[~df["CustomerID"].str.match(r"^C\d{5}$")]
    if len(invalid_id_format) > 0:
        violations["Invalid CustomerID format"] = len(invalid_id_format)
        details["Invalid CustomerID format"] = invalid_id_format["CustomerID"].tolist()[:5]

    # -------------------------------------------------------------------------
    # Rule 9: JoinDate should not be in the future
    # -------------------------------------------------------------------------
    # A customer can't have joined the store in a date that hasn't happened yet.
    if "JoinDate" in df.columns:
        try:
            parsed_dates = pd.to_datetime(df["JoinDate"], errors="coerce")
            # .dropna() removes NaT values (unparseable dates) to avoid comparison errors
            future_dates = parsed_dates.dropna()[parsed_dates.dropna() > pd.Timestamp.now()]
            if len(future_dates) > 0:
                violations["JoinDate in future"] = len(future_dates)
                details["JoinDate in future"] = (
                    df.loc[future_dates.index, "CustomerID"].tolist()[:5]
                )
        except Exception:
            pass  # Date parsing issues are already caught in validate_data_types

    # -------------------------------------------------------------------------
    # Summarize results
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
    Generate a detailed text-based validation report and save it to disk.

    The report format is deliberately simple (plain text) so it can be:
    - Read by anyone (no special software needed)
    - Versioned in Git (text diffs are easy to review)
    - Parsed by scripts (grep, awk for automated monitoring)
    - Attached to emails or tickets
    """
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    lines: List[str] = []

    # --- Header ---
    lines.append("=" * 70)
    lines.append("VALIDATION REPORT — CUSTOMERS DATASET")
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
    lines.append(f"  Unique Cities : {df['City'].nunique() if 'City' in df.columns else 'N/A'}")
    lines.append(f"  Age Range     : {df['Age'].min()} — {df['Age'].max()}" if 'Age' in df.columns else "")
    lines.append(f"  Points Range  : {df['LoyaltyPoints'].min()} — {df['LoyaltyPoints'].max()}" if 'LoyaltyPoints' in df.columns else "")
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
    lines.append(f"  Status               : {'✅ PASSED' if duplicate_result['passed'] else '❌ FAILED'}")
    lines.append(f"  Duplicate CustomerIDs : {duplicate_result['duplicate_customer_ids']}")
    lines.append(f"  Duplicate Names (info): {duplicate_result['duplicate_names_info']}")
    lines.append(f"  Fully Duplicated Rows : {duplicate_result['full_duplicates']}")
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
        for rule, detail in business_result["details"].items():
            lines.append(f"    {rule}: {detail}")
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

    # Write the report
    report_text = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    logger.info(f"📄 Validation report saved to: {report_path}")


# =============================================================================
# FUNCTION 8: run_validation() — The Orchestrator
# =============================================================================
def run_validation() -> bool:
    """
    Run the complete validation pipeline for the customers dataset.

    Returns True if ALL validations passed, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("STARTING VALIDATION: Customers Dataset")
    logger.info("=" * 60)

    # Step 1: Load the raw data
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

    # Step 3: Generate and save the detailed report
    generate_report(
        df=df,
        schema_result=schema_result,
        missing_result=missing_result,
        duplicate_result=duplicate_result,
        dtype_result=dtype_result,
        business_result=business_result,
        report_path=REPORT_FILE
    )

    # Step 4: Return overall pass/fail
    all_passed = all([
        schema_result["passed"],
        missing_result["passed"],
        duplicate_result["passed"],
        dtype_result["passed"],
        business_result["passed"]
    ])

    if all_passed:
        logger.info("🎉 Customers validation COMPLETED — ALL CHECKS PASSED")
    else:
        logger.warning("⚠️  Customers validation COMPLETED — SOME CHECKS FAILED")
        logger.warning("   Review the report for details: " + REPORT_FILE)

    return all_passed


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
