"""
==============================================================================
Master Script: run_pipeline.py
==============================================================================
Purpose:
    Orchestrates the complete data preprocessing pipeline for the
    Retail Product Recommendation system.

    Running this single script will:
    1. Validate all 4 raw datasets (products, customers, sales, inventory)
    2. Clean all 4 datasets (strip, normalise, fix, derive)
    3. Save processed CSV files to data/processed/
    4. Print progress messages at each stage
    5. Stop ONLY if a critical error occurs (file not found, unrecoverable)

Usage:
    py backend/data_pipeline/run_pipeline.py

    Must be run from the project root directory
    (Retail-Product-Recommendation/).

Output:
    data/processed/products_clean.csv
    data/processed/customers_clean.csv
    data/processed/sales_clean.csv
    data/processed/inventory_clean.csv
    reports/validation_report_products.txt
    reports/validation_report_customers.txt
    reports/validation_report_sales.txt
    reports/validation_report_inventory.txt
==============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so that "backend.data_pipeline.*"
# imports resolve correctly regardless of how the script is invoked.
# ---------------------------------------------------------------------------
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Also ensure CWD is the project root so relative file paths (data/raw/…)
# used by the validation and cleaning modules resolve correctly.
os.chdir(PROJECT_ROOT)

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("run_pipeline")


# =============================================================================
# PIPELINE ORCHESTRATOR
# =============================================================================
def main() -> int:
    """
    Run the complete preprocessing pipeline.

    Returns 0 on success, 1 on critical failure.
    """
    pipeline_start = time.time()

    logger.info("=" * 70)
    logger.info("🚀 RETAIL PRODUCT RECOMMENDATION — DATA PIPELINE")
    logger.info("=" * 70)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info("")

    # Track results for final summary
    validation_results = {}
    cleaning_results = {}
    output_files = {
        "products_clean.csv": os.path.join("data", "processed", "products_clean.csv"),
        "customers_clean.csv": os.path.join("data", "processed", "customers_clean.csv"),
        "sales_clean.csv": os.path.join("data", "processed", "sales_clean.csv"),
        "inventory_clean.csv": os.path.join("data", "processed", "inventory_clean.csv"),
    }

    # =========================================================================
    # PHASE 1: VALIDATION
    # =========================================================================
    logger.info("─" * 70)
    logger.info("📋 PHASE 1: DATA VALIDATION")
    logger.info("─" * 70)

    # --- Validate Products ---
    try:
        from backend.data_pipeline.validate_products import run_validation as validate_products
        result = validate_products()
        validation_results["Products"] = result
        logger.info(f"  {'✓' if result else '✗'} Products validation {'PASSED' if result else 'FAILED (non-critical)'}")
    except Exception as e:
        logger.error(f"  ✗ Products validation ERROR: {e}")
        validation_results["Products"] = False

    # --- Validate Customers ---
    try:
        from backend.data_pipeline.validate_customers import run_validation as validate_customers
        result = validate_customers()
        validation_results["Customers"] = result
        logger.info(f"  {'✓' if result else '✗'} Customers validation {'PASSED' if result else 'FAILED (non-critical)'}")
    except Exception as e:
        logger.error(f"  ✗ Customers validation ERROR: {e}")
        validation_results["Customers"] = False

    # --- Validate Sales ---
    try:
        from backend.data_pipeline.validate_sales import run_validation as validate_sales
        result = validate_sales()
        validation_results["Sales"] = result
        logger.info(f"  {'✓' if result else '✗'} Sales validation {'PASSED' if result else 'FAILED (non-critical)'}")
    except Exception as e:
        logger.error(f"  ✗ Sales validation ERROR: {e}")
        validation_results["Sales"] = False

    # --- Validate Inventory ---
    try:
        from backend.data_pipeline.validate_inventory import run_validation as validate_inventory
        result = validate_inventory()
        validation_results["Inventory"] = result
        logger.info(f"  {'✓' if result else '✗'} Inventory validation {'PASSED' if result else 'FAILED (non-critical)'}")
    except Exception as e:
        logger.error(f"  ✗ Inventory validation ERROR: {e}")
        validation_results["Inventory"] = False

    logger.info("")

    # =========================================================================
    # PHASE 2: CLEANING
    # =========================================================================
    logger.info("─" * 70)
    logger.info("🧹 PHASE 2: DATA CLEANING")
    logger.info("─" * 70)

    # --- Clean Products ---
    try:
        from backend.data_pipeline.clean_products import run_cleaning as clean_products
        result = clean_products()
        cleaning_results["Products"] = result
        logger.info(f"  {'✓' if result else '✗'} Products cleaning {'COMPLETED' if result else 'FAILED'}")
        if not result:
            logger.error("  ⛔ CRITICAL: Products cleaning failed — pipeline stopping")
            return 1
    except Exception as e:
        logger.error(f"  ✗ Products cleaning ERROR: {e}")
        cleaning_results["Products"] = False
        logger.error("  ⛔ CRITICAL: Products cleaning exception — pipeline stopping")
        return 1

    # --- Clean Customers ---
    try:
        from backend.data_pipeline.clean_customers import run_cleaning as clean_customers
        result = clean_customers()
        cleaning_results["Customers"] = result
        logger.info(f"  {'✓' if result else '✗'} Customers cleaning {'COMPLETED' if result else 'FAILED'}")
        if not result:
            logger.error("  ⛔ CRITICAL: Customers cleaning failed — pipeline stopping")
            return 1
    except Exception as e:
        logger.error(f"  ✗ Customers cleaning ERROR: {e}")
        cleaning_results["Customers"] = False
        logger.error("  ⛔ CRITICAL: Customers cleaning exception — pipeline stopping")
        return 1

    # --- Clean Sales ---
    try:
        from backend.data_pipeline.clean_sales import run_cleaning as clean_sales
        result = clean_sales()
        cleaning_results["Sales"] = result
        logger.info(f"  {'✓' if result else '✗'} Sales cleaning {'COMPLETED' if result else 'FAILED'}")
        if not result:
            logger.error("  ⛔ CRITICAL: Sales cleaning failed — pipeline stopping")
            return 1
    except Exception as e:
        logger.error(f"  ✗ Sales cleaning ERROR: {e}")
        cleaning_results["Sales"] = False
        logger.error("  ⛔ CRITICAL: Sales cleaning exception — pipeline stopping")
        return 1

    # --- Clean Inventory ---
    try:
        from backend.data_pipeline.clean_inventory import run_cleaning as clean_inventory
        result = clean_inventory()
        cleaning_results["Inventory"] = result
        logger.info(f"  {'✓' if result else '✗'} Inventory cleaning {'COMPLETED' if result else 'FAILED'}")
        if not result:
            logger.error("  ⛔ CRITICAL: Inventory cleaning failed — pipeline stopping")
            return 1
    except Exception as e:
        logger.error(f"  ✗ Inventory cleaning ERROR: {e}")
        cleaning_results["Inventory"] = False
        logger.error("  ⛔ CRITICAL: Inventory cleaning exception — pipeline stopping")
        return 1

    logger.info("")

    # =========================================================================
    # PHASE 3: OUTPUT VERIFICATION
    # =========================================================================
    logger.info("─" * 70)
    logger.info("🔍 PHASE 3: OUTPUT VERIFICATION")
    logger.info("─" * 70)

    all_files_exist = True
    for name, path in output_files.items():
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            logger.info(f"  ✓ {name} exists ({size_kb:.1f} KB)")
        else:
            logger.error(f"  ✗ {name} MISSING at {path}")
            all_files_exist = False

    logger.info("")

    # =========================================================================
    # PHASE 4: FINAL SUMMARY
    # =========================================================================
    pipeline_duration = time.time() - pipeline_start

    logger.info("=" * 70)
    logger.info("📊 PIPELINE SUMMARY")
    logger.info("=" * 70)

    # Validation summary
    logger.info("")
    logger.info("  VALIDATION RESULTS:")
    for dataset, passed in validation_results.items():
        logger.info(f"    {'✓' if passed else '✗'} {dataset} validated")

    # Cleaning summary
    logger.info("")
    logger.info("  CLEANING RESULTS:")
    for dataset, passed in cleaning_results.items():
        logger.info(f"    {'✓' if passed else '✗'} {dataset} cleaned")

    # File output summary
    logger.info("")
    logger.info("  OUTPUT FILES:")
    for name, path in output_files.items():
        exists = os.path.exists(path)
        logger.info(f"    {'✓' if exists else '✗'} {path}")

    # Overall result
    logger.info("")
    logger.info(f"  Duration: {pipeline_duration:.1f} seconds")

    all_valid = all(validation_results.values())
    all_clean = all(cleaning_results.values())

    if all_valid and all_clean and all_files_exist:
        logger.info("")
        logger.info("  ✓ Products validated")
        logger.info("  ✓ Customers validated")
        logger.info("  ✓ Sales validated")
        logger.info("  ✓ Inventory validated")
        logger.info("  ✓ Cleaning completed")
        logger.info("  ✓ CSV files generated")
        logger.info("")
        logger.info("=" * 70)
        logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY — ALL CHECKS PASSED")
        logger.info("=" * 70)
        return 0
    else:
        logger.info("")
        logger.info("=" * 70)
        logger.info("⚠️  PIPELINE COMPLETED WITH WARNINGS — Review logs above")
        logger.info("=" * 70)
        return 0 if all_clean and all_files_exist else 1


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
