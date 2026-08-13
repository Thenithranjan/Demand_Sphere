"""
==============================================================================
Demand Forecasting Orchestrator Script: run_forecasting.py
==============================================================================
Why this file exists:
    An orchestrator script aggregates all submodules (prepare, train, predict,
    evaluate, visualize) into a single, unified execution thread. This allows
    developers to trigger the entire ML pipeline (from raw data ingestion to
    finished prediction outputs and visual charts) with a single command:
    python backend/forecasting/run_forecasting.py

Pipeline Flow:
    1. Loads processed transactional and catalog datasets.
    2. Builds calendar grid features and shifts labels (Target t+1).
    3. Trains and tunes XGBoost regressor models with walk-forward CV.
    4. Evaluates model generalisation error on the test slice.
    5. Predicts next-month (Jan 2026) and Q1 demand for all products.
    6. Combines predictions with warehouse metrics to compile recommendations.
    7. Renders and saves forecasting visual diagnostic plots.
    8. Exports results to forecast_results.csv.
==============================================================================
"""

import os
import sys
import time
from pathlib import Path
import pandas as pd

# Ensure project root is in sys.path
FORECASTING_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FORECASTING_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Also ensure CWD is set to project root
os.chdir(PROJECT_ROOT)

from backend.forecasting import DATA_DIR, logger
from backend.forecasting.prepare_data import prepare_forecasting_data, split_forecasting_data
from backend.forecasting.train_model import train_demand_forecast_models
from backend.forecasting.evaluate import evaluate_models
from backend.forecasting.predict import generate_forecast_results
from backend.forecasting.visualize import generate_visualizations

def main() -> int:
    """
    Main orchestrator function for the Demand Forecasting pipeline.
    Returns 0 on success, 1 on failure.
    """
    start_time = time.time()
    logger.info("=" * 70)
    logger.info("🚀 RETAIL PRODUCT RECOMMENDATION — DEMAND FORECASTING PIPELINE")
    logger.info("=" * 70)
    logger.info(f"Project root: {PROJECT_ROOT}")

    try:
        # Step 1: Load individual cleaned datasets
        sales_path = DATA_DIR / "sales_clean.csv"
        products_path = DATA_DIR / "products_clean.csv"
        inventory_path = DATA_DIR / "inventory_clean.csv"

        for p in [sales_path, products_path, inventory_path]:
            if not p.exists():
                raise FileNotFoundError(f"Required clean dataset missing: {p}")

        logger.info("Loading cleaned datasets...")
        sales_df = pd.read_csv(sales_path)
        products_df = pd.read_csv(products_path)
        inventory_df = pd.read_csv(inventory_path)

        # Step 2: Prepare features and targets (prepare_data.py)
        grid_df, _ = prepare_forecasting_data()
        
        # Step 3: Chronological Train/Test/Inference Split (prepare_data.py)
        train_df, test_df, inference_df = split_forecasting_data(grid_df)

        # Step 4: Model Training and Tuning (train_model.py)
        qty_model, rev_model, training_metadata = train_demand_forecast_models()

        # Step 5: Model Evaluation on test set (evaluate.py)
        evaluation_metrics = evaluate_models(qty_model, rev_model, test_df)

        # Step 6: Generate Forecast Predictions (predict.py)
        product_forecast, aggregations = generate_forecast_results(
            qty_model=qty_model,
            rev_model=rev_model,
            inference_df=inference_df,
            products_df=products_df,
            inventory_df=inventory_df,
            sales_df=sales_df
        )

        # Step 7: Export forecast results CSV to project root
        results_output_path = PROJECT_ROOT / "forecast_results.csv"
        product_forecast.to_csv(results_output_path, index=False)
        logger.info(f"Saved forecasting output CSV -> {results_output_path}")

        # Step 8: Generate diagnostic visualizations (visualize.py)
        generate_visualizations(
            test_df=test_df,
            qty_model=qty_model,
            rev_model=rev_model,
            forecast_df=product_forecast,
            sales_df=sales_df,
            cat_forecast_df=aggregations["category"],
            brand_forecast_df=aggregations["brand"]
        )

        duration = time.time() - start_time
        logger.info("=" * 70)
        logger.info(f"🎉 FORECASTING RUN COMPLETED SUCCESSFULLY in {duration:.2f} seconds!")
        logger.info(f"Trained Models saved under: backend/models/")
        logger.info(f"Forecasting CSV saved to: {results_output_path}")
        logger.info(f"Visual charts saved under: reports/forecast/")
        logger.info("=" * 70)
        return 0

    except Exception as e:
        logger.error(f"Critical error during forecasting execution: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
