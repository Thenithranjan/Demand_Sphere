"""
==============================================================================
Inventory Orchestrator Script: run_inventory.py
==============================================================================
Why this file is needed:
    An orchestrator script integrates all components (data service, reorder calculations,
    stock monitoring, alert dispatching, decision optimization, reporting, and charting)
    into a single execution process. Running this script runs the entire analytical
    engine, outputs alerts, saves CSV summaries, generates charts, and exports the final
    inventory decision sheet to `inventory_decision.csv`.

Pipeline Flow:
    1. Loads current stock, demand predictions, and product metadata.
    2. Builds the consolidated integrated state dataframe.
    3. Calculates Economic Order Quantities (EOQ) and stock coverage.
    4. Applies safety margin risk monitoring and flags demand alerts.
    5. Dispatches alerts to `inventory_alerts.csv`.
    6. Run optimizer calculations (suggested buys, stockout timelines, risk levels).
    7. Saves sub-reports and compiles `inventory_summary.md`.
    8. Renders and saves 8 inventory visual control charts.
    9. Exports the decision list to `inventory_decision.csv` in the project root.
==============================================================================
"""

import os
import sys
import time
from pathlib import Path
import pandas as pd

# Ensure project root is in sys.path
INVENTORY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = INVENTORY_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure CWD is set to project root
os.chdir(PROJECT_ROOT)

from backend.inventory import logger
from backend.inventory.inventory_service import get_integrated_inventory_state
from backend.inventory.reorder_engine import compute_reorder_metrics
from backend.inventory.stock_monitor import monitor_stock_levels
from backend.inventory.alert_service import generate_inventory_alerts
from backend.inventory.inventory_optimizer import optimize_inventory_decisions
from backend.inventory.reports import generate_inventory_reports
from backend.inventory.visualize import generate_inventory_charts

def main() -> int:
    """
    Main orchestrator function for the Smart Inventory Optimization pipeline.
    Returns 0 on success, 1 on failure.
    """
    start_time = time.time()
    logger.info("=" * 70)
    logger.info("📦 RETAIL PRODUCT RECOMMENDATION — SMART INVENTORY OPTIMIZATION")
    logger.info("=" * 70)
    logger.info(f"Project root: {PROJECT_ROOT}")

    try:
        # Step 1: Load and integrate datasets (inventory_service.py)
        state_df = get_integrated_inventory_state()

        # Step 2: Compute reorder SCM metrics (reorder_engine.py)
        enriched_df = compute_reorder_metrics(state_df)

        # Step 3: Run stock level and safety limit monitoring (stock_monitor.py)
        monitored_df = monitor_stock_levels(enriched_df)

        # Step 4: Run decision optimization and risk rating (inventory_optimizer.py)
        optimized_df = optimize_inventory_decisions(monitored_df)

        # Step 5: Export inventory decision sheet CSV to project root
        decision_df = optimized_df[[
            "ProductID", "ProductName", "Category", "CurrentStock",
            "ForecastDemand", "SafetyStock", "ReorderPoint", "ReorderQuantity",
            "InventoryStatus", "RiskLevel", "Recommendation"
        ]]
        decision_output_path = PROJECT_ROOT / "inventory_decision.csv"
        decision_df.to_csv(decision_output_path, index=False)
        logger.info(f"Exported Inventory Decision CSV -> {decision_output_path}")

        # Step 6: Generate alerts log (alert_service.py)
        alerts_output_path = PROJECT_ROOT / "inventory_alerts.csv"
        generate_inventory_alerts(optimized_df, alerts_output_path)

        # Step 7: Generate operational sub-reports and inventory_summary.md (reports.py)
        generate_inventory_reports(optimized_df)

        # Step 8: Renders and saves 8 inventory diagnostic charts (visualize.py)
        generate_inventory_charts(optimized_df)

        duration = time.time() - start_time
        logger.info("=" * 70)
        logger.info(f"🎉 INVENTORY OPTIMIZATION RUN COMPLETED SUCCESSFULLY in {duration:.2f} seconds!")
        logger.info(f"Decision sheet saved to: {decision_output_path}")
        logger.info(f"Alerts log saved to    : {alerts_output_path}")
        logger.info(f"Reports & charts under : reports/inventory/")
        logger.info("=" * 70)
        return 0

    except Exception as e:
        logger.error(f"Critical error during inventory optimization execution: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
